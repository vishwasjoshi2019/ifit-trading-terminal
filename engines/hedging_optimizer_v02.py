import pandas as pd


# ============================================================
# IFIT HEDGING INTELLIGENCE V0.2.3
#
# Adaptive Hedge Optimizer
#
# PRINCIPLES
# 1. Core DGV risk reduction is mandatory.
# 2. Residual Greeks are TARGETS, not hard blockers.
# 3. Theta and cost are penalties.
# 4. Liquidity is rewarded.
# 5. If constraints cannot all be satisfied, return the
#    best available PARTIAL hedge rather than falsely saying
#    no hedge exists.
#
# STATUS
#   GREEN = strong hedge
#   YELLOW = partial hedge
#   RED   = no effective hedge
#
# Production hedging_engine.py is NOT modified.
# ============================================================


DEFAULT_MAX_QUANTITY = 5

# Preferred residual targets.
TARGET_DELTA = 45.0
TARGET_GAMMA = 0.80
TARGET_VEGA = 30.0

# Hard safety limits.
MAX_THETA_DETERIORATION = 150.0
MAX_COST_MULTIPLIER = 25.0


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
# RESIDUAL TARGET QUALITY
# ------------------------------------------------------------

def _target_quality(value, target):
    """
    Returns:
        1.0 = target fully satisfied
        0.0 = residual is twice the target or worse
    """

    value = abs(_safe(value))
    target = max(_safe(target), 0.000001)

    quality = 1.0 - (
        max(0.0, value - target)
        / target
    )

    return max(
        0.0,
        min(
            1.0,
            quality,
        ),
    )


def _overall_residual_quality(after):
    delta_quality = _target_quality(
        after["Delta"],
        TARGET_DELTA,
    )

    gamma_quality = _target_quality(
        after["Gamma"],
        TARGET_GAMMA,
    )

    vega_quality = _target_quality(
        after["Vega"],
        TARGET_VEGA,
    )

    return (
        0.40 * delta_quality
        + 0.30 * gamma_quality
        + 0.30 * vega_quality
    )


def _target_status(after):
    delta_ok = (
        abs(after["Delta"])
        <= TARGET_DELTA
    )

    gamma_ok = (
        abs(after["Gamma"])
        <= TARGET_GAMMA
    )

    vega_ok = (
        abs(after["Vega"])
        <= TARGET_VEGA
    )

    count = sum(
        [
            delta_ok,
            gamma_ok,
            vega_ok,
        ]
    )

    if count == 3:
        return "GREEN"

    if count >= 1:
        return "YELLOW"

    return "RED"


def _failed_targets(after):
    failed = []

    if abs(after["Delta"]) > TARGET_DELTA:
        failed.append("DELTA")

    if abs(after["Gamma"]) > TARGET_GAMMA:
        failed.append("GAMMA")

    if abs(after["Vega"]) > TARGET_VEGA:
        failed.append("VEGA")

    return ", ".join(failed) if failed else "NONE"


# ------------------------------------------------------------
# SCORE
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
        before_core
        - after_core
    )

    # --------------------------------------------------------
    # MANDATORY:
    # Core DGV risk MUST decrease.
    # --------------------------------------------------------

    if core_reduction <= 0:
        return None

    # --------------------------------------------------------
    # THETA
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

    # Do not allow extreme carry damage.
    if (
        theta_deterioration
        > MAX_THETA_DETERIORATION
    ):
        return None

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

    max_cost = max(
        before_core
        * MAX_COST_MULTIPLIER,
        1.0,
    )

    if cost > max_cost:
        return None

    # --------------------------------------------------------
    # RESIDUAL QUALITY
    # --------------------------------------------------------

    residual_quality = (
        _overall_residual_quality(after)
    )

    target_status = _target_status(
        after
    )

    failed_targets = _failed_targets(
        after
    )

    # --------------------------------------------------------
    # CORE REDUCTION
    # --------------------------------------------------------

    core_reduction_pct = (
        core_reduction
        / max(
            before_core,
            0.000001,
        )
    )

    core_component = (
        55.0
        * min(
            core_reduction_pct,
            1.0,
        )
    )

    # --------------------------------------------------------
    # RESIDUAL GREEK QUALITY
    # --------------------------------------------------------

    residual_component = (
        20.0
        * residual_quality
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
        10.0
        * liquidity
        / 100.0
    )

    # --------------------------------------------------------
    # THETA QUALITY
    # --------------------------------------------------------

    theta_quality = 1.0 - min(
        theta_deterioration
        / max(
            MAX_THETA_DETERIORATION,
            1.0,
        ),
        1.0,
    )

    theta_component = (
        10.0
        * theta_quality
    )

    # --------------------------------------------------------
    # COST QUALITY
    # --------------------------------------------------------

    cost_quality = 1.0 - min(
        cost
        / max(
            max_cost,
            1.0,
        ),
        1.0,
    )

    cost_component = (
        5.0
        * cost_quality
    )

    # --------------------------------------------------------
    # FINAL SCORE
    # --------------------------------------------------------

    score = (
        core_component
        + residual_component
        + liquidity_component
        + theta_component
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
            core_reduction_pct
            * 100.0
        ),

        "Delta": after["Delta"],
        "Gamma": after["Gamma"],
        "Vega": after["Vega"],
        "Theta": after["Theta"],

        "Theta Deterioration": (
            theta_deterioration
        ),

        "Residual Quality": (
            residual_quality
        ),

        "Target Status": target_status,
        "Failed Targets": failed_targets,

        "Hedge Cost": cost,
        "Liquidity Score": liquidity,

        "Core Component": core_component,
        "Residual Component": (
            residual_component
        ),
        "Liquidity Component": (
            liquidity_component
        ),
        "Theta Component": theta_component,
        "Cost Component": cost_component,

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

    # Prefer:
    # 1. GREEN over YELLOW
    # 2. Higher score
    # 3. Greater core reduction
    # 4. Better residual quality
    # 5. Lower theta deterioration
    # 6. Lower cost

    result_df["_StatusRank"] = (
        result_df["Target Status"]
        .map(
            {
                "GREEN": 2,
                "YELLOW": 1,
                "RED": 0,
            }
        )
        .fillna(0)
    )

    result_df = result_df.sort_values(
        [
            "_StatusRank",
            "V0.2 Score",
            "Core Risk Reduction",
            "Residual Quality",
            "Theta Deterioration",
            "Hedge Cost",
        ],
        ascending=[
            False,
            False,
            False,
            False,
            True,
            True,
        ],
    )

    result_df = result_df.drop(
        columns=["_StatusRank"]
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