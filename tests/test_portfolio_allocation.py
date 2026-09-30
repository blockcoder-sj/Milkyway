"""Shared allocation invariants and canonical-engine integration."""
import random
import unittest
import pandas as pd
from portfolio_allocation import plan_allocation
from backtest_core import run_backtest


class AllocationTests(unittest.TestCase):
    def apply(self, cash, holdings, prices, orders, cost):
        holdings=dict(holdings)
        for order in orders:
            amount=order.shares*prices[order.ticker]
            if order.side=='SELL':
                self.assertLessEqual(order.shares,holdings[order.ticker]+1e-8)
                holdings[order.ticker]-=order.shares
                cash+=amount*(1-cost)
            else:
                cash-=amount*(1+cost)
                holdings[order.ticker]=holdings.get(order.ticker,0)+order.shares
            self.assertGreaterEqual(cash,-1e-7)
        return cash,holdings

    def test_exposure_and_per_position_cap_leave_cash(self):
        args=dict(cash=100000,holdings={},prices={'A':100,'B':100},targets=['A','B'],investment_fraction=.8,max_position_fraction=.3,cost_per_side=.003)
        orders=plan_allocation(**args)
        cash,holdings=self.apply(args['cash'],{},args['prices'],orders,.003)
        self.assertAlmostEqual(holdings['A'],30000/1.003/100)
        self.assertAlmostEqual(cash,40000)

    def test_trim_and_top_up_retained_positions(self):
        args=dict(cash=0,holdings={'A':700,'B':300},prices={'A':100,'B':100},targets=['A','B'],rebalance_weights=True)
        orders=plan_allocation(**args)
        cash,positions=self.apply(0,args['holdings'],args['prices'],orders,0)
        self.assertEqual(cash,0)
        self.assertEqual(positions,{'A':500,'B':500})
        args['rebalance_weights']=False
        self.assertEqual(plan_allocation(**args),[])

    def test_replacing_targets_sells_removed_first(self):
        orders=plan_allocation(cash=0,holdings={'A':100},prices={'A':100,'B':100},targets=['B'],cost_per_side=.01)
        self.assertEqual([o.side for o in orders],['SELL','BUY'])
        cash,positions=self.apply(0,{'A':100},{'A':100,'B':100},orders,.01)
        self.assertAlmostEqual(cash,0)
        self.assertAlmostEqual(positions['B'],99/1.01)

    def test_empty_targets_liquidates(self):
        orders=plan_allocation(cash=0,holdings={'A':10},prices={'A':100},targets=[])
        self.assertEqual(len(orders),1)
        self.assertEqual(orders[0].side,'SELL')

    def test_finite_inputs_and_invalid_cost_rejected(self):
        for updates in ({'cash':float('nan')},{'cash':-1},{'investment_fraction':1.1},{'cost_per_side':1},{'prices':{'A':0}}):
            args=dict(cash=100,holdings={},prices={'A':10},targets=['A']);args.update(updates)
            with self.assertRaises(ValueError):plan_allocation(**args)

    def test_randomized_conservation_and_whole_share_bounds(self):
        rng=random.Random(730)
        for fractional in (True,False):
            for _ in range(250):
                prices={t:rng.uniform(5,500) for t in 'ABCD'}
                holdings={t:float(rng.randrange(100)) for t in 'ABC'}
                cash=rng.uniform(0,10000);cost=rng.uniform(0,.02)
                start=cash+sum(q*prices[t] for t,q in holdings.items())
                orders=plan_allocation(cash=cash,holdings=holdings,prices=prices,targets=['B','C','D'],cost_per_side=cost,investment_fraction=.7,max_position_fraction=.3,rebalance_weights=True,fractional=fractional)
                remaining,positions=self.apply(cash,holdings,prices,orders,cost)
                fees=sum(o.shares*prices[o.ticker]*cost for o in orders)
                self.assertAlmostEqual(remaining+sum(q*prices[t] for t,q in positions.items())+fees,start,places=7)
                if not fractional:self.assertTrue(all(o.shares==int(o.shares) for o in orders))

    def test_canonical_engine_applies_allocation_and_partial_rebalances(self):
        index=pd.bdate_range('2026-01-05',periods=4)
        prices=pd.DataFrame({'A':[100,100,200,200],'B':[100,100,100,100]},index=index)
        scores=pd.DataFrame({'A':[2]*4,'B':[1]*4},index=index)
        config=dict(capital=100000,max_positions=2,min_signal_count=2,cost_per_side=0,sector_cap_pct=1,
                    position_stop_pct=None,risk_free_rate=0,inertia_bonus=0,rebal_interval=1,rebalance_weights=True,investment_fraction=.6,max_position_fraction=.5)
        result=run_backtest(scores,prices,config=config,get_sector=lambda _: 'all')
        buys=[t for t in result['trade_log'] if t['side']=='BUY']
        self.assertEqual(buys[0]['gross'],30000)
        self.assertEqual(buys[1]['gross'],30000)
        self.assertTrue(any(t['reason']=='rebalance_weight' and t['side']=='SELL' for t in result['trade_log']))
        config['rebalance_weights']=False
        legacy=run_backtest(scores,prices,config=config,get_sector=lambda _: 'all')
        self.assertEqual(len(legacy['trade_log']),2)
