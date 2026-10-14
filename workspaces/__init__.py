"""IFIT Terminal Workspaces Package."""
from workspaces.command_center import render_command_center
from workspaces.markets import render_markets
from workspaces.equities import render_equities
from workspaces.screener import render_screener
from workspaces.options import render_options
from workspaces.charts import render_charts
from workspaces.portfolio import render_portfolio
from workspaces.risk_engine import render_risk_engine
from workspaces.ai_intelligence import render_ai_intelligence
from workspaces.bonds import render_bonds
from workspaces.commodities import render_commodities
from workspaces.cross_asset import render_cross_asset
from workspaces.forex import render_forex
from workspaces.crypto import render_crypto
from workspaces.global_markets import render_global_markets
from workspaces.mutual_funds import render_mutual_funds

__all__ = [
    "render_command_center",
    "render_markets",
    "render_equities",
    "render_screener",
    "render_options",
    "render_charts",
    "render_portfolio",
    "render_risk_engine",
    "render_ai_intelligence",
    "render_bonds",
    "render_commodities",
    "render_cross_asset",
    "render_forex",
    "render_crypto",
    "render_global_markets",
    "render_mutual_funds",
]
