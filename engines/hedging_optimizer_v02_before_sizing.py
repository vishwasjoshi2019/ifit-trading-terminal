import pandas as pd


# ============================================================
# IFIT HEDGING INTELLIGENCE V0.2
#
# Objective:
#   CORE RISK
#       Delta + Gamma + Vega
#
#   SECONDARY
#       Theta / Carry
#
#   EXECUTION
#       Cost + Liquidity
#
# HARD RULE:
#   Never recommend a hedge that increases core DGV risk.
#
# This file is standalone.
# Production hedging_engine.py is NOT modified.
# ============================================================


def _safe(value, default=0.0):
    try:
        value = float(value)
        if pd.isna(value):
            return default
        return value
    except Exception:
        return default


def core_risk(delta, gamma, vega):
    return (
        0.45 * abs(_safe(delta))
        + 25.0 * abs(_safe(gamma))
        + 0.20 * abs(_safe(vega))
    )


def apply_hedge(portfolio, hedge, quantity):
    return {
        "Delta": (
            _safe(portfolio["Delta"])
            + quantity * _safe(hedge["Delta"])
        ),
        "Gamma": (
            _safe(portfolio["Gamma"])
            + quantity * _safe(hedge["Gamma"])
        ),
        "Vega": (
            _safe(portfolio["Vega"])
            + quantity * _safe(hedge["Vega"])
        ),
        "Theta": (
            _safe(portfolio["Theta"])
            + quantity * _safe(hedge["Theta"])
        ),
    }


def score_hedge(portfolio, hedge, quantity):
    before_core = core_risk(
        portfolio["Delta"],
        portfolio["Gamma"],
        portfolio["Vega"],
    )

    after = apply_hedge(
        portfolio,
        hedge,
        quantity,
    )

    after_core = core_risk(
        after["Delta"],
        after["Gamma"],
        after["Vega"],
    )

    core_reduction = before_core - after_core

    # --------------------------------------------------------
    # HARD FILTER
    # --------------------------------------------------------

    if core_reduction <= 0:
        return None

    # --------------------------------------------------------
    # Core risk reduction percentage
    # --------------------------------------------------------

    core_reduction_pct = (
        core_reduction
        / max(before_core, 0.000001)
    )

    # --------------------------------------------------------
    # Theta / carry
    #
    # Theta is NOT core risk.
    # It is only a secondary penalty.
    # --------------------------------------------------------

    before_theta = abs(
        _safe(portfolio["Theta"])
    )

    after_theta = abs(
        _safe(after["Theta"])
    )

    theta_change = max(
        0.0,
        after_theta - before_theta,
    )

    # Normalize theta penalty.
    theta_ratio = theta_change / max(
        before_theta,
        1.0,
    )

    # Cap so theta can never overwhelm
    # genuine core-risk reduction.
    theta_penalty = min(
        theta_ratio,
        1.0,
    )

    # --------------------------------------------------------
    # Cost
    # --------------------------------------------------------

    cost = abs(quantity) * abs(
        _safe(hedge.get("Cost", 0.0))
    )

    # Normalize cost relative to a simple
    # core-risk monetary proxy.
    cost_ratio = cost / max(
        before_core * 10.0,
        1.0,
    )

    cost_penalty = min(
        cost_ratio,
        1.0,
    )

    # --------------------------------------------------------
    # Liquidity
    # --------------------------------------------------------

    liquidity = max(
        0.0,
        min(
            100.0,
            _safe(
                hedge.get(
                    "Liquidity Score",
                    0.0,
                )
            ),
        ),
    )

    liquidity_score = liquidity / 100.0

    # --------------------------------------------------------
    # V0.2 SCORE
    #
    # 70% = core risk reduction
    # 15% = liquidity
    # 15% = cost + carry efficiency
    #
    # Core reduction dominates.
    # --------------------------------------------------------

    core_component = (
        70.0
        * min(
            core_reduction_pct,
            1.0,
        )
    )

    liquidity_component = (
        15.0
        * liquidity_score
    )

    efficiency_component = (
        15.0
        * (
            1.0
            - 0.50 * theta_penalty
            - 0.50 * cost_penalty
        )
    )

    score = (
        core_component
        + liquidity_component
        + efficiency_component
    )

    score = max(
        0.0,
        min(
            100.0,
            score,
        ),
    )

    return {
        "Instrument": hedge.get(
            "Instrument",
            "",
        ),
        "Type": hedge.get(
            "Type",
            "",
        ),
        "Strike": _safe(
            hedge.get(
                "Strike",
                0.0,
            )
        ),
        "Quantity": int(quantity),

        "Before Core Risk": before_core,
        "After Core Risk": after_core,
        "Core Risk Reduction": core_reduction,

        "Core Risk Reduction %": (
            core_reduction_pct * 100.0
        ),

        "Delta": after["Delta"],
        "Gamma": after["Gamma"],
        "Vega": after["Vega"],
        "Theta": after["Theta"],

        "Theta Change": theta_change,
        "Theta Penalty": theta_penalty,

        "Hedge Cost": cost,
        "Cost Penalty": cost_penalty,

        "Liquidity Score": liquidity,

        "Core Component": core_component,
        "Liquidity Component": liquidity_component,
        "Efficiency Component": efficiency_component,

        "V0.2 Score": score,
    }


def optimize_single_v02(
    portfolio,
    universe,
    max_quantity=10,
):
    results = []

    if universe is None or len(universe) == 0:
        return pd.DataFrame()

    for _, hedge in universe.iterrows():

        for quantity in range(
            -max_quantity,
            max_quantity + 1,
        ):

            if quantity == 0:
                continue

            result = score_hedge(
                portfolio,
                hedge,
                quantity,
            )

            if result is not None:
                results.append(result)

    if not results:
        return pd.DataFrame()

    result_df = pd.DataFrame(results)

    result_df = result_df.sort_values(
        [
            "V0.2 Score",
            "Core Risk Reduction",
            "Liquidity Score",
            "Hedge Cost",
        ],
        ascending=[
            False,
            False,
            False,
            True,
        ],
    )

    return result_df.reset_index(
        drop=True
    )


def best_single_v02(
    portfolio,
    universe,
    max_quantity=10,
):
    results = optimize_single_v02(
        portfolio,
        universe,
        max_quantity=max_quantity,
    )

    if results.empty:
        return None

    return results.iloc[0].to_dict()