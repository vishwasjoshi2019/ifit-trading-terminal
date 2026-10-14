"""
IFIT Hedging Intelligence Engine
V0.1

Explainable portfolio hedge research engine.
No order placement. No external market-data calls.

Inputs are portfolio Greek exposures plus candidate hedge instruments.
The engine evaluates simple linear hedge combinations and ranks them by:
    - residual Delta/Gamma/Vega risk
    - hedge cost
    - hedge efficiency

All scores are normalized research diagnostics, not guarantees.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from itertools import product
from typing import Iterable, Optional

import numpy as np
import pandas as pd

from engines.hedging_optimizer_v02 import optimize_single_v02


@dataclass(frozen=True)
class HedgeConfig:
    delta_weight: float = 0.45
    gamma_weight: float = 0.25
    vega_weight: float = 0.20
    theta_weight: float = 0.10
    cost_weight: float = 0.20
    max_contracts: int = 10
    contract_step: int = 1


@dataclass(frozen=True)
class PortfolioExposure:
    delta: float
    gamma: float
    vega: float
    theta: float = 0.0

    def as_dict(self):
        return asdict(self)


def _safe_float(value, default=0.0) -> float:
    try:
        x = float(value)
        return x if np.isfinite(x) else default
    except Exception:
        return default


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, float(value)))


def exposure_magnitude(exposure: PortfolioExposure) -> float:
    """
    Normalized absolute portfolio exposure proxy.
    The scaling keeps the diagnostic stable for typical prototype values.
    """
    return float(
        np.sqrt(
            exposure.delta ** 2
            + 10.0 * exposure.gamma ** 2
            + 0.01 * exposure.vega ** 2
            + 0.01 * exposure.theta ** 2
        )
    )


def build_demo_hedge_universe() -> pd.DataFrame:
    """
    Deterministic prototype hedge candidates.

    Positive Greek values represent long exposure to the relevant Greek.
    Negative values represent short exposure.

    Cost is a normalized per-contract premium/cost proxy.
    """
    rows = [
        {
            "Instrument": "NIFTY FUTURES",
            "Type": "FUTURE",
            "Strike": np.nan,
            "Delta": 1.00,
            "Gamma": 0.00,
            "Vega": 0.00,
            "Theta": 0.00,
            "Cost": 1.00,
            "Liquidity Score": 96.0,
        },
        {
            "Instrument": "NIFTY ATM PUT",
            "Type": "PUT",
            "Strike": 25000,
            "Delta": -0.50,
            "Gamma": 0.018,
            "Vega": 14.0,
            "Theta": -8.0,
            "Cost": 7.00,
            "Liquidity Score": 92.0,
        },
        {
            "Instrument": "NIFTY OTM PUT",
            "Type": "PUT",
            "Strike": 24500,
            "Delta": -0.25,
            "Gamma": 0.012,
            "Vega": 10.0,
            "Theta": -5.0,
            "Cost": 4.00,
            "Liquidity Score": 88.0,
        },
        {
            "Instrument": "NIFTY DEEP ITM PUT",
            "Type": "PUT",
            "Strike": 25500,
            "Delta": -0.82,
            "Gamma": 0.010,
            "Vega": 8.0,
            "Theta": -4.0,
            "Cost": 10.00,
            "Liquidity Score": 94.0,
        },
        {
            "Instrument": "NIFTY OTM CALL",
            "Type": "CALL",
            "Strike": 25500,
            "Delta": 0.25,
            "Gamma": 0.012,
            "Vega": 10.0,
            "Theta": -5.0,
            "Cost": 4.00,
            "Liquidity Score": 87.0,
        },
        {
            "Instrument": "NIFTY ATM CALL",
            "Type": "CALL",
            "Strike": 25000,
            "Delta": 0.50,
            "Gamma": 0.018,
            "Vega": 14.0,
            "Theta": -8.0,
            "Cost": 7.00,
            "Liquidity Score": 91.0,
        },
        {
            "Instrument": "NIFTY SHORT ATM CALL",
            "Type": "SHORT CALL",
            "Strike": 25000,
            "Delta": -0.50,
            "Gamma": -0.018,
            "Vega": -14.0,
            "Theta": 8.0,
            "Cost": -7.00,
            "Liquidity Score": 90.0,
        },
        {
            "Instrument": "NIFTY SHORT ATM PUT",
            "Type": "SHORT PUT",
            "Strike": 25000,
            "Delta": 0.50,
            "Gamma": -0.018,
            "Vega": -14.0,
            "Theta": 8.0,
            "Cost": -7.00,
            "Liquidity Score": 90.0,
        },
    ]
    return pd.DataFrame(rows)


def _risk_distance(exposure: PortfolioExposure) -> float:
    """
    Weighted absolute Greek risk proxy.
    """
    return float(
        0.45 * abs(exposure.delta)
        + 25.0 * abs(exposure.gamma)
        + 0.20 * abs(exposure.vega)
        + 0.10 * abs(exposure.theta)
    )


def _apply_hedge(
    portfolio: PortfolioExposure,
    hedge: pd.Series,
    quantity: int,
) -> PortfolioExposure:
    return PortfolioExposure(
        delta=portfolio.delta + quantity * _safe_float(hedge["Delta"]),
        gamma=portfolio.gamma + quantity * _safe_float(hedge["Gamma"]),
        vega=portfolio.vega + quantity * _safe_float(hedge["Vega"]),
        theta=portfolio.theta + quantity * _safe_float(hedge["Theta"]),
    )


def _hedge_cost(hedge: pd.Series, quantity: int) -> float:
    return abs(quantity) * abs(_safe_float(hedge["Cost"]))


def _efficiency(
    before: float,
    after: float,
    cost: float,
    liquidity: float,
) -> float:
    if before <= 0:
        return 0.0

    improvement = max(0.0, (before - after) / before)
    cost_penalty = min(cost / max(before, 1.0), 1.0)
    liquidity_factor = _clamp(liquidity, 0.0, 100.0) / 100.0

    score = (
        100.0
        * improvement
        * (1.0 - 0.35 * cost_penalty)
        * (0.70 + 0.30 * liquidity_factor)
    )
    return round(_clamp(score), 2)
def _optimize_single_hedges_v023_adapter(
    portfolio: PortfolioExposure,
    hedge_universe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Run IFIT V0.2.3 adaptive single-hedge optimizer and
    convert its output into the legacy Hedging Intelligence
    dashboard schema.

    The combined hedge optimizer remains untouched.
    """

    portfolio_dict = {
        "Delta": portfolio.delta,
        "Gamma": portfolio.gamma,
        "Vega": portfolio.vega,
        "Theta": portfolio.theta,
    }

    v023 = optimize_single_v02(
        portfolio_dict,
        hedge_universe,
    )

    if v023 is None or v023.empty:
        return pd.DataFrame()

    rows = []

    for _, row in v023.iterrows():

        rows.append(
            {
                "Instrument": row.get(
                    "Instrument",
                    "",
                ),
                "Type": row.get(
                    "Type",
                    "",
                ),
                "Strike": row.get(
                    "Strike",
                    0.0,
                ),
                "Quantity": row.get(
                    "Quantity",
                    0,
                ),

                "Portfolio Delta": portfolio.delta,
                "Residual Delta": round(
                    _safe_float(
                        row.get(
                            "Delta",
                            0.0,
                        )
                    ),
                    4,
                ),

                "Portfolio Gamma": portfolio.gamma,
                "Residual Gamma": round(
                    _safe_float(
                        row.get(
                            "Gamma",
                            0.0,
                        )
                    ),
                    6,
                ),

                "Portfolio Vega": portfolio.vega,
                "Residual Vega": round(
                    _safe_float(
                        row.get(
                            "Vega",
                            0.0,
                        )
                    ),
                    4,
                ),

                "Portfolio Theta": portfolio.theta,
                "Residual Theta": round(
                    _safe_float(
                        row.get(
                            "Theta",
                            0.0,
                        )
                    ),
                    4,
                ),

                "Hedge Cost": round(
                    _safe_float(
                        row.get(
                            "Hedge Cost",
                            0.0,
                        )
                    ),
                    4,
                ),

                "Residual Risk": round(
                    _safe_float(
                        row.get(
                            "After Core Risk",
                            0.0,
                        )
                    ),
                    4,
                ),

                "Liquidity Score": round(
                    _safe_float(
                        row.get(
                            "Liquidity Score",
                            0.0,
                        )
                    ),
                    2,
                ),

                "Hedge Efficiency": round(
                    _safe_float(
                        row.get(
                            "V0.2 Score",
                            0.0,
                        )
                    ),
                    2,
                ),

                "Optimizer Score": round(
                    _safe_float(
                        row.get(
                            "V0.2 Score",
                            0.0,
                        )
                    ),
                    2,
                ),

                "V0.2 Status": row.get(
                    "Target Status",
                    "YELLOW",
                ),

                "V0.2 Failed Targets": row.get(
                    "Failed Targets",
                    "NONE",
                ),

                "Core Risk Reduction": round(
                    _safe_float(
                        row.get(
                            "Core Risk Reduction",
                            0.0,
                        )
                    ),
                    4,
                ),

                "Core Risk Reduction %": round(
                    _safe_float(
                        row.get(
                            "Core Risk Reduction %",
                            0.0,
                        )
                    ),
                    4,
                ),

                "Theta Deterioration": round(
                    _safe_float(
                        row.get(
                            "Theta Deterioration",
                            0.0,
                        )
                    ),
                    4,
                ),
            }
        )

    return pd.DataFrame(rows)

def optimize_single_hedges_v023(
    portfolio: PortfolioExposure,
    hedge_universe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Public V0.2.3 adaptive single-hedge entry point.

    Existing optimize_single_hedges() remains unchanged.
    """
    return _optimize_single_hedges_v023_adapter(
        portfolio,
        hedge_universe,
    )


def optimize_single_hedges(
    portfolio: PortfolioExposure,
    hedge_universe: pd.DataFrame,
    config: Optional[HedgeConfig] = None,
) -> pd.DataFrame:
    """
    Test each candidate instrument across a bounded quantity range.
    """
    config = config or HedgeConfig()
    before = _risk_distance(portfolio)

    rows = []

    for _, hedge in hedge_universe.iterrows():
        for qty in range(-config.max_contracts, config.max_contracts + 1):
            if qty == 0:
                continue

            after_exp = _apply_hedge(portfolio, hedge, qty)
            after = _risk_distance(after_exp)
            cost = _hedge_cost(hedge, qty)
            efficiency = _efficiency(
                before,
                after,
                cost,
                _safe_float(hedge.get("Liquidity Score", 0.0)),
            )

            rows.append(
                {
                    "Instrument": hedge["Instrument"],
                    "Type": hedge["Type"],
                    "Strike": hedge["Strike"],
                    "Quantity": qty,
                    "Portfolio Delta": portfolio.delta,
                    "Residual Delta": round(after_exp.delta, 4),
                    "Portfolio Gamma": portfolio.gamma,
                    "Residual Gamma": round(after_exp.gamma, 6),
                    "Portfolio Vega": portfolio.vega,
                    "Residual Vega": round(after_exp.vega, 4),
                    "Portfolio Theta": portfolio.theta,
                    "Residual Theta": round(after_exp.theta, 4),
                    "Hedge Cost": round(cost, 4),
                    "Residual Risk": round(after, 4),
                    "Liquidity Score": round(
                        _safe_float(hedge.get("Liquidity Score", 0.0)), 2
                    ),
                    "Hedge Efficiency": efficiency,
                }
            )

    result = pd.DataFrame(rows)

    if result.empty:
        return result

    # Prefer lower residual risk, then lower cost, then higher liquidity.
    result["Optimizer Score"] = (
        100.0
        - 60.0
        * (
            result["Residual Risk"]
            / max(before, 1.0)
        ).clip(upper=2.0)
        - 10.0
        * (
            result["Hedge Cost"]
            / max(before, 1.0)
        ).clip(upper=1.0)
        + 0.10 * result["Liquidity Score"]
    ).clip(0.0, 100.0).round(2)

    result = result.sort_values(
        ["Hedge Efficiency", "Optimizer Score", "Residual Risk"],
        ascending=[False, False, True],
    ).reset_index(drop=True)

    return result


def optimize_combined_hedges(
    portfolio: PortfolioExposure,
    hedge_universe: pd.DataFrame,
    config: Optional[HedgeConfig] = None,
    max_legs: int = 2,
) -> pd.DataFrame:
    """
    Search simple two-leg hedge combinations.

    The search is deliberately bounded for prototype speed and
    explainability. It is not a continuous portfolio optimizer.
    """
    config = config or HedgeConfig()
    before = _risk_distance(portfolio)

    candidates = hedge_universe.reset_index(drop=True)
    rows = []

    for i in range(len(candidates)):
        for j in range(i + 1, len(candidates)):
            h1 = candidates.iloc[i]
            h2 = candidates.iloc[j]

            for q1 in range(-config.max_contracts, config.max_contracts + 1):
                if q1 == 0:
                    continue

                for q2 in range(-config.max_contracts, config.max_contracts + 1):
                    if q2 == 0:
                        continue

                    after = PortfolioExposure(
                        delta=portfolio.delta
                        + q1 * _safe_float(h1["Delta"])
                        + q2 * _safe_float(h2["Delta"]),
                        gamma=portfolio.gamma
                        + q1 * _safe_float(h1["Gamma"])
                        + q2 * _safe_float(h2["Gamma"]),
                        vega=portfolio.vega
                        + q1 * _safe_float(h1["Vega"])
                        + q2 * _safe_float(h2["Vega"]),
                        theta=portfolio.theta
                        + q1 * _safe_float(h1["Theta"])
                        + q2 * _safe_float(h2["Theta"]),
                    )

                    residual = _risk_distance(after)
                    cost = _hedge_cost(h1, q1) + _hedge_cost(h2, q2)
                    liquidity = (
                        _safe_float(h1.get("Liquidity Score", 0.0))
                        + _safe_float(h2.get("Liquidity Score", 0.0))
                    ) / 2.0

                    efficiency = _efficiency(
                        before,
                        residual,
                        cost,
                        liquidity,
                    )

                    rows.append(
                        {
                            "Hedge 1": h1["Instrument"],
                            "Qty 1": q1,
                            "Hedge 2": h2["Instrument"],
                            "Qty 2": q2,
                            "Residual Delta": round(after.delta, 4),
                            "Residual Gamma": round(after.gamma, 6),
                            "Residual Vega": round(after.vega, 4),
                            "Residual Theta": round(after.theta, 4),
                            "Hedge Cost": round(cost, 4),
                            "Residual Risk": round(residual, 4),
                            "Liquidity Score": round(liquidity, 2),
                            "Hedge Efficiency": efficiency,
                        }
                    )

    result = pd.DataFrame(rows)

    if result.empty:
        return result

    result = result.sort_values(
        ["Hedge Efficiency", "Residual Risk", "Hedge Cost"],
        ascending=[False, True, True],
    ).reset_index(drop=True)

    return result


def hedge_summary(
    portfolio: PortfolioExposure,
    ranked: pd.DataFrame,
) -> dict:
    """
    Return compact dashboard metrics.
    """
    before = _risk_distance(portfolio)

    if ranked is None or ranked.empty:
        return {
            "Portfolio Risk Proxy": round(before, 4),
            "Best Hedge Efficiency": 0.0,
            "Best Residual Risk": round(before, 4),
            "Best Hedge Cost": 0.0,
            "Recommended Hedge": "No hedge candidate",
        }

    top = ranked.iloc[0]

    if "Instrument" in top.index:
        recommendation = f'{top["Instrument"]} × {int(top["Quantity"])}'
    else:
        recommendation = (
            f'{top["Hedge 1"]} × {int(top["Qty 1"])} + '
            f'{top["Hedge 2"]} × {int(top["Qty 2"])}'
        )

    return {
        "Portfolio Risk Proxy": round(before, 4),
        "Best Hedge Efficiency": round(
            _safe_float(top.get("Hedge Efficiency", 0.0)), 2
        ),
        "Best Residual Risk": round(
            _safe_float(top.get("Residual Risk", before)), 4
        ),
        "Best Hedge Cost": round(
            _safe_float(top.get("Hedge Cost", 0.0)), 4
        ),
        "Recommended Hedge": recommendation,
    }


def hedge_recommendation(
    portfolio: PortfolioExposure,
    ranked: pd.DataFrame,
) -> dict:
    """
    Explain the leading hedge candidate from the ranked results.
    """
    if ranked is None or ranked.empty:
        return {
            "direction": "NO HEDGE",
            "reason": "No valid hedge candidates were supplied.",
            "confidence": 0.0,
        }

    top = ranked.iloc[0]
    residual_delta = _safe_float(top.get("Residual Delta", 0.0))
    residual_gamma = _safe_float(top.get("Residual Gamma", 0.0))
    residual_vega = _safe_float(top.get("Residual Vega", 0.0))
    efficiency = _safe_float(top.get("Hedge Efficiency", 0.0))

    if abs(portfolio.delta) >= max(abs(portfolio.gamma) * 25.0, abs(portfolio.vega) * 0.20):
        primary = "DELTA"
    elif abs(portfolio.gamma) >= 0.50:
        primary = "GAMMA"
    elif abs(portfolio.vega) >= 10.0:
        primary = "VEGA"
    else:
        primary = "BALANCED GREEK RISK"

    return {
        "direction": primary,
        "reason": (
            f'Leading hedge: {top.get("Instrument", "combined hedge")} '
            f'with residual Delta {residual_delta:.3f}, '
            f'Gamma {residual_gamma:.5f}, Vega {residual_vega:.2f}.'
        ),
        "confidence": round(_clamp(efficiency), 2),
    }


def build_demo_hedging() -> dict:
    """
    Deterministic end-to-end demo for smoke testing.
    """
    portfolio = PortfolioExposure(
        delta=42.0,
        gamma=-0.65,
        vega=-18.0,
        theta=-7.0,
    )

    universe = build_demo_hedge_universe()

    single = optimize_single_hedges(portfolio, universe)
    combined = optimize_combined_hedges(
        portfolio,
        universe,
        config=HedgeConfig(max_contracts=4),
    )

    return {
        "portfolio": portfolio,
        "universe": universe,
        "single": single,
        "combined": combined,
        "summary": hedge_summary(portfolio, single),
        "recommendation": hedge_recommendation(portfolio, single),
    }


if __name__ == "__main__":
    demo = build_demo_hedging()

    print("HEDGING ENGINE QA")
    print("Portfolio:", demo["portfolio"].as_dict())
    print("Universe rows:", len(demo["universe"]))
    print("Single hedge rows:", len(demo["single"]))
    print("Combined hedge rows:", len(demo["combined"]))
    print("Summary:", demo["summary"])
    print("Recommendation:", demo["recommendation"])

    if not demo["single"].empty:
        print("\nTOP SINGLE HEDGE")
        print(
            demo["single"][
                [
                    "Instrument",
                    "Quantity",
                    "Residual Delta",
                    "Residual Gamma",
                    "Residual Vega",
                    "Hedge Cost",
                    "Hedge Efficiency",
                ]
            ].head(5).to_string(index=False)
        )

    if not demo["combined"].empty:
        print("\nTOP COMBINED HEDGE")
        print(
            demo["combined"][
                [
                    "Hedge 1",
                    "Qty 1",
                    "Hedge 2",
                    "Qty 2",
                    "Residual Delta",
                    "Residual Gamma",
                    "Residual Vega",
                    "Hedge Cost",
                    "Hedge Efficiency",
                ]
            ].head(5).to_string(index=False)
        )
