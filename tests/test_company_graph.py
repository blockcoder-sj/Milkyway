"""Canonical identity and public company navigation, entirely offline."""
import datetime as dt
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sqlite3
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch, Mock

from fastapi import HTTPException
from cloud_app.company_graph import CompanyGraph, _enable_wal
from cloud_app.company_schemas import CompanyKnowledge, Source
from cloud_app import (
    company_entities as pages,
    company_worker as worker,
    company_feed as feed,
)
from cloud_app.company_service import root
from cloud_app.market_service import _write_cache
from cloud_app.local_ops import create_backup, restore_backup

NOW = dt.datetime(2026, 10, 1, tzinfo=dt.timezone.utc)
SRC = Source(
    label="Public report", url="https://www.sec.gov/report", as_of="2025-12-31"
)


def company(symbol="AAPL", qid="Q312", name="Apple", **extra):
    return CompanyKnowledge(
        symbol=symbol, entity_id=qid, name=name, fetched_at=NOW, **extra
    )


def edge(
    name="Private subsidiary", qid="Q123", symbol=None, kind="subsidiary", **extra
):
    return dict(name=name, entity_id=qid, symbol=symbol, kind=kind, source=SRC, **extra)


class CompanyGraphTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.settings = SimpleNamespace(
            personal_local_mode=True,
            production=False,
            dataset_dir=Path(self.temp.name) / "runtime/personal-data",
        )
        self.graph = CompanyGraph(self.settings)

    def tearDown(self):
        self.temp.cleanup()

    def test_wal_initialization_retries_only_sqlite_busy_and_never_rewrites_active_mode(self):
        busy = sqlite3.OperationalError('busy')
        busy.sqlite_errorcode = sqlite3.SQLITE_BUSY
        db = Mock()
        db.execute.side_effect = [busy, Mock(fetchone=lambda: ('wal',))]
        with patch('cloud_app.company_graph.time.sleep') as pause:
            _enable_wal(db)
        self.assertEqual(db.execute.call_count, 2)
        self.assertTrue(all(call.args == ('PRAGMA journal_mode',) for call in db.execute.call_args_list))
        pause.assert_called_once()
        db.execute.side_effect = sqlite3.OperationalError('disk failure')
        with self.assertRaisesRegex(sqlite3.OperationalError, 'disk failure'):
            _enable_wal(db)
        db.execute.side_effect = busy
        with patch('cloud_app.company_graph.time.monotonic', side_effect=[0, 6]), self.assertRaises(sqlite3.OperationalError):
            _enable_wal(db)

    @unittest.skipUnless(os.name == 'posix', 'POSIX advisory lock regression')
    def test_second_connection_does_not_release_first_connections_file_locks(self):
        # A different process probes SQLite's shared-byte region on the main DB.
        # Raw os.open/close of an existing file releases ALL this process's locks.
        probe = """
import errno, fcntl, os, sys
fd=os.open(sys.argv[1],os.O_RDWR)
try:
    fcntl.lockf(fd,fcntl.LOCK_EX|fcntl.LOCK_NB,510,0x40000002,os.SEEK_SET)
except OSError as exc:
    sys.exit(0 if exc.errno in (errno.EACCES, errno.EAGAIN) else 8)
sys.exit(9)
"""
        with self.graph.connection() as first:
            first.execute('BEGIN IMMEDIATE')
            with self.graph.connection() as second:
                second.execute('SELECT COUNT(*) FROM company_entities').fetchone()
                result=subprocess.run([sys.executable,'-c',probe,str(self.graph.path)],capture_output=True,timeout=10)
                self.assertEqual(result.returncode,0,result.stderr.decode())
            self.assertEqual(first.execute('PRAGMA quick_check').fetchone()[0],'ok')

    def test_directed_relations_have_canonical_targets_and_original_evidence(self):
        key = self.graph.ingest(
            company(relations=[edge(), edge("Supplier", "Q456", kind="supplier")])
        )
        relations = self.graph.relations(key)
        subsidiary = next(row for row in relations if row["kind"] == "subsidiary")
        self.assertTrue(subsidiary["target_id"].startswith("c_"))
        self.assertEqual(subsidiary["source"], SRC.model_dump())
        reverse = self.graph.relations(subsidiary["target_id"])[0]
        self.assertEqual(reverse["kind"], "parent")
        self.assertTrue(reverse["reverse"])
        self.assertEqual(reverse["target_id"], key)
        self.assertEqual(reverse["reported_by"], "Apple")
        self.assertEqual(reverse["source"], SRC.model_dump())

    def test_alias_upgrade_keeps_prior_links_and_redirects(self):
        apple = self.graph.ingest(company(qid=None))
        parent = self.graph.ingest(
            company("MSFT", "Q2283", "Microsoft", relations=[edge("Apple", "Q312")])
        )
        old_stub = self.graph.relations(parent)[0]["target_id"]
        self.assertNotEqual(apple, old_stub)
        self.assertEqual(self.graph.ingest(company()), apple)
        self.assertEqual(self.graph.entity(old_stub)["id"], apple)
        self.assertEqual(self.graph.relations(parent)[0]["target_id"], apple)
        self.assertEqual(self.graph.relations(apple)[0]["target_id"], parent)

    def test_same_relationship_groups_all_evidence_and_preserves_retractions(self):
        apple = self.graph.ingest(company(relations=[edge(detail="Apple statement")]))
        target = self.graph.relations(apple)[0]["target_id"]
        other_source = Source(
            label="Subsidiary report", url="https://www.sec.gov/other"
        )
        private = company(
            None,
            "Q123",
            "Private subsidiary",
            relations=[
                dict(
                    name="Apple",
                    entity_id="Q312",
                    symbol="AAPL",
                    kind="parent",
                    detail="Subsidiary statement",
                    source=other_source,
                ),
            ],
        )
        self.assertEqual(self.graph.ingest(private), target)
        relations = self.graph.relations(target)
        self.assertEqual(len(relations), 1)
        self.assertEqual(relations[0]["kind"], "parent")
        evidence = relations[0]["evidence"]
        self.assertEqual(
            {item["detail"] for item in evidence},
            {"Apple statement", "Subsidiary statement"},
        )
        self.assertEqual({item["reverse"] for item in evidence}, {True, False})
        self.assertEqual(
            {item["source"]["url"] for item in evidence}, {SRC.url, other_source.url}
        )
        self.graph.ingest(company())
        remaining = self.graph.relations(target)[0]["evidence"]
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0]["detail"], "Subsidiary statement")

    def test_same_name_does_not_merge_distinct_identified_entities(self):
        key = self.graph.ingest(
            company(relations=[edge("Same", "Q123"), edge("Same", "Q456")])
        )
        self.assertEqual(len({r["target_id"] for r in self.graph.relations(key)}), 2)

    def test_current_reviewed_wording_wins_same_document_and_keeps_old_evidence(self):
        from copy import deepcopy
        from cloud_app.company_research_catalog import RELATIONS
        reviewed = deepcopy(next(e for e in RELATIONS['NUAI'] if e.get('registry_id') == 'luminant-et'))
        old = deepcopy(reviewed)
        old['detail'] = 'Earlier cached wording'
        owner = self.graph.ingest(company('NUAI', None, 'New Era', relations=[old, reviewed]))
        with self.graph.connection() as db:
            db.execute("UPDATE company_relations SET observed_at='2099-01-01' WHERE detail=?", (old['detail'],))
        relation, = self.graph.relations(owner)
        self.assertEqual(relation['detail'], reviewed['detail'])
        reverse, = self.graph.relations(relation['target_id'])
        self.assertEqual(reverse['detail'], reviewed['detail'])
        self.assertEqual({e['detail'] for e in reverse['evidence']}, {old['detail'], reviewed['detail']})

    def test_newer_dated_document_wins_over_older_reviewed_or_recently_fetched_claim(self):
        from copy import deepcopy
        from cloud_app.company_research_catalog import RELATIONS
        old = deepcopy(next(e for e in RELATIONS['NUAI'] if e.get('registry_id') == 'luminant-et'))
        newer = deepcopy(old)
        newer['detail'] = 'Newer document statement'
        newer['source'] = dict(label='Later primary statement', url='https://www.sec.gov/later',
                               as_of='2026-10-03', level='primary')
        collected = deepcopy(old)
        collected['detail'] = 'Collection date is not the document date'
        collected['source'] = dict(label='Undated page', url='https://www.sec.gov/undated',
                                   as_of='열람 2026-10-04', level='primary')
        owner = self.graph.ingest(company('NUAI', None, 'New Era', relations=[old, newer, collected]))
        with self.graph.connection() as db:
            db.execute("UPDATE company_relations SET observed_at='2099-01-01' WHERE detail!=?", (newer['detail'],))
        relation, = self.graph.relations(owner)
        self.assertEqual(relation['detail'], newer['detail'])
        self.assertEqual(len(relation['evidence']), 3)
        self.assertEqual(self.graph.relations(relation['target_id'])[0]['detail'], newer['detail'])

    def test_newer_provider_claim_does_not_displace_primary_evidence(self):
        from copy import deepcopy
        from cloud_app.company_research_catalog import RELATIONS
        primary = deepcopy(next(e for e in RELATIONS['NUAI'] if e.get('registry_id') == 'luminant-et'))
        secondary = deepcopy(primary)
        secondary['detail'] = 'Later secondary claim'
        secondary['source'] = dict(label='Provider account', url='https://example.org/later',
                                   as_of='2026-10-04', level='provider')
        owner = self.graph.ingest(company('NUAI', None, 'New Era', relations=[primary, secondary]))
        relation, = self.graph.relations(owner)
        self.assertEqual(relation['detail'], primary['detail'])
        self.assertEqual(len(relation['evidence']), 2)
        self.assertEqual(self.graph.relations(relation['target_id'])[0]['detail'], primary['detail'])

    def test_name_only_reference_is_navigable_but_not_collected_by_guessing(self):
        key = self.graph.ingest(company(relations=[edge(qid=None)]))
        target = self.graph.relations(key)[0]["target_id"]
        page = pages.entity_snapshot(self.settings, target, NOW)
        self.assertFalse(page["collectable"])
        self.assertIsNone(page["quote"]["market_cap"])
        self.assertTrue(page["sources"])
        self.assertEqual(page["relations"][0]["target_id"], key)
        with self.assertRaises(HTTPException) as error:
            pages.enqueue_entity(self.settings, target)
        self.assertEqual(error.exception.status_code, 409)

    def test_replacing_one_owner_does_not_erase_another_owners_claim(self):
        apple = self.graph.ingest(company(relations=[edge()]))
        target = self.graph.relations(apple)[0]["target_id"]
        microsoft = self.graph.ingest(
            company("MSFT", "Q2283", "Microsoft", relations=[edge(kind="partner")])
        )
        self.graph.ingest(company())
        self.assertEqual(self.graph.relations(apple), [])
        self.assertEqual(self.graph.relations(target)[0]["target_id"], microsoft)
        self.assertTrue(self.graph.entity(target)["sources"])

    def test_conflicting_qid_rejects_entire_transaction(self):
        key = self.graph.ingest(company(relations=[edge()]))
        with self.assertRaisesRegex(ValueError, "Conflicting"):
            self.graph.ingest(company(qid="Q999", relations=[]))
        self.assertEqual(self.graph.entity(key)["entity_id"], "Q312")
        self.assertEqual(len(self.graph.relations(key)), 1)

    def test_concurrent_first_import_is_idempotent_and_foreign_keys_valid(self):
        with ThreadPoolExecutor(max_workers=6) as pool:
            keys = list(
                pool.map(
                    lambda _: self.graph.ingest(company(relations=[edge()])), range(12)
                )
            )
        self.assertEqual(len(set(keys)), 1)
        with self.graph.connection() as db:
            self.assertEqual(
                db.execute("SELECT COUNT(*) FROM company_relations").fetchone()[0], 1
            )
            self.assertEqual(
                db.execute("SELECT COUNT(*) FROM company_entities").fetchone()[0], 2
            )
            self.assertIsNone(db.execute("PRAGMA foreign_key_check").fetchone())

    def test_legacy_import_enriches_public_research_and_rejects_wrong_identity(self):
        path = root(self.settings) / "AAPL.json"
        value = company(relations=[edge()]).model_dump(mode="json")
        _write_cache(path, value)
        _write_cache(path.with_name("WRONG.json"), value)
        before = path.read_bytes()
        self.assertEqual(pages.bootstrap(self.settings), {"imported": 1, "rejected": 1})
        self.assertNotEqual(path.read_bytes(), before)
        self.assertEqual(pages.identified(__import__('json').loads(path.read_text())).entity_id, 'Q312')
        after = path.read_bytes()
        self.assertEqual(pages.bootstrap(self.settings)["imported"], 0)
        self.assertEqual(path.read_bytes(), after)

    def test_identical_unreviewed_cache_skips_validation_but_content_and_sector_changes_do_not(self):
        root(self.settings)
        value=company('ZZZTEST',qid=None,name='Synthetic public company',collector_version=4)
        self.graph.ingest(value)
        path=root(self.settings)/'ZZZTEST.json'
        _write_cache(path,value.model_dump(mode='json'))
        with patch.object(pages,'enrich',wraps=pages.enrich) as enrich:
            self.assertEqual(pages.bootstrap(self.settings)['imported'],0)
            enrich.assert_not_called()
        value.description='Changed content, same timestamp'
        value.description_source=SRC
        _write_cache(path,value.model_dump(mode='json'))
        with patch.object(pages,'enrich',wraps=pages.enrich) as enrich:
            self.assertEqual(pages.bootstrap(self.settings)['imported'],1)
            enrich.assert_called_once()
        with patch('cloud_app.company_service.related_directory',return_value={'ZZZTEST':{'sector':'us_45'}}):
            self.assertEqual(pages.bootstrap(self.settings)['imported'],1)
        self.assertEqual(self.graph.by_symbol('ZZZTEST')['sector'],'us_45')

    def test_clean_v4_graph_does_not_reparse_all_reports_at_startup(self):
        self.graph.ingest(company(collector_version=4))
        with patch.object(CompanyKnowledge,'model_validate_json',wraps=CompanyKnowledge.model_validate_json) as validate:
            self.graph.remove_encyclopedia()
            validate.assert_not_called()
        with self.graph.connection() as db:
            self.assertEqual(
                db.execute("SELECT COUNT(*) FROM company_profiles").fetchone()[0], 1
            )

    def test_invalid_entity_and_cloud_mode_are_rejected(self):
        for value in ("../env", "Q123", "c_" + "0" * 32):
            with self.assertRaises(HTTPException):
                pages.entity_snapshot(self.settings, value)
        self.settings.personal_local_mode = False
        with self.assertRaises(ValueError):
            CompanyGraph(self.settings)

    def test_database_symlink_is_rejected(self):
        target = Path(self.temp.name) / "untouched"
        target.write_text("untouched")
        self.graph.path.symlink_to(target)
        with self.assertRaises(ValueError):
            self.graph.ingest(company())
        self.assertEqual(target.read_text(), "untouched")

    def test_symlink_inserted_during_exclusive_creation_is_rejected(self):
        target = Path(self.temp.name) / 'untouched-raced'
        target.write_text('untouched')
        target.chmod(0o640)
        original_open = os.open
        def raced_open(path, flags, mode=0o777, **kwargs):
            if Path(path) == self.graph.path:
                self.graph.path.symlink_to(target)
                raise FileExistsError('raced creation')
            return original_open(path, flags, mode, **kwargs)
        with patch('cloud_app.company_graph.os.open', side_effect=raced_open):
            with self.assertRaisesRegex(ValueError, 'Unsafe company graph file'):
                with self.graph.connection():
                    self.fail('Must reject the raced symlink')
        self.assertEqual(target.read_text(), 'untouched')
        self.assertEqual(target.stat().st_mode & 0o777, 0o640)

    def test_legacy_private_qid_is_navigation_only_and_cannot_queue_wiki(self):
        key = self.graph.ingest(company(relations=[edge()]))
        private = self.graph.relations(key)[0]["target_id"]
        with self.assertRaises(HTTPException) as error:
            pages.enqueue_entity(self.settings, private)
        self.assertEqual(error.exception.status_code, 409)
        self.assertFalse(pages.entity_snapshot(self.settings, private, NOW)['collectable'])
        self.assertEqual(self.graph.relations(private)[0]["target_id"], key)

    def test_connected_public_ticker_discovers_real_directory_context(self):
        from cloud_app.market_details import cache_path

        key = self.graph.ingest(
            company(relations=[edge("Listed company", "Q456", "AAA", "supplier")])
        )
        target = self.graph.relations(key)[0]["target_id"]
        _write_cache(
            cache_path(self.settings, "us_45"),
            {
                "companies": {
                    "rows": [
                        dict(
                            name="Listed company",
                            symbol="AAA",
                            currency="USD",
                            market_cap=123,
                            displayed_share_pct=100,
                            source="Yahoo Finance",
                            url="https://finance.yahoo.com/quote/AAA/",
                        )
                    ]
                }
            },
        )
        page = pages.entity_snapshot(self.settings, target, NOW)
        self.assertEqual(page["entity_key"], target)
        self.assertEqual(page["sector"], "us_45")
        self.assertEqual(page["quote"]["market_cap"], 123)
        self.assertEqual(page["entity_id"], "Q456")

    def test_legacy_qid_only_queued_request_is_rejected_without_provider(self):
        private = self.graph.ingest(
            company(None, "Q123", "Private", description="original")
        )
        request = root(self.settings) / "requests" / (private + ".json")
        _write_cache(request, {'entity_key':private,'symbol':None,'entity_id':'Q123'})
        with patch.object(
            worker._provider,
            "run",
            return_value=company(None, "Q999", "Wrong").model_dump(mode="json"),
        ) as provider:
            with self.assertRaises(ValueError): worker.process_request(self.settings, request)
            provider.assert_not_called()
        value = pages.entity_snapshot(self.settings, private, NOW)
        self.assertEqual(value["description"], "original")
        self.assertEqual(value["entity_id"], "Q123")
        self.assertFalse(value["errors"])

    def test_legacy_private_identity_never_requests_an_encyclopedia(self):
        with patch.object(feed, 'get') as network:
            result=feed.collect_company({'name':'Private','symbol':None,'entity_id':'Q123'}, {})
        self.assertEqual(result['entity_id'],'Q123')
        self.assertEqual(result['sources'],[])
        network.assert_not_called()

    def test_online_backup_restores_committed_graph_and_excludes_wal(self):
        key = self.graph.ingest(company(relations=[edge()]))
        runtime = self.settings.dataset_dir.parent
        with sqlite3.connect(runtime / "club.sqlite3") as db:
            db.execute("CREATE TABLE ledger(id INTEGER)")
        with self.graph.connection() as live:
            # Keep a WAL connection open while taking the snapshot.
            archive = create_backup(runtime, Path(self.temp.name) / "backups")
        restored = Path(self.temp.name) / "restored"
        restore_backup(archive, restored, Path(self.temp.name) / "restore-backups")
        settings = SimpleNamespace(
            personal_local_mode=True,
            production=False,
            dataset_dir=restored / "personal-data",
        )
        graph = CompanyGraph(settings)
        self.assertEqual(graph.relations(key)[0]["source"], SRC.model_dump())
        self.assertEqual(graph.entity(key)["entity_id"], "Q312")
        import zipfile

        with zipfile.ZipFile(archive) as file:
            self.assertIn("company-details/graph.sqlite3", file.namelist())
            self.assertNotIn("company-details/graph.sqlite3-wal", file.namelist())


if __name__ == "__main__":
    unittest.main()
