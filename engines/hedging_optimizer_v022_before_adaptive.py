import pandas as pd


# ============================================================
# IFIT HEDGING INTELLIGENCE V0.2.2
#
# Objective hierarchy:
#   1. Reduce Core DGV Risk
#   2. Prefer better Theta / Carry
#   3. Prefer liquid instruments
#   4. Control hedge cost
#
# Score:
#   65% Core DGV Risk Reduction
#   15% Liquidity
#   10% Carry Quality
#   10% Cost Efficiency
#
# Production hedging_engine.py is NOT modified.
# ============================================================


DEFAULT_MAX_QUANTITY = 5

MAX_THETA_DETERIORATION = 150.0
MAX_COST_MULTIPLIER = 25.0

MAX_RESIDUAL_DELTA = 45.0
MAX_RESIDUAL_GAMMA = 0.80
MAX_RESIDUAL_VEGA = 30.0


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


def passes_guardrails(
    portfolio,
    hedge,
    quantity,
    before_core,
):
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

    # Core DGV risk MUST decrease.
    if after_core >= before_core:
        return False

    # Residual Delta.
    if abs(after["Delta"]) > MAX_RESIDUAL_DELTA:
        return False

    # Residual Gamma.
    if abs(after["Gamma"]) > MAX_RESIDUAL_GAMMA:
        return False

    # Residual Vega.
    if abs(after["Vega"]) > MAX_RESIDUAL_VEGA:
        return False

    # Theta deterioration hard ceiling.
    before_theta = abs(
        _safe(portfolio["Theta"])
    )

    after_theta = abs(
        after["Theta"]
    )

    theta_deterioration = max(
        0.0,
        after_theta - before_theta,
    )

    if theta_deterioration > MAX_THETA_DETERIORATION:
        return False

    # Cost hard ceiling.
    cost = abs(quantity) * abs(
        _safe(
            hedge.get(
                "Cost",
                0.0,
            )
        )
    )

    max_cost = max(
        before_core * MAX_COST_MULTIPLIER,
        1.0,
    )

    if cost > max_cost:
        return False

    return True


def score_hedge(
    portfolio,
    hedge,
    quantity,
):
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

    core_reduction = (
        before_core - after_core
    )

    if core_reduction <= 0:
        return None

    if not passes_guardrails(
        portfolio,
        hedge,
        quantity,
        before_core,
    ):
        return None

    # --------------------------------------------------------
    # CORE RISK REDUCTION
    # --------------------------------------------------------

    core_reduction_pct = (
        core_reduction
        / max(
            before_core,
            0.000001,
        )
    )

    core_quality = min(
        core_reduction_pct,
        1.0,
    )

    core_component = (
        65.0
        * core_quality
    )

    # --------------------------------------------------------
    # LIQUIDITY
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

    liquidity_component = (
        15.0
        * liquidity
        / 100.0
    )

    # --------------------------------------------------------
    # THETA / CARRY QUALITY
    #
    # 100 = no deterioration
    # 0   = maximum allowed deterioration
    # --------------------------------------------------------

    before_theta = abs(
        _safe(
            portfolio["Theta"]
        )
    )

    after_theta = abs(
        _safe(
            after["Theta"]
        )
    )

    theta_deterioration = max(
        0.0,
        after_theta - before_theta,
    )

    theta_quality = 1.0 - min(
        theta_deterioration
        / max(
            MAX_THETA_DETERIORATION,
            1.0,
        ),
        1.0,
    )

    carry_component = (
        10.0
        * theta_quality
    )

    # --------------------------------------------------------
    # COST EFFICIENCY
    # --------------------------------------------------------

    cost = abs(quantity) * abs(
        _safe(
            hedge.get(
                "Cost",
                0.0,
            )
        )
    )

    max_cost_reference = max(
        before_core * MAX_COST_MULTIPLIER,
        1.0,
    )

    cost_quality = 1.0 - min(
        cost
        / max_cost_reference,
        1.0,
    )

    cost_component = (
        10.0
        * cost_quality
    )

    # --------------------------------------------------------
    # FINAL V0.2.2 SCORE
    # --------------------------------------------------------

    score = (
        core_component
        + liquidity_component
        + carry_component
        + cost_component
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

        "Theta Deterioration": (
            theta_deterioration
        ),

        "Hedge Cost": cost,
        "Liquidity Score": liquidity,

        "Core Component": core_component,
        "Liquidity Component": liquidity_component,
        "Carry Component": carry_component,
        "Cost Component": cost_component,

        "V0.2 Score": score,
    }


def optimize_single_v02(
    portfolio,
    universe,
    max_quantity=DEFAULT_MAX_QUANTITY,
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

    result_df = pd.DataFrame(
        results
    )

    result_df = result_df.sort_values(
        [
            "V0.2 Score",
            "Core Risk Reduction",
            "Theta Deterioration",
            "Hedge Cost",
        ],
        ascending=[
            False,
            False,
            True,
            True,
        ],
    )

    return result_df.reset_index(
        drop=True
    )


def best_single_v02(
    portfolio,
    universe,
    max_quantity=DEFAULT_MAX_QUANTITY,
):
    results = optimize_single_v02(
        portfolio,
        universe,
        max_quantity=max_quantity,
    )

    if results.empty:
        return None

    return results.iloc[0].to_dict()