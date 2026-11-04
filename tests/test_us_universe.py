"""Full-pool ranking, closed-bar signals and bounded resumable collection."""
import datetime as dt
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, Mock

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from cloud_app import us_universe as universe, main
from cloud_app.database import Base, User, Strategy, MarketDataConnection
from cloud_app.research_models import ResearchBase
from cloud_app.provider_process import ProviderOperationError
from cloud_app.strategies import StrategySpec, get_dataset_bundle, run_strategy_backtest


def bars(required, count=90, growth=1):
    return [[day.date().isoformat(),100+i*growth,101+i*growth,99+i*growth,100+i*growth,1000000]
            for i,day in enumerate(pd.bdate_range(end=required,periods=count))]


class UniverseTests(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory()
        self.engine=create_engine("sqlite:///"+self.directory.name+"/ledger")
        Base.metadata.create_all(self.engine);ResearchBase.metadata.create_all(self.engine)
        self.factory=sessionmaker(bind=self.engine,expire_on_commit=False)
        self.settings=replace(main.settings,personal_local_mode=True,app_env="development",dataset_dir=Path(self.directory.name)/"data",snapshots_glob=str(Path(self.directory.name)/"snapshots/*.json"))
        self.spec=StrategySpec(name="Whole market",universe="us_market",factors=[{"kind":"momentum","lookback":20}],portfolio={"max_positions":3})
        with self.factory() as db:
            user=User(email="test@invalid.test",display_name="Test",password_hash="unused")
            db.add(user);db.flush();self.owner=user.id
            db.add(Strategy(user_id=user.id,name=self.spec.name,spec_json=self.spec.model_dump_json()))
            db.add(MarketDataConnection(user_id=user.id,provider="toss",environment="live",encrypted_api_key="synthetic",encrypted_api_secret="synthetic",key_hint="test",secret_hint="test"));db.commit()
        self.now=dt.datetime(2026,11,4,17,tzinfo=dt.timezone.utc);self.required=dt.date(2026,11,3)
        self.patches=[patch.object(universe,"SessionLocal",self.factory),patch.object(universe,"utcnow",return_value=self.now),
                      patch.object(universe,"last_completed_session",return_value=self.required),patch.object(universe,"_configuration",return_value={"key":"synthetic","secret":"synthetic"})]
        for item in self.patches:item.start()

    def tearDown(self):
        for item in reversed(self.patches):item.stop()
        self.engine.dispose();self.directory.cleanup()

    def test_catalog_covers_every_exchange_without_etfs_or_fixed_ticker_shortlist(self):
        payload={"result":[{"symbol":"A"+str(i),"name":"Equity "+str(i),"securityType":"STOCK","isCommonShare":True} for i in range(250)]}
        payload["result"] += [{"symbol":"ETF","name":"ETF","securityType":"ETF","isCommonShare":True},
                              {"symbol":"PREF","name":"Preferred","securityType":"STOCK","isCommonShare":False}]
        self.assertEqual(len(universe.parse_catalog(payload,"NASDAQ")),250)
        with self.assertRaises(ValueError):universe.parse_catalog({"result":[]},"NYSE")

    def test_candle_parser_uses_completed_us_date_and_rejects_invalid_ohlc(self):
        def candle(day, **changes):
            return {"timestamp":day+"T00:00:00-05:00","currency":"USD","openPrice":"10","highPrice":"12","lowPrice":"9","closePrice":"11","volume":"100",**changes}
        result={"result":{"candles":[candle("2026-11-04"),candle("2026-11-03")],"nextBefore":None}}
        values,_=universe.parse_candles(result,self.required)
        self.assertEqual([r[0] for r in values],["2026-11-03"])
        for changes in ({"currency":"KRW"},{"highPrice":"1"},{"closePrice":"NaN"},{"volume":True}):
            with self.assertRaises(ValueError):universe.parse_candles({"result":{"candles":[candle("2026-11-03",**changes)]}},self.required)

    def test_ranking_scans_more_than_twenty_and_selects_from_entire_pool(self):
        rows=[("A"+str(i),bars(self.required,growth=(i+1)/100)) for i in range(60)]
        targets,eligible=universe.rank(iter(rows),self.spec,self.required)
        self.assertEqual(targets,["A59","A58","A57"])
        self.assertEqual(eligible,60)
        self.assertNotIn("symbols",universe.key(self.spec))

    def test_halted_missing_sessions_are_not_treated_as_consecutive_trading_history(self):
        complete=bars(self.required,count=90)
        missing=bars(self.required,count=90,growth=10)
        del missing[-5]
        targets,eligible=universe.rank(iter([("AAA",complete),("HALT",missing)]),self.spec,self.required)
        self.assertEqual(targets,["AAA"]);self.assertEqual(eligible,1)

    def test_quote_and_history_failure_waits_without_claiming_ready(self):
        runner=Mock();runner.run.side_effect=ProviderOperationError(429,"retry:60")
        universe.tick(self.settings,runner);universe.tick(self.settings,runner)
        self.assertEqual(runner.run.call_count,1)
        value=universe.status(self.settings,self.owner,self.spec)
        self.assertEqual(value["error"],"rate_limited");self.assertFalse(value["ready"])

    def test_one_bad_history_is_reported_while_transient_network_failures_are_not_excluded(self):
        payload={"operation":"history","symbols":["AAA","BAD","EMPTY"],"required":self.required.isoformat(),"needed":1}
        candle={"timestamp":"2026-11-03T00:00:00-05:00","openPrice":"10","highPrice":"11","lowPrice":"9","closePrice":"10","volume":"100","currency":"USD"}
        def response(client,path,params):
            if params["symbol"]=="BAD":raise universe.HistoryUnavailable("Unavailable")
            return {"result":{"candles":[] if params["symbol"]=="EMPTY" else [candle]}}
        with patch.object(universe,"_client",object()),patch.object(universe,"_request",side_effect=response):
            result=universe._execute(payload,{})
        self.assertEqual(len(result["AAA"]["rows"]),1)
        self.assertEqual(result["BAD"]["error"],"unavailable")
        self.assertEqual(result["EMPTY"]["error"],"unavailable")
        with patch.object(universe,"_client",object()),patch.object(universe,"_request",side_effect=TimeoutError):
            with self.assertRaises(TimeoutError):universe._execute(payload,{})

    def test_collection_checkpoints_and_exports_one_immutable_full_market_generation(self):
        names={market:"A"+str(i) for i,market in enumerate(universe.MARKETS)}
        def response(payload,*args,**kwargs):
            if payload["operation"]=="catalog":
                market=payload["market"]
                return [{"symbol":names[market],"name":market,"market":market}]
            return {name:bars(self.required,growth=int(name[1:])+1) for name in payload["symbols"]}
        runner=Mock(run=Mock(side_effect=response))
        for _ in range(4):universe.tick(self.settings,runner)
        self.assertEqual(universe.status(self.settings,self.owner,self.spec)["total"],4)
        self.assertFalse(universe.status(self.settings,self.owner,self.spec)["ready"])
        universe.tick(self.settings,runner);universe.tick(self.settings,runner)
        value=universe.status(self.settings,self.owner,self.spec)
        self.assertTrue(value["ready"]);self.assertEqual(value["processed"],4)
        called=runner.run.call_count;universe.tick(self.settings,runner);self.assertEqual(runner.run.call_count,called)
        captured=universe.dataset_settings(self.settings,self.owner)
        bundle=get_dataset_bundle(captured)
        self.assertEqual(bundle.symbol_count,4)
        self.assertFalse(bundle.forward_data_gate_ready)
        self.assertEqual(set(bundle.data),set(names.values()))
        self.assertTrue(all(not row.get("certification_eligible") for row in bundle.snapshots))
        self.assertEqual(universe.candidates(self.settings,self.owner,self.spec),["A3","A2","A1"])
        with self.assertRaisesRegex(ValueError,"백테스트 가능 기간"):
            run_strategy_backtest(self.spec,start="2025-01-01",end="2026-11-03",bias_mode="exploratory",settings=captured)
        result=run_strategy_backtest(self.spec,start=str(bundle.index[65].date()),end="2026-11-03",bias_mode="exploratory",settings=captured)
        self.assertGreater(result["metrics"]["trade_count"],0)
        self.assertFalse(result["certification_eligible"])
        with self.factory() as db:
            db.get(MarketDataConnection,self.owner).encrypted_api_secret="rotated";db.commit()
        self.assertFalse(universe.status(self.settings,self.owner,self.spec)["ready"])

    def test_changed_credentials_cannot_publish_inflight_catalog(self):
        def rotate(*args,**kwargs):
            with self.factory() as db:
                db.get(MarketDataConnection,self.owner).encrypted_api_secret="rotated";db.commit()
            return [{"symbol":"AAA","name":"Test","market":"NYSE"}]
        universe.tick(self.settings,Mock(run=Mock(side_effect=rotate)))
        with universe._db(self.settings,self.owner) as db:
            self.assertEqual(db.execute("SELECT count(*) FROM instruments").fetchone()[0],0)

    def test_http_status_never_creates_cache_or_calls_provider(self):
        with patch.object(universe,"ProviderProcess") as provider:
            self.assertFalse(universe.status(self.settings,self.owner,self.spec)["ready"])
            self.assertFalse(universe.database_path(self.settings,self.owner).exists())
            provider.assert_not_called()

    def test_whole_market_schema_requires_no_fixed_symbols(self):
        self.assertEqual(self.spec.symbols,[])
        with self.assertRaises(ValueError):StrategySpec(name="Bad",universe="us_market",symbols=["AAPL"],factors=[{"kind":"momentum"}])

    def test_toss_quote_worker_accepts_200_symbols_and_keeps_kis_limit(self):
        from cloud_app.worker import PersonalQuoteProvider
        for provider,maximum in (("toss",200),("kis",20)):
            with patch("cloud_app.worker.ProviderProcess") as process:
                process.return_value.run.return_value=[]
                client=PersonalQuoteProvider({"provider":provider},10)
                client.fetch(["A"+str(i) for i in range(maximum)])
                process.return_value.run.assert_called_once()
                with self.assertRaises(ValueError):client.fetch(["A"+str(i) for i in range(maximum+1)])
                client.close()
