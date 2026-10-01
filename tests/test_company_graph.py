"""Canonical identity and public company navigation, entirely offline."""
import datetime as dt
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sqlite3
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from cloud_app.company_graph import CompanyGraph
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

    def test_same_name_does_not_merge_distinct_identified_entities(self):
        key = self.graph.ingest(
            company(relations=[edge("Same", "Q123"), edge("Same", "Q456")])
        )
        self.assertEqual(len({r["target_id"] for r in self.graph.relations(key)}), 2)

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

    def test_legacy_import_preserves_files_and_rejects_wrong_identity(self):
        path = root(self.settings) / "AAPL.json"
        value = company(relations=[edge()]).model_dump(mode="json")
        _write_cache(path, value)
        _write_cache(path.with_name("WRONG.json"), value)
        before = path.read_bytes()
        self.assertEqual(pages.bootstrap(self.settings), {"imported": 1, "rejected": 1})
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(pages.bootstrap(self.settings)["imported"], 0)
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

    def test_private_company_queue_worker_requires_registered_exact_qid(self):
        key = self.graph.ingest(company(relations=[edge()]))
        private = self.graph.relations(key)[0]["target_id"]
        pages.enqueue_entity(self.settings, private)
        self.assertEqual(
            pages.enqueue_entity(self.settings, private)["status"], "queued"
        )
        request = root(self.settings) / "requests" / (private + ".json")
        response = company(
            None,
            "Q123",
            "Private subsidiary",
            products=[dict(title="Product", source=SRC)],
        ).model_dump(mode="json")
        with patch.object(worker._provider, "run", return_value=response) as provider:
            worker.process_request(self.settings, request)
        payload = provider.call_args.args[0]
        self.assertIsNone(payload["symbol"])
        self.assertEqual(payload["entity_id"], "Q123")
        self.assertEqual(
            pages.entity_snapshot(self.settings, private, NOW)["products"][0]["title"],
            "Product",
        )
        self.assertEqual(
            pages.enqueue_entity(self.settings, private)["status"], "recent"
        )
        self.assertEqual(self.graph.relations(private)[0]["target_id"], key)

    def test_private_wrong_provider_identity_keeps_old_data(self):
        private = self.graph.ingest(
            company(None, "Q123", "Private", description="original")
        )
        pages.enqueue_entity(self.settings, private)
        request = root(self.settings) / "requests" / (private + ".json")
        with patch.object(
            worker._provider,
            "run",
            return_value=company(None, "Q999", "Wrong").model_dump(mode="json"),
        ):
            worker.process_request(self.settings, request)
        value = pages.entity_snapshot(self.settings, private, NOW)
        self.assertEqual(value["description"], "original")
        self.assertEqual(value["entity_id"], "Q123")
        self.assertTrue(value["errors"])

    def test_qid_fetch_never_uses_name_search_or_ticker_for_private_entities(self):
        response = {"entities": {"Q123": {"id": "Q123", "claims": {}, "labels": {}}}}
        with patch.object(feed, "get", return_value=response) as network:
            result, _ = feed.wikidata("Private", None, "Q123")
        self.assertEqual(result["entity_id"], "Q123")
        self.assertEqual(network.call_args.args[1]["action"], "wbgetentities")
        self.assertEqual(network.call_count, 1)
        with patch.object(
            feed,
            "get",
            return_value={"entities": {"Q123": {"id": "Q123", "missing": ""}}},
        ):
            with self.assertRaises(ValueError):
                feed.wikidata("Private", None, "Q123")

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
