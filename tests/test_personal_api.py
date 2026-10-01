"""Personal onboarding, operational readiness and complete-history API tests."""
import asyncio
import datetime as dt
import json
import hashlib
import os
import stat
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from cloud_app import config, main
from cloud_app.database import Base, BacktestJob, EquityPoint, PaperAccount, PaperFill, RuntimeHeartbeat, Strategy, User, utcnow
from cloud_app.strategies import StrategySpec


async def consume(response):
    result = b""
    async for chunk in response.body_iterator:
        result += chunk if isinstance(chunk, bytes) else chunk.encode()
    await response.background()
    return result


class PersonalApiTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.engine = create_engine("sqlite:///" + str(self.root / "test.sqlite3"))
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine, expire_on_commit=False)()
        self.settings = replace(config.get_settings(), personal_local_mode=True, local_demo_data=False,
                                dataset_dir=self.root / "data", quote_provider="member", credential_backend="local",
                                authority_enabled=False, shared_ai_enabled=False, member_credentials_enabled=True)
        self.patches = [patch.object(main,"settings",self.settings), patch("cloud_app.paper.get_settings",return_value=self.settings)]
        for item in self.patches: item.start()
        self.user = User(email="local@example.test",display_name="local",password_hash="unused")
        self.other = User(email="other@example.test",display_name="other",password_hash="unused")
        self.session.add_all([self.user,self.other]);self.session.flush()
        self.spec = StrategySpec(name="manual test",symbols=["AAPL","MSFT"],factors=[{"kind":"momentum"}],portfolio={"max_positions":2})
        self.strategy = Strategy(user_id=self.user.id,name=self.spec.name,spec_json=self.spec.model_dump_json(),original_prompt="")
        self.session.add(self.strategy);self.session.flush()
        self.account = PaperAccount(user_id=self.user.id,strategy_id=self.strategy.id,name="paper",cash=100000,initial_cash=100000)
        self.session.add(self.account);self.session.commit()

    def tearDown(self):
        self.session.close();self.engine.dispose()
        for item in reversed(self.patches): item.stop()
        self.directory.cleanup()

    def test_detail_route_only_reads_allowlisted_personal_cache(self):
        from cloud_app.market_details import _provider
        with patch.object(_provider,'run') as external:
            payload=main.personal_market_detail('sp500',self.user)
            self.assertEqual(payload['id'],'sp500')
            self.assertEqual(payload['history']['rows'],[])
            external.assert_not_called()
        with self.assertRaises(HTTPException) as error:
            main.personal_market_detail('unknown',self.user)
        self.assertEqual(error.exception.status_code,404)
        with patch.object(main,'settings',replace(self.settings,personal_local_mode=False)):
            with self.assertRaises(HTTPException):main.personal_market_detail('sp500',self.user)

    def test_company_routes_read_cache_and_queue_public_work_with_csrf(self):
        from cloud_app import company_worker
        with patch.object(company_worker._provider, 'run') as external:
            payload = main.personal_company_detail('kr_13', '005930.KS', self.user)
            self.assertEqual(payload['symbol'], '005930.KS')
            queued = main.personal_company_refresh('kr_13', '005930.KS', self.user)
            self.assertEqual(queued['status'], 'queued')
            external.assert_not_called()
        routes = {route.path: route for route in main.app.routes if hasattr(route, 'dependant')}
        refresh = routes['/api/company-details/{sector_id}/{symbol}/refresh']
        self.assertIn(main.csrf_guard, [dep.call for dep in refresh.dependant.dependencies])
        with patch.object(main, 'settings', replace(self.settings, personal_local_mode=False)):
            with self.assertRaises(HTTPException): main.personal_company_detail('kr_13', '005930.KS', self.user)

    def test_entity_routes_require_authentication_and_csrf_and_known_identity(self):
        payload = main.personal_company_detail('kr_13', '005930.KS', self.user)
        entity = main.personal_company_entity(payload['entity_key'], self.user)
        self.assertEqual(entity['entity_key'], payload['entity_key'])
        routes = {route.path: route for route in main.app.routes if hasattr(route, 'dependant')}
        self.assertIn(main.current_user, [d.call for d in routes['/api/company-entities/{entity_key}'].dependant.dependencies])
        self.assertIn(main.csrf_guard, [d.call for d in routes['/api/company-entities/{entity_key}/refresh'].dependant.dependencies])
        with self.assertRaises(HTTPException):
            main.personal_company_entity('c_' + '0'*32, self.user)

    def test_company_network_route_is_authenticated_bounded_and_cache_only(self):
        from cloud_app.company_graph import CompanyGraph
        from cloud_app.company_schemas import CompanyKnowledge
        source = dict(label='Synthetic filing', url='https://www.sec.gov/report.htm',
                      as_of='2025-12-31', level='primary')
        graph = CompanyGraph(self.settings)
        graph.ingest(CompanyKnowledge(symbol='AAA', name='Root', relations=[dict(
            name='Middle', symbol='BBB', kind='supplier', detail='공시된 공급 관계', source=source)]))
        root, via = graph.by_symbol('AAA')['id'], graph.by_symbol('BBB')['id']
        with patch('cloud_app.company_worker._provider.run') as external:
            payload = main.personal_company_network(root, via, 1, 'all', self.user)
            self.assertEqual(payload['via']['id'], via)
            external.assert_not_called()
        route = next(row for row in main.app.routes
                     if row.path == '/api/company-entities/{entity_key}/network')
        self.assertIn(main.current_user, [dep.call for dep in route.dependant.dependencies])
        parameters = main.app.openapi()['paths'][route.path]['get']['parameters']
        query = {row['name']: row['schema'] for row in parameters}
        self.assertEqual((query['page']['minimum'], query['page']['maximum']), (1, 50))
        self.assertEqual(query['kind']['pattern'], '^(all|supplier|customer|partner|competitor)$')
        with patch.object(main, 'settings', replace(self.settings, personal_local_mode=False)):
            with self.assertRaises(HTTPException):
                main.personal_company_network(root, via, 1, 'all', self.user)

    def test_new_install_dashboard_works_before_history_or_keys(self):
        payload=main.dashboard(self.user,self.session)
        self.assertTrue(payload["personal_local_mode"])
        self.assertFalse(payload["personal_data"]["ready"])
        self.assertEqual(payload["operational"]["status"],"worker_offline")
        self.assertFalse(payload["market_data_connection"]["connected"])

    def test_readiness_requires_all_workers_but_bootstrap_does_not_require_keys(self):
        self.assertEqual(main.startup_ready(self.session)["status"],"ready")
        self.assertEqual(main.ready(self.session).status_code,503)
        for component in ("paper-worker","backtest-worker","personal-data"):
            self.session.add(RuntimeHeartbeat(component=component,instance_id="test",observed_at=utcnow(),detail="running"))
        self.session.commit()
        self.assertEqual(main.ready(self.session).status_code,200)
        self.assertEqual(main.trading_ready(self.user,self.session).status_code,503)

    def test_latest_history_and_full_exports_keep_old_and_new_records(self):
        origin=dt.datetime(2026,1,1,tzinfo=dt.timezone.utc)
        self.session.add_all([EquityPoint(account_id=self.account.id,equity=1000+number,cash=1000,observed_at=origin+dt.timedelta(minutes=number)) for number in range(3002)])
        self.session.add_all([PaperFill(account_id=self.account.id,ticker="AAPL",side="BUY",shares=1,price=100,fee=.3,reason="rebalance",dedupe_key="export-"+str(number),executed_at=origin+dt.timedelta(minutes=number)) for number in range(302)])
        self.session.commit()
        payload=main.account_history(self.account.id,self.user,self.session)
        self.assertEqual(len(payload["equity"]),3000)
        self.assertEqual(payload["equity"][-1]["value"],4001)
        self.assertEqual(payload["pagination"]["point_total"],3002)
        older=main.account_history(self.account.id,self.user,self.session,point_offset=3000,fill_offset=300)
        self.assertEqual(len(older["equity"]),2)
        self.assertEqual(len(older["fills"]),2)
        csv=asyncio.run(consume(main.export_account(self.account.id,"fills",self.user,self.session))).decode("utf-8-sig")
        self.assertEqual(len(csv.splitlines()),303)
        with self.assertRaises(HTTPException) as exc:
            main.export_account(self.account.id,"fills",self.other,self.session)
        self.assertEqual(exc.exception.status_code,404)

    def test_recent_worker_error_is_never_reported_as_running(self):
        for component in ("paper-worker","backtest-worker","personal-data"):
            self.session.add(RuntimeHeartbeat(component=component,instance_id="test",observed_at=utcnow(),detail="error=RuntimeError" if component=="paper-worker" else "running"))
        self.session.commit()
        payload=main.dashboard(self.user,self.session)
        self.assertEqual(payload["operational"]["status"],"worker_error")

    def test_backtest_pagination_and_export_include_all_results(self):
        for number in range(53):
            self.session.add(BacktestJob(user_id=self.user.id,strategy_id=self.strategy.id,status="completed",bias_mode="exploratory",start_date=dt.date(2026,1,1),end_date=dt.date(2026,2,1),result_json=json.dumps({"number":number})))
        self.session.commit()
        self.assertEqual(len(main.list_backtests(self.user,self.session)),50)
        self.assertEqual(len(main.list_backtests(self.user,self.session,offset=50)),3)
        payload=json.loads(asyncio.run(consume(main.export_backtests(self.user,self.session))))
        self.assertEqual(len(payload),53)
        self.assertEqual(payload[0]["strategy_spec"]["symbols"],["AAPL","MSFT"])

    def test_manual_strategy_requires_symbols_and_active_capacity_is_bounded(self):
        with self.assertRaises(HTTPException):
            main.create_strategy(main.StrategyBody(spec=StrategySpec(name="missing",factors=[{"kind":"momentum"}])),self.user,self.session)
        large=StrategySpec(name="too many",symbols=["T"+chr(65+i) for i in range(20)],factors=[{"kind":"momentum"}])
        with self.assertRaises(HTTPException) as exc:
            main._ensure_personal_quote_capacity(self.session,self.user.id,large)
        self.assertEqual(exc.exception.status_code,409)

    def test_cloud_mode_cannot_silently_ignore_personal_symbol_selection(self):
        with patch.object(main,"settings",replace(self.settings,personal_local_mode=False)):
            with self.assertRaises(HTTPException) as exc:
                main._save_strategy(self.session,self.user,self.spec,"")
        self.assertEqual(exc.exception.status_code,422)

    def test_install_session_secret_is_atomic_persistent_and_not_shared_default(self):
        with patch.object(config,"ROOT",self.root),patch.dict("os.environ",{"PERSONAL_LOCAL_MODE":"true","SESSION_SECRET":"","SESSION_SECRET_FILE":""}):
            with ThreadPoolExecutor(max_workers=8) as pool:
                values=list(pool.map(lambda _:config._session_secret(),range(16)))
            self.assertEqual(len(set(values)),1)
            self.assertEqual(values[0],config._session_secret())
            self.assertNotEqual(values[0],"dev-only-change-me")
            self.assertEqual((self.root / "runtime/.session_secret").stat().st_mode & 0o777,0o600)

    def test_concurrent_strategy_saves_cannot_exceed_100_symbol_union(self):
        for offset in range(0,80,20):
            spec=StrategySpec(name="existing"+str(offset),symbols=["T"+str(i) for i in range(offset,offset+20)],factors=[{"kind":"momentum"}])
            self.session.add(Strategy(user_id=self.user.id,name=spec.name,spec_json=spec.model_dump_json(),original_prompt=""))
        self.session.commit()
        barrier=threading.Barrier(2)
        lock=main.quota_allocation
        @contextmanager
        def simultaneous_admission(session,scope,owner):
            barrier.wait(timeout=5)
            with lock(session,scope,owner):
                yield
        def save(offset):
            with sessionmaker(bind=self.engine,expire_on_commit=False)() as session:
                user=session.get(User,self.user.id)
                spec=StrategySpec(name="concurrent"+str(offset),symbols=["T"+str(i) for i in range(offset,offset+18)],factors=[{"kind":"momentum"}])
                try:
                    main._save_strategy(session,user,spec,"")
                    return 201
                except HTTPException as exc:
                    return exc.status_code
        with patch.object(main,"quota_allocation",simultaneous_admission),ThreadPoolExecutor(max_workers=2) as pool:
            outcomes=list(pool.map(save,[100,200]))
        self.assertEqual(sorted(outcomes),[201,409])


class PersistentLocalSecretTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)

    def tearDown(self):
        self.directory.cleanup()

    def test_six_independent_cold_start_processes_publish_one_complete_key(self):
        code = """import hashlib,sys,time
from pathlib import Path
from cloud_app.config import persistent_local_secret
root=Path(sys.argv[1]);(root/('ready-'+sys.argv[2])).touch()
while not (root/'go').exists(): time.sleep(.005)
print(hashlib.sha256(persistent_local_secret(root/'.market_credential_secret').encode()).hexdigest())
"""
        processes = [subprocess.Popen([sys.executable,'-c',code,str(self.root),str(index)],
                      stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True) for index in range(6)]
        try:
            deadline=time.monotonic()+15
            while len(list(self.root.glob('ready-*')))<6 and time.monotonic()<deadline:
                time.sleep(.01)
            self.assertEqual(len(list(self.root.glob('ready-*'))),6)
            (self.root/'go').touch()
            results=[]
            for process in processes:
                output,error=process.communicate(timeout=15)
                self.assertEqual(process.returncode,0,error[-500:])
                results.append(output.strip())
            self.assertEqual(len(set(results)),1)
            path=self.root/'.market_credential_secret'
            self.assertEqual(results[0],hashlib.sha256(path.read_bytes()).hexdigest())
            self.assertEqual(path.stat().st_mode & 0o777,0o600)
            self.assertEqual(list(self.root.glob('.secret-new-*')),[])
        finally:
            for process in processes:
                if process.poll() is None:process.kill()
                process.communicate()

    def test_process_crash_before_or_after_publication_never_exposes_partial_key(self):
        code = """import os,sys
from pathlib import Path
from unittest.mock import patch
from cloud_app.config import persistent_local_secret
link=os.link
def crash(source,target):
    if sys.argv[2]=='after':link(source,target)
    os._exit(23)
with patch('cloud_app.config.os.link',side_effect=crash):persistent_local_secret(Path(sys.argv[1]))
"""
        for stage in ('before','after'):
            with self.subTest(stage=stage):
                path=self.root/stage/'.secret'
                completed=subprocess.run([sys.executable,'-c',code,str(path),stage],capture_output=True,text=True,timeout=15)
                self.assertEqual(completed.returncode,23)
                if stage=='before':
                    self.assertFalse(path.exists())
                    original=None
                else:
                    original=path.read_text()
                    self.assertEqual(len(original),64)
                recovered=config.persistent_local_secret(path)
                self.assertEqual(len(recovered),64)
                if original is not None:self.assertEqual(recovered,original)
                self.assertEqual(config.persistent_local_secret(path),recovered)

    def test_fsync_failure_returns_no_key_and_retry_keeps_any_published_key(self):
        sync=os.fsync
        for failing_kind in ('file','directory'):
            with self.subTest(failing_kind=failing_kind):
                path=self.root/failing_kind/'.secret'
                def fail(descriptor):
                    mode=os.fstat(descriptor).st_mode
                    if (failing_kind=='file' and stat.S_ISREG(mode)) or (failing_kind=='directory' and stat.S_ISDIR(mode)):
                        raise OSError('synthetic persistence failure')
                    return sync(descriptor)
                with patch('cloud_app.config.os.fsync',side_effect=fail):
                    with self.assertRaises(OSError):config.persistent_local_secret(path)
                before=path.read_text() if path.exists() else None
                if failing_kind=='file':self.assertIsNone(before)
                after=config.persistent_local_secret(path)
                if before is not None:self.assertEqual(after,before)
                self.assertEqual(list(path.parent.glob('.secret-new-*')),[])

    def test_invalid_existing_keys_are_rejected_without_regeneration(self):
        for content in ('','short','x'*4097,'k'*32+' '*5000):
            path=self.root/'.secret'
            path.write_text(content);path.chmod(0o600)
            with self.assertRaises(RuntimeError):config.persistent_local_secret(path)
            self.assertEqual(path.read_text(),content)
        path.write_text('synthetic-private-key-material-for-permission-test')
        path.chmod(0o644)
        with self.assertRaises(RuntimeError):config.persistent_local_secret(path)
        self.assertEqual(path.stat().st_mode & 0o777,0o644)

    @unittest.skipUnless(hasattr(os,'O_NOFOLLOW'),'requires Linux/macOS no-follow open')
    def test_symlink_and_dangling_symlink_are_rejected_without_target_change(self):
        target=self.root/'target'
        target.write_text('synthetic-existing-target-that-must-not-change');target.chmod(0o600)
        path=self.root/'.secret'
        for source in (target,self.root/'absent'):
            path.symlink_to(source)
            with self.assertRaises((OSError,RuntimeError)):config.persistent_local_secret(path)
            self.assertTrue(path.is_symlink());path.unlink()
        self.assertEqual(target.read_text(),'synthetic-existing-target-that-must-not-change')
        self.assertFalse((self.root/'absent').exists())

    @unittest.skipUnless(hasattr(os,'mkfifo'),'requires Unix FIFO support')
    def test_fifo_is_rejected_without_blocking_on_open(self):
        path=self.root/'.secret';os.mkfifo(path,0o600)
        code="""import sys
from pathlib import Path
from cloud_app.config import persistent_local_secret
try:persistent_local_secret(Path(sys.argv[1]))
except (OSError,RuntimeError):sys.exit(0)
sys.exit(1)
"""
        completed=subprocess.run([sys.executable,'-c',code,str(path)],capture_output=True,text=True,timeout=5)
        self.assertEqual(completed.returncode,0,completed.stderr[-500:])
        self.assertTrue(stat.S_ISFIFO(path.stat().st_mode))

    def test_credential_encryption_uses_persisted_key_across_reloads(self):
        from cloud_app import credential_store
        from types import SimpleNamespace
        settings=SimpleNamespace(production=False,credential_backend='local',ai_credential_secret='',market_credential_secret='')
        with patch.object(credential_store,'ROOT',self.root):
            encrypted=credential_store.encrypt_credential('synthetic-test-credential',settings,purpose='market',owner_id='synthetic-owner',field='kis:paper:app key')
            path=self.root/'runtime/.market_credential_secret'
            original=path.read_bytes()
            self.assertEqual(credential_store.decrypt_credential(encrypted,settings,purpose='market',owner_id='synthetic-owner',field='kis:paper:app key',error_message='synthetic failure'),'synthetic-test-credential')
            self.assertEqual(path.read_bytes(),original)
            self.assertEqual(credential_store._master_secret(settings,'market').encode(),original)


if __name__ == "__main__":
    unittest.main()
