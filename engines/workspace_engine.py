"""IFIT V0.8.2 — Terminal Navigation & Workspace Engine.

Pure state/config helpers for the terminal shell. No market-data calls.
"""
from dataclasses import dataclass
from typing import Dict, List

WORKSPACES: Dict[str, Dict[str, object]] = {
    "Command Center": {
        "code": "HOME",
        "description": "Executive synchronized market snapshot",
        "subviews": ["Executive Overview", "Decision Matrix", "Evidence Ladder"],
    },
    "Markets": {
        "code": "MKT",
        "description": "Market state, breadth, volatility and futures",
        "subviews": ["Overview", "Breadth", "Volatility", "Futures", "Regime"],
    },
    "Equities": {
        "code": "EQ",
        "description": "Fundamentals, valuation, quality, growth and peers",
        "subviews": ["Overview", "Fundamentals", "Valuation", "Quality", "Growth", "Peers"],
    },
    "Screener": {
        "code": "SCR",
        "description": "Multi-factor equity, derivatives, market, order-flow and quant screening",
        "subviews": ["Equity", "Derivatives", "Market", "Order Flow", "Quant", "Decision Intelligence"],
    },
    "Cross-Asset": {"code": "XAS", "description": "Cross-Asset Intelligence and Regime Analysis", "subviews": ["Overview"]},
    "Global Markets": {"code": "GMI", "description": "Global Markets Intelligence and Cross-Market Regime Analysis", "subviews": ["Overview", "Global Equity", "Rates & FX", "Commodities", "Volatility"]},
    "Forex": {"code": "FX", "description": "Forex Intelligence, Currency Strength, Volatility and FX Derivatives", "subviews": ["Overview", "Intelligence", "Screener", "Derivatives", "Volatility", "Decision Intelligence"]},
    "Crypto": {"code": "CRP", "description": "Crypto Intelligence, Positioning, Derivatives, Flow and Volatility", "subviews": ["Overview", "Intelligence", "Screener", "Derivatives", "Volatility", "Decision Intelligence"]},
    "Mutual Funds": {"code": "MF", "description": "Mutual Fund Intelligence, Screening, Performance, Risk and Flows", "subviews": ["Overview", "Intelligence", "Screener", "Performance & Risk", "Flows", "Decision Intelligence"]},
    "Options": {
        "code": "OPT",
        "description": "Option chain, OI, volatility, Greeks, models and execution",
        "subviews": ["Option Chain", "Greeks", "Volatility", "OI & Gamma", "Heston", "Execution"],
    },
    "Charts": {
        "code": "CHT",
        "description": "Price, footprint, CVD, delta, POC and microstructure",
        "subviews": ["Candles", "Footprint", "CVD / Delta", "Profile", "Microstructure"],
    },
    "Portfolio": {
        "code": "PF",
        "description": "Holdings, Greeks, concentration, stress and portfolio risk",
        "subviews": ["Overview", "Greeks", "Risk", "Stress", "Correlation"],
    },
    "Risk Engine": {
        "code": "RISK",
        "description": "Cross-engine risk, drivers, stress and tail diagnostics",
        "subviews": ["Risk Overview", "Drivers", "Stress", "Tail Risk"],
    },
    "AI Intelligence": {
        "code": "AI",
        "description": "Grounded explanation and evidence workspace",
        "subviews": ["IFIT Command", "Explain", "Evidence", "Methodology"],
    },
    "Bonds / Fixed Income": {
        "code": "BOND",
        "description": "Indian fixed income, government securities, SDLs, corporate bonds, T-Bills, yield curve and bond intelligence",
        "subviews": [
            "Overview",
            "Bond Screener",
            "Yield Curve",
            "G-Secs",
            "SDLs",
            "Corporate Bonds",
            "T-Bills",
            "Intelligence",
        ],
    },
    "MCX / Commodities": {
        "code": "MCX",
        "description": "MCX commodities, momentum, positioning, volatility, term structure and roll intelligence",
        "subviews": [
            "Overview",
            "Commodities",
            "Momentum",
            "Positioning",
            "Volatility",
            "Term Structure",
            "Basis & Roll",
            "Intelligence",
        ],

   },

}

@dataclass(frozen=True)
class WorkspaceContext:
    module: str
    subview: str
    instrument: str
    timeframe: str
    data_mode: str
    snapshot_status: str


def workspace_names() -> List[str]:
    return list(WORKSPACES.keys())


def subviews_for(module: str) -> List[str]:
    item = WORKSPACES.get(module, WORKSPACES["Command Center"])
    return list(item["subviews"])


def workspace_code(module: str) -> str:
    return str(WORKSPACES.get(module, WORKSPACES["Command Center"])["code"])


def workspace_description(module: str) -> str:
    return str(WORKSPACES.get(module, WORKSPACES["Command Center"])["description"])


def build_context(module: str, subview: str, instrument: str, timeframe: str,
                  data_mode: str, snapshot_status: str) -> WorkspaceContext:
    if module not in WORKSPACES:
        module = "Command Center"
    allowed = subviews_for(module)
    if subview not in allowed:
        subview = allowed[0]
    return WorkspaceContext(module, subview, instrument, timeframe, data_mode, snapshot_status)


def context_payload(ctx: WorkspaceContext) -> dict:
    return {
        "module": ctx.module,
        "module_code": workspace_code(ctx.module),
        "subview": ctx.subview,
        "instrument": ctx.instrument,
        "timeframe": ctx.timeframe,
        "data_mode": ctx.data_mode,
        "snapshot_status": ctx.snapshot_status,
    }
