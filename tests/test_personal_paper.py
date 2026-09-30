"""Offline personal-ledger fault harness: deterministic time, real SQLite commits."""
import datetime as dt
import math
import time
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import pandas as pd
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from cloud_app.database import Base, BacktestJob, EquityPoint, MarketDataConnection, MemberQuote, PaperAccount, PaperFill, PaperPosition, RuntimeHeartbeat, Strategy, User
from cloud_app import paper, worker
from cloud_app.strategies import StrategySpec


class PersonalPaperTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.engine = create_engine('sqlite:///' + str(Path(self.directory.name) / 'ledger.sqlite3'))
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine, autoflush=False, expire_on_commit=False)
        self.settings = SimpleNamespace(personal_local_mode=True, member_credentials_enabled=True,
            quote_provider='member', authority_enabled=False, quote_max_age_seconds=180,
            shared_quote_tick_deadline_seconds=30, shared_quote_max_symbols_per_tick=20,
            terminal_events_path=Path(self.directory.name) / 'absent.jsonl')
        self.clock = dt.datetime(2026, 11, 2, 15, 0, tzinfo=dt.timezone.utc)
        self.spec = StrategySpec.model_validate({'name':'개인 검증', 'symbols':['AAA','BBB'],
            'factors':[{'kind':'momentum','lookback':2}],
            'filters':{'history_days':20,'min_average_volume':0},
            'portfolio':{'rebalance_days':1,'max_positions':1,'stop_loss_pct':None}})
        with self.sessions() as session:
            user = User(email='offline@example.test', display_name='Offline', password_hash='unused')
            session.add(user); session.flush()
            strategy = Strategy(user_id=user.id, name=self.spec.name, spec_json=self.spec.model_dump_json(), original_prompt='')
            session.add(strategy); session.flush()
            account = PaperAccount(user_id=user.id, strategy_id=strategy.id, name='Offline ledger', cash=100000,
                initial_cash=100000, created_at=dt.datetime(2026,10,30,tzinfo=dt.timezone.utc))
            session.add(account)
            session.add(MarketDataConnection(user_id=user.id, provider='kis', environment='paper',
                encrypted_api_key='synthetic', encrypted_api_secret='synthetic', key_hint='test', secret_hint='test'))
            session.commit()
            self.owner, self.account, self.strategy = user.id, account.id, strategy.id
        self.patchers = [patch('cloud_app.paper.get_settings', return_value=self.settings),
            patch('cloud_app.worker.get_settings', return_value=self.settings),
            patch('cloud_app.worker.SessionLocal', self.sessions),
            patch('cloud_app.paper.utcnow', side_effect=lambda:self.clock),
            patch('cloud_app.worker.utcnow', side_effect=lambda:self.clock),
            patch('cloud_app.personal_data.personal_data_status',return_value={'generation':'test','missing_action_symbols':[]})]
        for patcher in self.patchers:
            patcher.start()

    def tearDown(self):
        for patcher in reversed(self.patchers):
            patcher.stop()
        self.engine.dispose(); self.directory.cleanup()

    def quotes(self, session, names=('AAA','BBB'), offset=0):
        values = [paper.QuoteValue(name,100+offset,0,0,10,'kis_member',self.clock) for name in names]
        return paper.store_member_quotes(session, self.owner, values)

    def bundle(self):
        return SimpleNamespace(index=pd.DatetimeIndex([self.clock.date()-dt.timedelta(days=1)]), forward_data_gate_ready=False)

    def test_paper_allocation_reserves_cash_and_reweights_existing_positions(self):
        self.spec.portfolio.max_positions = 2
        self.spec.portfolio.investment_fraction = .6
        self.spec.portfolio.max_position_fraction = .3
        self.spec.portfolio.rebalance_weights = True
        self.spec.portfolio.cost_per_side = 0
        with self.sessions() as session:
            session.get(Strategy,self.strategy).spec_json = self.spec.model_dump_json()
            self.quotes(session); session.commit()
            with patch('cloud_app.paper.get_dataset_bundle',side_effect=self.bundle), patch('cloud_app.paper.latest_candidates',return_value=['AAA','BBB']):
                self.assertEqual(paper.rebalance_due_accounts(session),2)
                session.commit()
                self.assertAlmostEqual(session.get(PaperAccount,self.account).cash,40000)
                self.clock += dt.timedelta(days=1)
                paper.store_member_quotes(session,self.owner,[paper.QuoteValue('AAA',200,0,0,1,'kis_member',self.clock),paper.QuoteValue('BBB',100,0,0,1,'kis_member',self.clock)])
                session.commit()
                self.assertEqual(paper.rebalance_due_accounts(session),2)
                session.commit()
            positions={row.ticker:row.shares for row in session.scalars(select(PaperPosition)).all()}
            self.assertAlmostEqual(positions['AAA']*200,39000)
            self.assertAlmostEqual(positions['BBB']*100,39000)
            self.assertAlmostEqual(session.get(PaperAccount,self.account).cash,52000)

    def test_member_provider_never_uses_synthetic_dataset(self):
        with patch('cloud_app.paper.get_dataset_bundle', side_effect=AssertionError('no fallback')):
            self.assertEqual(paper.make_quote_provider(self.settings).fetch(['AAA']), [])

    def test_quote_validation_rejects_nonfinite_future_and_stale(self):
        with self.sessions() as session:
            invalid = [paper.QuoteValue('BAD', value,0,0,1,'kis_member',self.clock) for value in [math.nan,math.inf,-1]]
            invalid.append(paper.QuoteValue('FUTURE',100,0,0,1,'kis_member',self.clock+dt.timedelta(minutes=1)))
            self.assertEqual(paper.store_member_quotes(session,self.owner,invalid),0)
            self.quotes(session);session.commit()
            self.assertEqual(paper.quote_map(session,['AAA'],user_id=self.owner),{'AAA':100})
            self.clock += dt.timedelta(seconds=181)
            self.assertEqual(paper.quote_map(session,['AAA'],user_id=self.owner),{})

    def test_missing_target_quote_defers_entire_rebalance_and_then_recovers(self):
        with self.sessions() as session:
            self.quotes(session,['AAA']);session.commit()
            account = session.get(PaperAccount,self.account)
            with patch('cloud_app.paper.get_dataset_bundle',side_effect=self.bundle), patch('cloud_app.paper.latest_candidates',return_value=['AAA','BBB']):
                self.assertEqual(paper.rebalance_due_accounts(session),0)
                self.assertIsNone(account.last_rebalanced_on)
                self.assertEqual(account.cash,100000)
                self.quotes(session,['BBB']);session.flush()
                self.assertEqual(paper.rebalance_due_accounts(session),2)
                self.assertEqual(paper.rebalance_due_accounts(session),0)
            session.commit()
            self.assertEqual(len(session.scalars(select(PaperFill)).all()),2)

    def test_failed_mid_rebalance_rolls_back_cash_positions_and_fills(self):
        with self.sessions() as session:
            self.quotes(session);session.commit()
            actual_fill = paper._fill
            def fail_second(*args,**kwargs):
                if args[2]=='BBB':
                    raise RuntimeError('injected crash before commit')
                return actual_fill(*args,**kwargs)
            with patch('cloud_app.paper.get_dataset_bundle',side_effect=self.bundle), patch('cloud_app.paper.latest_candidates',return_value=['AAA','BBB']), patch('cloud_app.paper._fill',side_effect=fail_second):
                with self.assertRaises(RuntimeError):
                    paper.rebalance_due_accounts(session)
            session.rollback()
        with self.sessions() as restarted:
            self.assertEqual(restarted.get(PaperAccount,self.account).cash,100000)
            self.assertEqual(restarted.scalars(select(PaperFill)).all(),[])
            self.assertEqual(restarted.scalars(select(PaperPosition)).all(),[])

    def test_no_equity_point_fabricated_during_quote_outage(self):
        with self.sessions() as session:
            account=session.get(PaperAccount,self.account)
            paper._fill(session,account,'AAA','BUY',10,100,.003,'rebalance','initial')
            session.commit()
            self.assertEqual(paper.mark_and_stop_accounts(session),0)
            session.commit()
            self.assertEqual(session.scalars(select(EquityPoint)).all(),[])
            self.quotes(session);session.flush();paper.mark_and_stop_accounts(session);session.commit()
            self.assertEqual(len(session.scalars(select(EquityPoint)).all()),1)

    def test_personal_backtest_results_never_automatically_pruned(self):
        with self.sessions() as session:
            for number in range(55):
                session.add(BacktestJob(user_id=self.owner,strategy_id=self.strategy,status='completed',
                    start_date=dt.date(2025,1,1),end_date=dt.date(2025,12,1),bias_mode='exploratory',
                    finished_at=self.clock-dt.timedelta(days=100)))
            session.commit()
            worker._prune_backtest_results(session,self.owner,self.settings);session.commit()
            self.assertEqual(len(session.scalars(select(BacktestJob)).all()),55)

    def test_provider_outage_invalidates_even_recent_cached_quotes(self):
        with self.sessions() as session:
            self.quotes(session);session.commit()
            self.assertEqual(paper.quote_map(session,['AAA'],user_id=self.owner),{'AAA':100})
            with patch('cloud_app.worker._fetch_member_quotes',side_effect=TimeoutError('synthetic outage')):
                self.assertEqual(worker.collect_member_quotes(session,self.settings),(0,1))
            session.commit()
            self.assertEqual(paper.quote_map(session,['AAA'],user_id=self.owner),{})
            self.assertGreater(worker._member_retry_after[self.owner],0)
            worker._member_retry_after.pop(self.owner,None)

    def test_sandbox_rotation_covers_twenty_symbols_and_preserves_other_fresh_quotes(self):
        symbols=['A'+str(number) for number in range(20)]
        covered=[]
        def fetched(connection,settings,watchlist):
            covered.extend(watchlist)
            return self.owner,[paper.QuoteValue(ticker,100,0,0,1,'kis_member',self.clock) for ticker in watchlist]
        with patch('cloud_app.worker.collect_watchlist',return_value=set(symbols)), patch('cloud_app.worker._fetch_member_quotes',side_effect=fetched):
            for tick in range(4):
                with self.sessions() as session:
                    self.assertEqual(worker.collect_member_quotes(session,self.settings),(5,0))
                    session.commit()
                self.clock+=dt.timedelta(seconds=15)
        self.assertEqual(set(covered),set(symbols));self.assertEqual(len(covered),20)
        with self.sessions() as session:
            self.assertEqual(len(paper.quote_map(session,symbols,user_id=self.owner)),20)
        # A failed next slice invalidates only that attempted slice, preserving
        # the known-fresh observations for the remaining fifteen symbols.
        with self.sessions() as session, patch('cloud_app.worker.collect_watchlist',return_value=set(symbols)), patch('cloud_app.worker._fetch_member_quotes',side_effect=TimeoutError('outage')):
            self.assertEqual(worker.collect_member_quotes(session,self.settings),(0,1));session.commit()
            self.assertEqual(len(paper.quote_map(session,symbols,user_id=self.owner)),15)
        worker._member_retry_after.pop(self.owner,None)

    def test_stale_history_and_paused_accounts_never_trade(self):
        with self.sessions() as session:
            self.quotes(session);session.commit()
            with patch('cloud_app.paper.get_dataset_bundle',side_effect=self.bundle), patch('cloud_app.paper.latest_candidates',side_effect=ValueError('stale history')):
                self.assertEqual(paper.rebalance_due_accounts(session),0)
            session.commit()
            self.assertEqual(session.scalars(select(PaperFill)).all(),[])
            self.assertEqual(paper.account_snapshot(session,session.get(PaperAccount,self.account))['execution_status'],'waiting_history')
            session.get(PaperAccount,self.account).status='paused';session.commit()
            with patch('cloud_app.paper.get_dataset_bundle',side_effect=self.bundle), patch('cloud_app.paper.latest_candidates',return_value=['AAA']):
                self.assertEqual(paper.rebalance_due_accounts(session),0)
            self.assertEqual(session.scalars(select(PaperFill)).all(),[])

    def test_backtest_heartbeat_continues_during_long_computation(self):
        observed=[]
        original=worker.heartbeat
        def record(session,component,detail):
            observed.append((component,detail))
            return original(session,component,detail)
        with patch('cloud_app.worker.heartbeat',side_effect=record):
            with worker._backtest_liveness('synthetic-long-job',interval_seconds=.01):
                time.sleep(.07)
                self.assertGreaterEqual(len(observed),2)
            count=len(observed)
            time.sleep(.025)
            self.assertEqual(len(observed),count)
        with self.sessions() as session:
            self.assertIn('synthetic-long-job',session.get(RuntimeHeartbeat,'backtest-worker').detail)

    def test_tick_error_is_durable_and_next_tick_recovers(self):
        provider=paper.MemberOnlyQuoteProvider()
        with patch('cloud_app.worker.apply_personal_corporate_actions',side_effect=RuntimeError('synthetic failure')):
            worker.run_paper_tick(provider,self.settings)
        with self.sessions() as session:
            self.assertIn('error=RuntimeError',session.get(RuntimeHeartbeat,'paper-worker').detail)
        with patch('cloud_app.worker.regular_market_open',return_value=False), patch('cloud_app.worker.apply_personal_corporate_actions',return_value=0):
            worker.run_paper_tick(provider,self.settings)
        with self.sessions() as session:
            self.assertNotIn('error=',session.get(RuntimeHeartbeat,'paper-worker').detail)

    def test_known_dividend_gross_exdate_credit_is_exactly_once(self):
        self.clock=dt.datetime(2026,11,3,15,0,tzinfo=dt.timezone.utc)
        with self.sessions() as session:
            account=session.get(PaperAccount,self.account)
            paper._fill(session,account,'AAA','BUY',10,100,.003,'rebalance','initial')
            session.flush()
            session.scalar(select(PaperFill)).executed_at=dt.datetime(2026,11,2,15,tzinfo=dt.timezone.utc)
            session.commit(); before=account.cash
            events=[{'ticker':'AAA','date':'2026-11-03','split_ratio':0,'dividend':2}]
            with patch('cloud_app.personal_data.personal_corporate_actions',return_value=events):
                self.assertEqual(paper.apply_personal_corporate_actions(session,self.settings),1)
                self.assertEqual(paper.apply_personal_corporate_actions(session,self.settings),0)
            session.commit()
            self.assertEqual(account.cash,before+20)

    def test_seven_day_restart_outage_and_repeated_tick_harness(self):
        """Seven calendar days accelerated; includes five sessions and weekend."""
        provider=paper.MemberOnlyQuoteProvider()
        for day in range(7):
            self.clock=dt.datetime(2026,11,2+day,15,0,tzinfo=dt.timezone.utc)
            target=['AAA' if day%2==0 else 'BBB']
            def collect(session, settings):
                return self.quotes(session),0
            patches = [patch('cloud_app.worker.collect_member_quotes',side_effect=collect),
                patch('cloud_app.paper.get_dataset_bundle',side_effect=self.bundle),
                patch('cloud_app.paper.latest_candidates',return_value=target),
                patch('cloud_app.worker.apply_terminal_events',return_value={'settled':0,'review_accounts':0}),
                patch('cloud_app.worker.apply_personal_corporate_actions',return_value=0)]
            for item in patches:item.start()
            try:
                if day==2:
                    with patch('cloud_app.worker.collect_member_quotes',return_value=(0,1)):
                        worker.run_paper_tick(provider,self.settings)
                    with self.sessions() as session:
                        self.assertNotEqual(session.get(PaperAccount,self.account).last_rebalanced_on,self.clock.date())
                worker.run_paper_tick(provider,self.settings)
                with self.sessions() as session:
                    count=len(session.scalars(select(PaperFill)).all())
                    cash=session.get(PaperAccount,self.account).cash
                worker.run_paper_tick(provider,self.settings)
                # Dispose/open connections simulates process restart at committed boundary.
                self.engine.dispose()
                with self.sessions() as session:
                    self.assertEqual(len(session.scalars(select(PaperFill)).all()),count)
                    self.assertEqual(session.get(PaperAccount,self.account).cash,cash)
                    self.assertEqual(count,1+2*min(day,4))
            finally:
                for item in reversed(patches):item.stop()

    def test_known_split_is_exactly_once_and_preserves_cost_basis(self):
        self.clock=dt.datetime(2026,11,3,15,0,tzinfo=dt.timezone.utc)
        with self.sessions() as session:
            account=session.get(PaperAccount,self.account)
            paper._fill(session,account,'AAA','BUY',10,100,.003,'rebalance','initial')
            session.flush()
            fill=session.scalar(select(PaperFill));fill.executed_at=dt.datetime(2026,11,2,15,tzinfo=dt.timezone.utc)
            session.commit()
            events=[{'ticker':'AAA','date':'2026-11-03','split_ratio':2,'dividend':0}]
            with patch('cloud_app.personal_data.personal_corporate_actions',return_value=events):
                self.assertEqual(paper.apply_personal_corporate_actions(session,self.settings),1)
                self.assertEqual(paper.apply_personal_corporate_actions(session,self.settings),0)
            session.commit()
            position=session.scalar(select(PaperPosition))
            self.assertEqual(position.shares,20);self.assertEqual(position.avg_price,50)

    def test_delayed_split_then_dividend_uses_event_date_quantity(self):
        self.clock=dt.datetime(2026,11,5,15,0,tzinfo=dt.timezone.utc)
        with self.sessions() as session:
            account=session.get(PaperAccount,self.account)
            paper._fill(session,account,'AAA','BUY',10,100,.003,'rebalance','initial')
            session.flush();session.scalar(select(PaperFill)).executed_at=dt.datetime(2026,11,2,15,tzinfo=dt.timezone.utc)
            session.commit();before=account.cash
            events=[{'ticker':'AAA','date':'2026-11-03','split_ratio':2,'dividend':0},
                    {'ticker':'AAA','date':'2026-11-04','split_ratio':0,'dividend':1}]
            with patch('cloud_app.personal_data.personal_corporate_actions',return_value=events):
                self.assertEqual(paper.apply_personal_corporate_actions(session,self.settings),2)
                self.assertEqual(paper.apply_personal_corporate_actions(session,self.settings),0)
            self.assertEqual(session.scalar(select(PaperPosition)).shares,20)
            self.assertEqual(account.cash,before+20)

    def test_split_then_new_same_exdate_dividend_survives_sqlite_reload(self):
        self.clock=dt.datetime(2026,11,3,15,0,tzinfo=dt.timezone.utc)
        with self.sessions() as session:
            account=session.get(PaperAccount,self.account)
            paper._fill(session,account,'AAA','BUY',10,100,.003,'rebalance','initial')
            session.flush();session.scalar(select(PaperFill)).executed_at=dt.datetime(2026,11,2,15,tzinfo=dt.timezone.utc)
            session.commit();before=account.cash
            with patch('cloud_app.personal_data.personal_corporate_actions',return_value=[{'ticker':'AAA','date':'2026-11-03','split_ratio':2,'dividend':0}]):
                self.assertEqual(paper.apply_personal_corporate_actions(session,self.settings),1)
            session.commit()
        with self.sessions() as restarted:
            with patch('cloud_app.personal_data.personal_corporate_actions',return_value=[{'ticker':'AAA','date':'2026-11-03','split_ratio':2,'dividend':1}]):
                self.assertEqual(paper.apply_personal_corporate_actions(restarted,self.settings),1)
                self.assertEqual(paper.apply_personal_corporate_actions(restarted,self.settings),0)
            restarted.commit()
            self.assertEqual(restarted.get(PaperAccount,self.account).cash,before+20)
            self.assertEqual(restarted.scalar(select(PaperPosition)).shares,20)

    def test_stops_wait_for_held_symbol_action_check(self):
        with self.sessions() as session:
            account=session.get(PaperAccount,self.account)
            paper._fill(session,account,'AAA','BUY',10,100,.003,'rebalance','initial')
            self.quotes(session,['AAA'],offset=-50);session.commit()
            with patch('cloud_app.personal_data.personal_data_status',return_value={'generation':'test','missing_action_symbols':['AAA']}):
                self.assertEqual(paper.guard_personal_price_discontinuities(session,self.settings),0)
                self.assertEqual(paper.mark_and_stop_accounts(session),0)
                self.assertEqual(account.status,'active')
                self.assertEqual(session.scalar(select(PaperPosition)).last_price,100)
                self.assertEqual(paper.account_snapshot(session,account)['execution_status'],'waiting_history')

    def test_split_like_discontinuity_freezes_before_stop_or_rebalance(self):
        with self.sessions() as session:
            account=session.get(PaperAccount,self.account)
            paper._fill(session,account,'AAA','BUY',10,100,.003,'rebalance','initial')
            self.quotes(session,['AAA'],offset=-50);session.commit()
            self.assertEqual(paper.guard_personal_price_discontinuities(session,self.settings),1)
            self.assertEqual(account.status,'review_required')
            self.assertEqual(paper.mark_and_stop_accounts(session),0)
            self.assertEqual(session.scalar(select(PaperPosition)).shares,10)


class KisPersonalPacingTests(unittest.TestCase):
    def test_each_exchange_request_is_paced_for_sandbox_and_real(self):
        from cloud_app.kis_quotes import KisCredentials,KisQuoteClient
        from unittest.mock import MagicMock
        for sandbox,interval in [(True,.5),(False,.05)]:
            client=KisQuoteClient(KisCredentials('synthetic','synthetic',paper=sandbox))
            response=MagicMock();response.status_code=200
            client.session.get=MagicMock(return_value=response)
            elapsed=[100.0]
            def sleep(seconds): elapsed[0]+=seconds
            with patch.object(client,'_headers',return_value={}), patch('cloud_app.kis_quotes.time.monotonic',side_effect=lambda:elapsed[0]), patch('cloud_app.kis_quotes.time.sleep',side_effect=sleep) as sleeper, patch('cloud_app.kis_quotes.read_requests_json',return_value={'output':{'last':'100'}}):
                client._request_quote('AAA','NAS');client._request_quote('AAA','NYS');client._request_quote('AAA','AMS')
                self.assertEqual(sleeper.call_count,2)
                self.assertAlmostEqual(elapsed[0],100+interval*2)
            client.session.close()

    def test_pacing_respects_work_deadline(self):
        from cloud_app.kis_quotes import KisCredentials,KisQuoteClient,KisWorkBudgetExceeded
        client=KisQuoteClient(KisCredentials('synthetic','synthetic',paper=True),deadline_monotonic=100.2)
        client._next_quote_monotonic=100.5
        with patch('cloud_app.kis_quotes.time.monotonic',return_value=100), patch('cloud_app.kis_quotes.time.sleep') as sleeper:
            with self.assertRaises(KisWorkBudgetExceeded):client._pace_quote_request()
            sleeper.assert_not_called()
        client.session.close()


if __name__=='__main__':
    unittest.main()
