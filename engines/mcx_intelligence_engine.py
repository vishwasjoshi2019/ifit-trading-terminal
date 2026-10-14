"""
IFIT — MCX / Commodities Intelligence Engine V0.2

Simulation-first intelligence layer for MCX commodities.

Outputs:
- IV vs Realized Volatility
- Volatility Regime
- Price/OI Positioning
- Term Structure Signal
- Basis Signal
- Roll Signal
- Liquidity Regime
- Cross-Asset Score
- MCX Intelligence Score
- Intelligence Signal
- Actionable Thesis
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Optional

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------

@dataclass
class MCXIntelligenceConfig:
    seed: int = 8617
    market_name: str = "MCX"


# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------

def _clamp(value: float, low: float, high: float) -> float:
    return float(max(low, min(high, value)))


def _round(value: float, digits: int = 2) -> float:
    return round(float(value), digits)


def _safe_mean(series: pd.Series, default: float = 0.0) -> float:
    if series is None or len(series) == 0:
        return float(default)

    value = pd.to_numeric(series, errors="coerce").mean()

    if pd.isna(value):
        return float(default)

    return float(value)


def _signal(score: float) -> str:
    if score >= 72:
        return "STRONG BULLISH"
    if score >= 62:
        return "BULLISH"
    if score <= 28:
        return "STRONG BEARISH"
    if score <= 38:
        return "BEARISH"
    return "NEUTRAL"


def _volatility_regime(iv: float, rv: float, percentile: float) -> str:
    spread = iv - rv

    if percentile >= 80 and spread >= 5:
        return "HIGH / PREMIUM"
    if percentile >= 65:
        return "ELEVATED"
    if percentile <= 25 and spread <= 0:
        return "LOW / CHEAP"
    if percentile <= 40:
        return "COMPRESSED"

    return "NORMAL"


def _positioning(price_change: float, oi_change: float) -> str:
    """
    Classical price/OI interpretation:

    Price ↑ + OI ↑ = Long Build-up
    Price ↓ + OI ↑ = Short Build-up
    Price ↑ + OI ↓ = Short Covering
    Price ↓ + OI ↓ = Long Unwinding
    """

    if price_change > 0.40 and oi_change > 1.00:
        return "LONG BUILD-UP"

    if price_change < -0.40 and oi_change > 1.00:
        return "SHORT BUILD-UP"

    if price_change > 0.40 and oi_change < -1.00:
        return "SHORT COVERING"

    if price_change < -0.40 and oi_change < -1.00:
        return "LONG UNWINDING"

    return "MIXED"


def _positioning_score(positioning: str) -> float:
    mapping = {
        "LONG BUILD-UP": 90.0,
        "SHORT COVERING": 78.0,
        "MIXED": 50.0,
        "LONG UNWINDING": 25.0,
        "SHORT BUILD-UP": 10.0,
    }

    return mapping.get(positioning, 50.0)


def _term_structure_score(term_structure: str) -> float:
    mapping = {
        "CONTANGO": 48.0,
        "MILD CONTANGO": 45.0,
        "FLAT": 55.0,
        "MILD BACKWARDATION": 72.0,
        "BACKWARDATION": 85.0,
    }

    return mapping.get(term_structure, 50.0)


def _basis_score(basis: float) -> float:
    """
    Positive basis is treated as supportive only within a reasonable range.
    Extreme basis is treated as a warning rather than blindly bullish.
    """

    if basis >= 2.0:
        return 62.0

    if basis >= 1.0:
        return 70.0

    if basis >= 0.25:
        return 64.0

    if basis > -0.25:
        return 55.0

    if basis > -1.0:
        return 42.0

    return 32.0


def _roll_score(roll_behaviour: str) -> float:
    mapping = {
        "POSITIVE ROLL": 72.0,
        "NEUTRAL ROLL": 55.0,
        "NEGATIVE ROLL": 35.0,
        "ROLL RISK": 25.0,
    }

    return mapping.get(roll_behaviour, 50.0)


def _liquidity_regime(volume_ratio: float, liquidity_score: float) -> str:
    if liquidity_score >= 75 and volume_ratio >= 1.25:
        return "HIGH LIQUIDITY"

    if liquidity_score >= 60:
        return "HEALTHY"

    if liquidity_score >= 40:
        return "NORMAL"

    return "THIN"


def _term_structure_signal(term_structure_score: float) -> str:
    if term_structure_score >= 70:
        return "SUPPORTIVE"
    if term_structure_score <= 40:
        return "NEGATIVE"
    return "NEUTRAL"


def _basis_signal(basis_score: float) -> str:
    if basis_score >= 65:
        return "SUPPORTIVE"
    if basis_score <= 40:
        return "NEGATIVE"
    return "NEUTRAL"


def _roll_signal(roll_score: float) -> str:
    if roll_score >= 65:
        return "SUPPORTIVE"
    if roll_score <= 40:
        return "NEGATIVE"
    return "NEUTRAL"


def _thesis(row: pd.Series) -> str:
    score = float(row["MCX Intelligence Score"])
    positioning = str(row["Positioning"])
    vol_regime = str(row["Volatility Regime"])
    term_signal = str(row["Term Structure Signal"])
    basis_signal = str(row["Basis Signal"])
    roll_signal = str(row["Roll Signal"])

    if score >= 72:
        direction = "Strong bullish setup"
    elif score >= 62:
        direction = "Bullish setup"
    elif score <= 28:
        direction = "Strong bearish setup"
    elif score <= 38:
        direction = "Bearish setup"
    else:
        direction = "Balanced setup"

    return (
        f"{direction}: {positioning.lower()}, "
        f"{vol_regime.lower()} volatility, "
        f"{term_signal.lower()} term structure, "
        f"{basis_signal.lower()} basis and "
        f"{roll_signal.lower()} roll."
    )


# ---------------------------------------------------------------------
# BASE INTELLIGENCE
# ---------------------------------------------------------------------

def build_mcx_intelligence(
    commodities: Optional[Iterable[str]] = None,
    seed: int = 8617,
) -> pd.DataFrame:
    """
    Build deterministic simulation data for the MCX intelligence layer.

    This function intentionally does not connect to a live market feed.
    """

    rng = np.random.default_rng(seed)

    metadata: Dict[str, Dict[str, float]] = {
        "GOLD": {
            "iv": 18.5,
            "rv": 16.2,
            "volume_ratio": 1.18,
            "liquidity": 86,
        },
        "SILVER": {
            "iv": 29.0,
            "rv": 25.1,
            "volume_ratio": 1.34,
            "liquidity": 80,
        },
        "CRUDE OIL": {
            "iv": 34.5,
            "rv": 31.2,
            "volume_ratio": 1.42,
            "liquidity": 88,
        },
        "NATURAL GAS": {
            "iv": 51.5,
            "rv": 47.8,
            "volume_ratio": 1.63,
            "liquidity": 71,
        },
        "COPPER": {
            "iv": 25.0,
            "rv": 22.7,
            "volume_ratio": 1.21,
            "liquidity": 82,
        },
        "ALUMINIUM": {
            "iv": 22.0,
            "rv": 20.4,
            "volume_ratio": 1.12,
            "liquidity": 76,
        },
        "ZINC": {
            "iv": 27.5,
            "rv": 24.8,
            "volume_ratio": 1.27,
            "liquidity": 74,
        },
        "LEAD": {
            "iv": 28.5,
            "rv": 26.3,
            "volume_ratio": 1.31,
            "liquidity": 69,
        },
        "NICKEL": {
            "iv": 38.0,
            "rv": 34.7,
            "volume_ratio": 1.48,
            "liquidity": 65,
        },
    }

    all_commodities = list(metadata.keys())

    if commodities:
        requested = [str(x).upper() for x in commodities]
        universe = [x for x in all_commodities if x in requested]
    else:
        universe = all_commodities

    rows = []

    for commodity in universe:
        meta = metadata[commodity]

        price_change = float(
            rng.normal(
                {
                    "GOLD": 0.85,
                    "SILVER": 1.40,
                    "CRUDE OIL": 0.60,
                    "NATURAL GAS": -0.90,
                    "COPPER": 1.10,
                    "ALUMINIUM": 0.55,
                    "ZINC": 1.00,
                    "LEAD": 1.25,
                    "NICKEL": -0.35,
                }[commodity],
                0.95,
            )
        )

        oi_change = float(
            rng.normal(
                {
                    "GOLD": 2.4,
                    "SILVER": 3.2,
                    "CRUDE OIL": 1.8,
                    "NATURAL GAS": 4.0,
                    "COPPER": 2.6,
                    "ALUMINIUM": 1.5,
                    "ZINC": 2.7,
                    "LEAD": 3.0,
                    "NICKEL": -1.0,
                }[commodity],
                1.35,
            )
        )

        iv = max(5.0, meta["iv"] + rng.normal(0, 1.1))
        rv = max(4.0, meta["rv"] + rng.normal(0, 1.0))

        volatility_percentile = _clamp(
            50
            + (iv - rv) * 5
            + rng.normal(0, 5),
            5,
            98,
        )

        momentum_1m = (
            price_change * 2.25
            + rng.normal(1.0, 2.2)
        )

        volume_ratio = max(
            0.55,
            meta["volume_ratio"] + rng.normal(0, 0.08),
        )

        liquidity_score = _clamp(
            meta["liquidity"] + rng.normal(0, 3.5),
            20,
            100,
        )

        basis = float(
            rng.normal(
                {
                    "GOLD": 0.55,
                    "SILVER": 0.80,
                    "CRUDE OIL": 1.20,
                    "NATURAL GAS": -0.85,
                    "COPPER": 0.40,
                    "ALUMINIUM": 0.15,
                    "ZINC": 0.60,
                    "LEAD": 0.35,
                    "NICKEL": -0.40,
                }[commodity],
                0.45,
            )
        )

        term_structure = (
            "BACKWARDATION"
            if basis > 0.75
            else "MILD BACKWARDATION"
            if basis > 0.20
            else "FLAT"
            if basis >= -0.20
            else "MILD CONTANGO"
            if basis >= -0.75
            else "CONTANGO"
        )

        roll_behaviour = (
            "POSITIVE ROLL"
            if basis > 0.75
            else "NEUTRAL ROLL"
            if basis >= -0.20
            else "NEGATIVE ROLL"
        )

        positioning = _positioning(
            price_change,
            oi_change,
        )

        positioning_score = _positioning_score(positioning)

        vol_edge = iv - rv

        volatility_score = _clamp(
            55
            + vol_edge * 2
            - max(volatility_percentile - 70, 0) * 0.35,
            10,
            95,
        )

        momentum_score = _clamp(
            50 + momentum_1m * 3.0,
            10,
            95,
        )

        term_score = _term_structure_score(term_structure)
        basis_score = _basis_score(basis)
        roll_score = _roll_score(roll_behaviour)

        liquidity_regime = _liquidity_regime(
            volume_ratio,
            liquidity_score,
        )

        # Cross-asset component:
        # momentum + positioning + liquidity + volatility structure
        cross_asset_score = _clamp(
            momentum_score * 0.30
            + positioning_score * 0.30
            + term_score * 0.15
            + basis_score * 0.10
            + roll_score * 0.05
            + liquidity_score * 0.10,
            0,
            100,
        )

        intelligence_score = _clamp(
            momentum_score * 0.20
            + positioning_score * 0.20
            + volatility_score * 0.15
            + term_score * 0.12
            + basis_score * 0.10
            + roll_score * 0.08
            + liquidity_score * 0.07
            + cross_asset_score * 0.08,
            0,
            100,
        )

        signal = _signal(intelligence_score)

        rows.append(
            {
                "Market": "MCX",
                "Commodity": commodity,
                "Price Change %": _round(price_change),
                "Volume Ratio": _round(volume_ratio),
                "OI Change %": _round(oi_change),
                "IV %": _round(iv),
                "RV %": _round(rv),
                "IV-RV Spread %": _round(vol_edge),
                "Volatility Percentile": _round(
                    volatility_percentile
                ),
                "Volatility Regime": _volatility_regime(
                    iv,
                    rv,
                    volatility_percentile,
                ),
                "Positioning": positioning,
                "Positioning Score": _round(
                    positioning_score
                ),
                "Momentum 1M %": _round(momentum_1m),
                "Momentum Score": _round(momentum_score),
                "Term Structure": term_structure,
                "Term Structure Score": _round(term_score),
                "Term Structure Signal": _term_structure_signal(
                    term_score
                ),
                "Basis %": _round(basis),
                "Basis Score": _round(basis_score),
                "Basis Signal": _basis_signal(
                    basis_score
                ),
                "Roll Behaviour": roll_behaviour,
                "Roll Score": _round(roll_score),
                "Roll Signal": _roll_signal(
                    roll_score
                ),
                "Liquidity Score": _round(
                    liquidity_score
                ),
                "Liquidity Regime": liquidity_regime,
                "Cross-Asset Score": _round(
                    cross_asset_score
                ),
                "MCX Intelligence Score": _round(
                    intelligence_score
                ),
                "Signal": signal,
            }
        )

    df = pd.DataFrame(rows)

    if not df.empty:
        df["Thesis"] = df.apply(
            _thesis,
            axis=1,
        )

    return df


# ---------------------------------------------------------------------
# FILTERS
# ---------------------------------------------------------------------

def apply_mcx_intelligence_filters(
    df: pd.DataFrame,
    commodities=None,
    signals=None,
    positioning=None,
    volatility_regimes=None,
    term_structures=None,
    roll_behaviours=None,
    min_score: float = 0.0,
    min_momentum: float = -999.0,
    min_liquidity: float = 0.0,
    min_oi_change: float = -999.0,
    max_oi_change: float = 999.0,
) -> pd.DataFrame:

    if df is None or df.empty:
        return pd.DataFrame()

    out = df.copy()

    if commodities:
        selected = {str(x).upper() for x in commodities}
        out = out[
            out["Commodity"].str.upper().isin(selected)
        ]

    if signals:
        selected = {str(x).upper() for x in signals}
        out = out[
            out["Signal"].str.upper().isin(selected)
        ]

    if positioning:
        selected = {
            str(x).upper()
            for x in positioning
        }
        out = out[
            out["Positioning"].str.upper().isin(
                selected
            )
        ]

    if volatility_regimes:
        selected = {
            str(x).upper()
            for x in volatility_regimes
        }
        out = out[
            out["Volatility Regime"]
            .str.upper()
            .isin(selected)
        ]

    if term_structures:
        selected = {
            str(x).upper()
            for x in term_structures
        }
        out = out[
            out["Term Structure"]
            .str.upper()
            .isin(selected)
        ]

    if roll_behaviours:
        selected = {
            str(x).upper()
            for x in roll_behaviours
        }
        out = out[
            out["Roll Behaviour"]
            .str.upper()
            .isin(selected)
        ]

    out = out[
        out["MCX Intelligence Score"] >= float(min_score)
    ]

    out = out[
        out["Momentum 1M %"] >= float(min_momentum)
    ]

    out = out[
        out["Liquidity Score"] >= float(min_liquidity)
    ]

    out = out[
        (out["OI Change %"] >= float(min_oi_change))
        & (out["OI Change %"] <= float(max_oi_change))
    ]

    return out.reset_index(drop=True)


# ---------------------------------------------------------------------
# RANKING
# ---------------------------------------------------------------------

def rank_mcx_intelligence(
    df: pd.DataFrame,
    ascending: bool = False,
) -> pd.DataFrame:

    if df is None or df.empty:
        return pd.DataFrame()

    out = df.copy()

    out = out.sort_values(
        by=[
            "MCX Intelligence Score",
            "Cross-Asset Score",
            "Momentum Score",
        ],
        ascending=[
            ascending,
            ascending,
            ascending,
        ],
        kind="mergesort",
    ).reset_index(drop=True)

    out.insert(
        0,
        "Rank",
        np.arange(1, len(out) + 1),
    )

    return out


# ---------------------------------------------------------------------
# SUMMARY
# ---------------------------------------------------------------------

def mcx_intelligence_summary(
    df: pd.DataFrame,
) -> Dict[str, object]:

    if df is None or df.empty:
        return {
            "Commodities": 0,
            "Strong Bullish": 0,
            "Bullish": 0,
            "Neutral": 0,
            "Bearish": 0,
            "Strong Bearish": 0,
            "Average Intelligence Score": 0.0,
            "Average IV": 0.0,
            "Average RV": 0.0,
            "Average IV-RV Spread": 0.0,
            "Average Momentum": 0.0,
            "Average OI Change": 0.0,
            "Average Liquidity": 0.0,
            "Signal": "NEUTRAL",
        }

    signals = (
        df["Signal"]
        .astype(str)
        .str.upper()
    )

    avg_score = _safe_mean(
        df["MCX Intelligence Score"]
    )

    summary_signal = _signal(avg_score)

    return {
        "Commodities": int(len(df)),
        "Strong Bullish": int(
            (signals == "STRONG BULLISH").sum()
        ),
        "Bullish": int(
            (signals == "BULLISH").sum()
        ),
        "Neutral": int(
            (signals == "NEUTRAL").sum()
        ),
        "Bearish": int(
            (signals == "BEARISH").sum()
        ),
        "Strong Bearish": int(
            (signals == "STRONG BEARISH").sum()
        ),
        "Average Intelligence Score": _round(
            avg_score
        ),
        "Average IV": _round(
            _safe_mean(df["IV %"])
        ),
        "Average RV": _round(
            _safe_mean(df["RV %"])
        ),
        "Average IV-RV Spread": _round(
            _safe_mean(df["IV-RV Spread %"])
        ),
        "Average Momentum": _round(
            _safe_mean(df["Momentum 1M %"])
        ),
        "Average OI Change": _round(
            _safe_mean(df["OI Change %"])
        ),
        "Average Liquidity": _round(
            _safe_mean(df["Liquidity Score"])
        ),
        "Signal": summary_signal,
    }


# ---------------------------------------------------------------------
# LOOKUPS
# ---------------------------------------------------------------------

def available_mcx_intelligence_commodities():
    return [
        "GOLD",
        "SILVER",
        "CRUDE OIL",
        "NATURAL GAS",
        "COPPER",
        "ALUMINIUM",
        "ZINC",
        "LEAD",
        "NICKEL",
    ]


def available_mcx_intelligence_signals():
    return [
        "STRONG BULLISH",
        "BULLISH",
        "NEUTRAL",
        "BEARISH",
        "STRONG BEARISH",
    ]


def available_positioning_states():
    return [
        "LONG BUILD-UP",
        "SHORT COVERING",
        "MIXED",
        "LONG UNWINDING",
        "SHORT BUILD-UP",
    ]


def available_volatility_regimes():
    return [
        "HIGH / PREMIUM",
        "ELEVATED",
        "NORMAL",
        "COMPRESSED",
        "LOW / CHEAP",
    ]


def available_mcx_term_structures():
    return [
        "BACKWARDATION",
        "MILD BACKWARDATION",
        "FLAT",
        "MILD CONTANGO",
        "CONTANGO",
    ]


def available_mcx_roll_behaviours():
    return [
        "POSITIVE ROLL",
        "NEUTRAL ROLL",
        "NEGATIVE ROLL",
        "ROLL RISK",
    ]


# ---------------------------------------------------------------------
# CONVENIENCE FUNCTION
# ---------------------------------------------------------------------

def build_mcx_intelligence_snapshot(
    commodities=None,
    min_score: float = 0.0,
    min_momentum: float = -999.0,
    min_liquidity: float = 0.0,
    min_oi_change: float = -999.0,
    max_oi_change: float = 999.0,
    signals=None,
    positioning=None,
    volatility_regimes=None,
    term_structures=None,
    roll_behaviours=None,
    seed: int = 8617,
):
    universe = build_mcx_intelligence(
        commodities=commodities,
        seed=seed,
    )

    filtered = apply_mcx_intelligence_filters(
        universe,
        commodities=commodities,
        signals=signals,
        positioning=positioning,
        volatility_regimes=volatility_regimes,
        term_structures=term_structures,
        roll_behaviours=roll_behaviours,
        min_score=min_score,
        min_momentum=min_momentum,
        min_liquidity=min_liquidity,
        min_oi_change=min_oi_change,
        max_oi_change=max_oi_change,
    )

    ranked = rank_mcx_intelligence(filtered)

    summary = mcx_intelligence_summary(
        ranked
    )

    return ranked, summary


# ---------------------------------------------------------------------
# END
# ---------------------------------------------------------------------