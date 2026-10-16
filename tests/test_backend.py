from __future__ import annotations

import asyncio
import json
import unittest

from backend.feed_interface import BaseMarketFeed
from backend.models import (
    NormalizedTick,
    OrderBookDepth,
    OptionChainSnapshot,
    OHLCVCandle,
    MarketSnapshot,
)
from backend.feeds.simulation_feed import SimulationFeed
from backend.feed_manager import feed_manager


class TestBackendStreaming(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await feed_manager.initialize()
        await feed_manager.start()

    async def asyncTearDown(self):
        await feed_manager.stop()

    async def test_simulation_feed_tick(self):
        tick = feed_manager.get_latest_tick("NIFTY")
        self.assertIsNotNone(tick)
        self.assertEqual(tick.symbol, "NIFTY")
        self.assertGreater(tick.ltp, 0)
        self.assertGreater(tick.bid, 0)
        self.assertGreater(tick.ask, 0)
        self.assertGreater(tick.ask, tick.bid)
        self.assertFalse(tick.is_live)
        self.assertEqual(tick.source, "SIMULATION")

    async def test_simulation_feed_depth(self):
        depth = feed_manager.get_depth("NIFTY")
        self.assertIsNotNone(depth)
        self.assertEqual(depth.symbol, "NIFTY")
        self.assertEqual(len(depth.levels), 5)
        self.assertGreater(depth.total_buy_qty, 0)
        self.assertGreater(depth.total_sell_qty, 0)
        self.assertGreater(depth.spread, 0)

    async def test_simulation_feed_option_chain(self):
        chain = feed_manager.get_option_chain("NIFTY")
        self.assertIsNotNone(chain)
        self.assertEqual(chain.underlying_symbol, "NIFTY")
        self.assertGreater(chain.underlying_price, 0)
        self.assertGreater(len(chain.strikes), 10)
        self.assertGreater(chain.pcr_oi, 0)
        self.assertGreater(chain.max_pain, 0)

    async def test_simulation_feed_candles(self):
        candles = feed_manager.get_candles("NIFTY", limit=50)
        self.assertIsInstance(candles, list)
        self.assertGreater(len(candles), 10)
        c0 = candles[-1]
        self.assertGreater(c0.open, 0)
        self.assertGreater(c0.high, 0)
        self.assertGreater(c0.low, 0)
        self.assertGreater(c0.close, 0)

    async def test_market_snapshot(self):
        snap = feed_manager.get_snapshot("NIFTY")
        self.assertIsInstance(snap, MarketSnapshot)
        self.assertEqual(snap.symbol, "NIFTY")
        self.assertIsNotNone(snap.tick)
        self.assertIsNotNone(snap.depth)
        self.assertGreater(len(snap.recent_candles), 0)

    async def test_provider_switching(self):
        providers = feed_manager.get_providers_info()
        self.assertEqual(providers["active_provider"], "SIMULATION")

        # Test switching to DHAN (even if not configured, should switch cleanly)
        switched = await feed_manager.switch_provider("DHAN")
        self.assertTrue(switched)
        self.assertEqual(feed_manager.active_provider_name, "DHAN")

        # Switch back to SIMULATION
        switched_back = await feed_manager.switch_provider("SIMULATION")
        self.assertTrue(switched_back)
        self.assertEqual(feed_manager.active_provider_name, "SIMULATION")

    async def test_quant_endpoints(self):
        from backend.server import (
            get_yield_curve,
            get_equity_screener,
            get_cross_asset,
            run_monte_carlo_simulation,
            get_options_greeks,
            MonteCarloRequest,
        )

        # Test Yield curve
        yc = await get_yield_curve()
        self.assertIsInstance(yc, list)
        self.assertGreater(len(yc), 5)

        # Test Screener
        scr = await get_equity_screener()
        self.assertIsInstance(scr, list)
        self.assertGreater(len(scr), 10)

        # Test Cross Asset
        ca = await get_cross_asset()
        self.assertIn("correlation", ca)
        self.assertIn("asset_table", ca)

        # Test Monte Carlo
        mc = await run_monte_carlo_simulation(MonteCarloRequest(spot=24800, days=10, paths=100))
        self.assertIn("var_95", mc)
        self.assertIn("p50", mc)

        # Test Options Greeks
        greeks = await get_options_greeks(spot=24800)
        self.assertIsInstance(greeks, list)
        self.assertGreater(len(greeks), 5)


    async def test_tick_listener_dispatch(self):
        received_ticks = []

        async def dummy_listener(tick: NormalizedTick):
            received_ticks.append(tick)

        sim_feed = feed_manager.providers["SIMULATION"]
        sim_feed.add_tick_listener(dummy_listener)

        # Wait for ticks to be emitted
        await asyncio.sleep(0.6)
        sim_feed.remove_tick_listener(dummy_listener)

        self.assertGreater(len(received_ticks), 0)
        self.assertIn(received_ticks[0].symbol, {"NIFTY", "BANKNIFTY", "FINNIFTY", "RELIANCE", "HDFCBANK", "TCS", "INFY"})


if __name__ == "__main__":
    unittest.main()
