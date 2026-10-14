import pandas as pd


# ============================================================
# IFIT HEDGING INTELLIGENCE V0.2.1
#
# Objective hierarchy:
#   1. Reduce Core DGV Risk
#   2. Control residual Greeks
#   3. Control Theta deterioration
#   4. Control hedge cost
#   5. Prefer liquid instruments
#
# Production hedging_engine.py is NOT modified.
# ============================================================


# ------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------

DEFAULT_MAX_QUANTITY = 5

MAX_THETA_DETERIORATION = 150.0
MAX_COST_MULTIPLIER = 25.0

MAX_RESIDUAL_DELTA = 45.0
MAX_RESIDUAL_GAMMA = 0.80
MAX_RESIDUAL_VEGA = 30.0


# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# V0.2.1 GUARDRAILS
# ------------------------------------------------------------

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

    # 1. Core risk MUST decrease
    if after_core >= before_core:
        return False

    # 2. Residual Delta
    if abs(after["Delta"]) > MAX_RESIDUAL_DELTA:
        return False

    # 3. Residual Gamma
    if abs(after["Gamma"]) > MAX_RESIDUAL_GAMMA:
        return False

    # 4. Residual Vega
    if abs(after["Vega"]) > MAX_RESIDUAL_VEGA:
        return False

    # 5. Theta deterioration
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

    # 6. Cost guardrail
    cost = abs(quantity) * abs(
        _safe(hedge.get("Cost", 0.0))
    )

    max_cost = max(
        before_core * MAX_COST_MULTIPLIER,
        1.0,
    )

    if cost > max_cost:
        return False

    return True


# ------------------------------------------------------------
# SCORING
# ------------------------------------------------------------

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

    # Hard core-risk filter
    if core_reduction <= 0:
        return None

    # Guardrails
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
        / max(before_core, 0.000001)
    )

    core_component = (
        70.0
        * min(
            core_reduction_pct,
            1.0,
        )
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
    # THETA / CARRY
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

    theta_ratio = (
        theta_change
        / max(before_theta, 1.0)
    )

    theta_penalty = min(
        theta_ratio,
        1.0,
    )

    # --------------------------------------------------------
    # COST
    # --------------------------------------------------------

    cost = abs(quantity) * abs(
        _safe(
            hedge.get(
                "Cost",
                0.0,
            )
        )
    )

    cost_ratio = (
        cost
        / max(
            before_core * 25.0,
            1.0,
        )
    )

    cost_penalty = min(
        cost_ratio,
        1.0,
    )

    # --------------------------------------------------------
    # EXECUTION EFFICIENCY
    # --------------------------------------------------------

    efficiency = (
        1.0
        - 0.50 * theta_penalty
        - 0.50 * cost_penalty
    )

    efficiency = max(
        0.0,
        efficiency,
    )

    efficiency_component = (
        15.0
        * efficiency
    )

    # --------------------------------------------------------
    # FINAL SCORE
    # --------------------------------------------------------

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

        "Hedge Cost": cost,

        "Liquidity Score": liquidity,

        "Core Component": core_component,
        "Liquidity Component": liquidity_component,
        "Efficiency Component": efficiency_component,

        "V0.2 Score": score,
    }


# ------------------------------------------------------------
# SINGLE HEDGE OPTIMIZER
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# BEST SINGLE HEDGE
# ------------------------------------------------------------

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