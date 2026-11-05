"""US-wide current-price selection and actual paper integration, all offline."""
import datetime as dt
import json
import os
import tempfile
import unittest
import zipfile
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock

import httpx
import pandas as pd
from sqlalchemy import select, func

from cloud_app import auto_universe as auto, paper, worker, personal_data, research_ai
from cloud_app.database import PaperAccount, PaperFill, PaperPosition, Strategy
from cloud_app.local_demo import _atomic_json
from cloud_app.provider_process import ProviderProcess
from cloud_app.strategies import StrategySpec, get_dataset_bundle, run_strategy_backtest
from cloud_app.toss_quotes import TossQuoteClient, TossCredentials, TossOpenApiError, TossRateLimitError
from tests import test_personal_continuous as continuous

UTC = dt.timezone.utc
NOW = dt.datetime(2026, 11, 5, 15, 0, tzinfo=UTC)


def automatic_spec(**kwargs):
    values = dict(name="US market momentum", universe="us_all", symbols=[],
        factors=[{"kind":"momentum","lookback":2}],
        filters={"history_days":20,"min_average_volume":0},
        portfolio={"max_positions":1,"rebalance_days":1,"investment_fraction":.8,
                   "max_position_fraction":.5,"rebalance_weights":True,"stop_loss_pct":-.1})
    values.update(kwargs)
    return StrategySpec.model_validate(values)


def history(now=NOW, base=100.):
    required = auto.last_completed_session(now).isoformat()
    dates = pd.bdate_range(end=required, periods=80)
    return {"session":required,"source":"offline", "rows":[[d.date().isoformat(),base,base+1,base-1,base,1_000_000.] for d in dates]}


def seed(root, symbols, now=NOW):
    required = auto.last_completed_session(now).isoformat()
    _atomic_json(root / "catalog.json", {"symbols":symbols,"sha256":"offline-inventory", "date":now.astimezone(auto.EASTERN).date().isoformat()})
    _atomic_json(root / "progress.json", {"session":required,"catalog":"offline-inventory","outcomes":{s:"ready" for s in symbols}})
    for symbol in symbols:
        _atomic_json(auto._history_path(root, symbol), history(now))


def auto_http_execute(payload, configuration):
    """Spawned real adapter + HTTP, with only endpoint and replay clock replaced."""
    from cloud_app import auto_universe as child
    from cloud_app.toss_quotes import TossQuoteClient
    endpoint = os.environ["MILKYWAY_OFFLINE_TOSS_ENDPOINT"]
    if not endpoint.startswith("http://127.0.0.1:"): raise RuntimeError("offline endpoint required")
    TossQuoteClient.base_url = endpoint
    real_datetime = dt.datetime
    replay = real_datetime.fromisoformat(payload["now"])
    class Clock(real_datetime):
        @classmethod
        def now(cls, tz=None):
            return replay.astimezone(tz) if tz else replay.replace(tzinfo=None)
    child.dt.datetime = Clock
    return child._execute(payload, configuration)


class AutoSelectionTests(unittest.TestCase):
    def test_catalog_has_no_top_n_and_includes_adrs_class_shares_and_reits(self):
        names = [f"A{i:05d}|Company {i} Common Stock|Q|N|N|100|N|N" for i in range(6500)]
        names += ["ADR|Issuer American Depositary Shares|Q|N|N|100|N|N", "UNITED|United Company Common Stock|Q|N|N|100|N|N", "ETF|Index ETF|Q|N|N|100|Y|N", "TEST|Test|Q|Y|N|100|N|N"]
        nasdaq = "Symbol|Security Name|Market Category|Test Issue|Financial Status|Round Lot Size|ETF|NextShares\n"+"\n".join(names)
        other = "ACT Symbol|Security Name|Exchange|CQS Symbol|ETF|Round Lot Size|Test Issue|NASDAQ Symbol\nBRK.B|Berkshire Class B Common Stock|N|BRK.B|N|100|N|BRK.B\nREIT|Real Estate Trust Common Stock|N|REIT|N|100|N|REIT\nPREF|Issuer Preferred Shares|N|PREF|N|100|N|PREF"
        symbols = auto.parse_catalog(nasdaq, other)
        self.assertEqual(len(symbols),6504)
        self.assertTrue({"ADR","BRK.B","REIT","UNITED"} <= set(symbols))
        self.assertFalse({"ETF","TEST","PREF"} & set(symbols))

    def test_current_prices_change_selection_and_weights_without_changing_strategy(self):
        spec = automatic_spec()
        histories = {s:history() for s in ["AAA","BBB"]}
        quotes = {s:{"price":p,"observed_at":NOW.isoformat()} for s,p in [("AAA",105),("BBB",100)]}
        targets, weights, excluded, stamp = auto.select_from_market(spec,histories,quotes,NOW)
        self.assertEqual(targets,["AAA"]); self.assertEqual(weights,{"AAA":.5})
        quotes["BBB"]["price"] = 120
        self.assertEqual(auto.select_from_market(spec,histories,quotes,NOW)[0],["BBB"])
        two = spec.model_copy(update={"portfolio":spec.portfolio.model_copy(update={"max_positions":2})})
        self.assertEqual(auto.select_from_market(two,histories,quotes,NOW)[1],{"BBB":.4,"AAA":.4})

    def test_an_old_unselected_quote_does_not_expire_fresh_targets(self):
        quotes={"AAA":{"price":120,"observed_at":NOW.isoformat()}, "BBB":{"price":100,"observed_at":(NOW-dt.timedelta(seconds=179)).isoformat()}}
        result=auto.select_from_market(automatic_spec(),{s:history() for s in quotes},quotes,NOW)
        self.assertEqual(result[0],["AAA"])
        self.assertEqual(result[3],NOW.isoformat())

    def test_missing_stale_future_prices_and_history_are_visible_exclusions(self):
        histories = {s:history() for s in ["GOOD","OLD","FUTURE","NONE","STALE","LOW"]}
        histories["STALE"]["session"] = "2026-11-03"
        quotes = {s:{"price":100,"observed_at":NOW.isoformat()} for s in histories}
        quotes.pop("NONE");quotes["LOW"]["price"]=1
        quotes["OLD"]["observed_at"]=(NOW-dt.timedelta(seconds=181)).isoformat()
        quotes["FUTURE"]["observed_at"]=(NOW+dt.timedelta(seconds=1)).isoformat()
        result=auto.select_from_market(automatic_spec(),histories,quotes,NOW)
        self.assertEqual(result[0],["GOOD"])
        self.assertEqual(result[2],{"history":1,"quote":3,"filters":1})
        quotes["GOOD"]["price"]=float("nan")
        self.assertEqual(auto.select_from_market(automatic_spec(),histories,quotes,NOW)[0],[])

    def test_decision_rejects_expired_quotes_changed_spec_and_new_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            settings=replace(worker.get_settings(),dataset_dir=Path(directory)/"personal-data")
            root=auto.root_for(settings);seed(root,["AAA"])
            spec=automatic_spec()
            decision={"created_at":NOW.isoformat(),"quote_as_of":NOW.isoformat(),"targets":["AAA"],"history_session":"2026-11-04","catalog_sha256":"offline-inventory"}
            _atomic_json(root/"decisions.json",{auto.spec_digest(spec):decision})
            self.assertEqual(auto.decision_for(settings,spec,NOW)["targets"],["AAA"])
            with self.assertRaises(ValueError):auto.decision_for(settings,spec,NOW+dt.timedelta(seconds=181))
            with self.assertRaises(ValueError):auto.decision_for(settings,spec.model_copy(update={"name":"New strategy"}),NOW)
            _atomic_json(root/"catalog.json",{"date":"2026-11-05","sha256":"changed"})
            with self.assertRaises(ValueError):auto.decision_for(settings,spec,NOW)

    def test_failed_full_sweep_does_not_replace_a_complete_decision(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            _atomic_json(root/"catalog.json",{"symbols":[f"A{i:04d}" for i in range(201)],"sha256":"fixture"})
            _atomic_json(root/"decisions.json",{"previous":"complete"})
            client=Mock();client.get_prices.side_effect=[[],TossRateLimitError()]
            with patch.object(auto.time,"sleep"):
                with self.assertRaises(TossRateLimitError): auto._screen(client,root,{"specs":[automatic_spec().model_dump_json()]},NOW)
            self.assertEqual(json.loads((root/"decisions.json").read_text()),{"previous":"complete"})
            self.assertEqual([len(c.args[0]) for c in client.get_prices.call_args_list],[200,1])

    def test_toss_history_first_and_yahoo_only_when_history_is_unavailable(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);client=Mock();client.daily_candles.return_value=history()["rows"]
            with patch("yfinance.download") as yahoo, patch.object(auto.time,"sleep"):
                self.assertEqual(auto._history(client,root,["AAA"],"2026-11-04",NOW),{"AAA":"ready"})
                yahoo.assert_not_called()
            client.daily_candles.side_effect=TossRateLimitError(30)
            with patch("yfinance.download") as yahoo:
                with self.assertRaises(TossRateLimitError):auto._history(client,root,["BBB"],"2026-11-04",NOW)
                yahoo.assert_not_called()
            client.daily_candles.side_effect=TossOpenApiError("unavailable")
            frame=auto._frame(history()["rows"])
            with patch("yfinance.download",return_value=frame) as yahoo, patch.object(auto.time,"sleep"):
                self.assertEqual(auto._history(client,root,["BBB"],"2026-11-04",NOW),{"BBB":"ready"})
                self.assertEqual(json.loads(auto._history_path(root,"BBB").read_text())["source"],"yahoo_fallback")

    def test_rate_limit_cooldown_survives_a_new_refresh_call(self):
        from cloud_app.provider_process import ProviderOperationError
        with tempfile.TemporaryDirectory() as directory:
            settings=replace(worker.get_settings(),dataset_dir=Path(directory)/"personal-data")
            root=auto.root_for(settings);seed(root,["AAA"])
            with patch.object(auto._process,"run",side_effect=ProviderOperationError(429,"retry_after=300")) as provider:
                self.assertEqual(auto.refresh(settings,[automatic_spec()],{"key":"synthetic","secret":"synthetic"},NOW),(False,[]))
                self.assertIn("요청 한도",auto.status(settings)["message"])
                self.assertEqual(auto.refresh(settings,[automatic_spec()],{"key":"synthetic","secret":"synthetic"},NOW+dt.timedelta(seconds=61)),(False,[]))
                self.assertEqual(provider.call_count,1)

    def test_ai_response_can_save_an_automatic_strategy_without_any_ticker(self):
        reply={"reply":"미국 전체에서 선정합니다", "strategy":automatic_spec().model_dump(mode="json")}
        payload={"status":"completed","output":[{"type":"message","content":[{"type":"output_text","text":json.dumps(reply)}]}]}
        client=httpx.Client(transport=httpx.MockTransport(lambda _:httpx.Response(200,json=payload)))
        with patch.object(research_ai.httpx,"Client",return_value=client):
            result=research_ai._execute({}, {"key":"synthetic"})
        self.assertNotIn("error",result)
        self.assertEqual(result["reply"]["strategy"]["symbols"],[])
        self.assertEqual(result["reply"]["strategy"]["universe"],"us_all")

    def test_backtest_reselects_across_market_and_pins_immutable_history(self):
        with tempfile.TemporaryDirectory() as directory:
            settings=replace(worker.get_settings(),personal_local_mode=True,app_env="development",dataset_dir=Path(directory)/"personal-data",terminal_events_path=Path(directory)/"events.jsonl")
            root=auto.root_for(settings);seed(root,["AAA","BBB","BRK.B"])
            auto.prepare_backtest_generation(settings)
            captured=auto.backtest_settings(settings)
            bundle=get_dataset_bundle(captured)
            self.assertEqual(set(bundle.data),{"AAA","BBB","BRK.B"})
            result=run_strategy_backtest(automatic_spec(),start="2026-08-17",end="2026-11-04",bias_mode="exploratory",settings=settings)
            self.assertFalse(result["certification_eligible"])
            self.assertGreater(result["metrics"]["trade_count"],0)
            self.assertIn("현재 미국 상장주식 전체",result["caveat"])
            # Changing live screening history does not change the captured generation.
            _atomic_json(auto._history_path(root,"AAA"),history(base=200))
            self.assertEqual(get_dataset_bundle(captured).fingerprint,bundle.fingerprint)


class AutoPaperIntegrationTests(unittest.TestCase):
    def test_live_sweep_to_paper_fills_rotation_and_stale_fail_closed(self):
        f=continuous.ContinuousPaperTests()
        f.setUp();self.addCleanup(f.tearDown)
        spec=automatic_spec()
        root=auto.root_for(f.settings)
        runner=ProviderProcess(auto_http_execute);self.addCleanup(runner.close)
        real_refresh, real_history = auto.refresh, personal_data.refresh_personal_data
        def data_step():
            with patch.object(auto,"refresh",side_effect=lambda settings,specs,configuration: real_refresh(settings,specs,configuration,f.now)), patch.object(personal_data,"refresh_personal_data",side_effect=lambda symbols,settings,**kw: real_history(symbols,settings,now=f.now,**kw)):
                return worker.refresh_personal_history(f.settings)
        with patch.object(auto,"_process",runner):
            with f.sessions() as db:
                strategy=db.get(PaperAccount,f.account).strategy
                strategy.spec_json=spec.model_dump_json();db.commit()
            seed(root,["AAA","BBB"],f.now)
            f.prices.update(AAA=110.,BBB=100.)
            self.assertFalse(data_step())
            self.assertEqual(auto.decision_for(f.settings,spec,f.now)["targets"],["AAA"])
            # The real data-worker orchestration prepares corporate actions before execution.
            f.tick()
            with f.sessions() as db:
                self.assertEqual(db.scalars(select(PaperPosition.ticker)).all(),["AAA","AAA"])
                count=db.scalar(select(func.count()).select_from(PaperFill))
                self.assertEqual(count,2)
            f.tick()
            with f.sessions() as db:self.assertEqual(db.scalar(select(func.count()).select_from(PaperFill)),count)
            # No rule or ticker-list edit: a new current price changes selection.
            f.now+=dt.timedelta(days=1);f.monotonic+=86400
            seed(root,["AAA","BBB"],f.now);f.prices.update(AAA=100.,BBB=125.)
            self.assertFalse(data_step())
            self.assertEqual(auto.decision_for(f.settings,spec,f.now)["targets"],["BBB"])
            f.tick()
            with f.sessions() as db:
                self.assertEqual(sorted(db.scalars(select(PaperPosition.ticker)).all()),["AAA","BBB"])
                self.assertEqual(db.scalar(select(func.count()).select_from(PaperFill)),4)
                # Exposure is computed from actual current execution prices, with a 50% per-stock cap.
                account=db.get(PaperAccount,f.account)
                position=db.scalar(select(PaperPosition).where(PaperPosition.account_id==f.account))
                self.assertLessEqual(position.shares*125/(account.cash+position.shares*125),.501)
            f.now+=dt.timedelta(minutes=4);f.monotonic+=240
            f.tick()
            with f.sessions() as db:self.assertEqual(db.scalar(select(func.count()).select_from(PaperFill)),4)
            # Preserve immutable research inputs in backups; rebuild screening
            # caches after restore rather than restoring stale trading decisions.
            from cloud_app.local_ops import create_backup, restore_backup
            auto.prepare_backtest_generation(f.settings)
            archive=create_backup(f.runtime,f.root/"backups")
            with zipfile.ZipFile(archive) as backup:
                names=backup.namelist()
                self.assertIn("auto-market/backtests/current.json",names)
                self.assertFalse(any(name.startswith("auto-market/history/") for name in names))
                self.assertNotIn("auto-market/decisions.json",names)
            restored=f.root/"restored"
            restore_backup(archive,restored,f.root/"restore-backups")
            self.assertTrue((restored/"auto-market/backtests/current.json").is_file())
            self.assertFalse((restored/"auto-market/decisions.json").exists())


class TossDailyHistoryTests(unittest.TestCase):
    def setUp(self):
        self.client = TossQuoteClient(TossCredentials("offline", "offline"))
        self.client.session = MagicMock()
        self.client.token = "offline-token"
        self.client.token_expires_at = dt.datetime.now(UTC) + dt.timedelta(hours=1)

    def tearDown(self):
        self.client.session.close()

    def response(self, candles, cursor=None, status=200):
        response = MagicMock(status_code=status)
        raw = json.dumps({"result":{"candles":candles,"nextBefore":cursor}}).encode()
        response.headers = {"Content-Length":str(len(raw))}
        response.iter_content.return_value = [raw]
        return response

    def candle(self, day, close=100):
        return {"timestamp":f"2026-11-{day:02d}T00:00:00+09:00","openPrice":"100","highPrice":"101","lowPrice":"99","closePrice":str(close),"volume":"10000","currency":"USD"}

    def test_adjusted_pages_preserve_source_dates_and_deduplicate_inclusive_boundary(self):
        self.client.session.get.side_effect = [self.response([self.candle(4),self.candle(3)],"2026-11-03T00:00:00+09:00"), self.response([self.candle(3),self.candle(2)])]
        rows = self.client.daily_candles("BRK.B", count=3)
        self.assertEqual([row[0] for row in rows],["2026-11-02","2026-11-03","2026-11-04"])
        calls = self.client.session.get.call_args_list
        self.assertEqual(calls[0].kwargs["params"]["adjusted"],"true")
        self.assertEqual(calls[1].kwargs["params"]["before"],"2026-11-03T00:00:00+09:00")

    def test_conflicting_pages_and_repeated_cursors_are_rejected(self):
        self.client.session.get.side_effect = [self.response([self.candle(4)],"2026-11-04T00:00:00+09:00"),self.response([self.candle(4,200)])]
        with self.assertRaises(TossOpenApiError):self.client.daily_candles("AAA", count=3)
        self.client.session.get.side_effect = [self.response([self.candle(4)],"2026-11-04T00:00:00+09:00"),self.response([self.candle(4)],"2026-11-04T00:00:00+09:00")]
        with self.assertRaises(TossOpenApiError):self.client.daily_candles("AAA", count=3)

    def test_rate_denial_is_not_retried_in_the_candle_loop(self):
        self.client.session.get.return_value = self.response([],status=429)
        with self.assertRaises(TossRateLimitError):self.client.daily_candles("AAA")
        self.assertEqual(self.client.session.get.call_count,1)
