"""
IFIT Decision Intelligence Engine
V0.9.0 - first intelligence aggregation layer.

Purpose:
Convert existing IFIT screening/analytics outputs into an explainable
decision snapshot rather than another raw-data screen.

This version is intentionally deterministic and simulation-safe. It can
consume the existing Market, Derivatives, Order Flow and Quant engines.
No external market-data dependency is introduced.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional
import math


@dataclass
class DecisionConfig:
    market_name: str = "NIFTY 50"
    seed: int = 8509
    bullish_threshold: float = 60.0
    bearish_threshold: float = 40.0


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, float(value)))


def _safe_mean(values, default: float = 50.0) -> float:
    vals = []
    for v in values:
        try:
            if v is not None and math.isfinite(float(v)):
                vals.append(float(v))
        except Exception:
            pass
    return sum(vals) / len(vals) if vals else default


def _signal_score(signal: str) -> float:
    """Map common IFIT signal labels to a 0-100 directional score."""
    s = str(signal or "").upper().strip()
    mapping = {
        "STRONG BUY": 90.0,
        "BUY": 75.0,
        "LONG BUILDUP": 82.0,
        "SHORT COVERING": 70.0,
        "BULLISH": 75.0,
        "STRONG BULLISH": 90.0,
        "LEADER": 82.0,
        "OUTPERFORM": 70.0,
        "NEUTRAL": 50.0,
        "MEAN": 50.0,
        "ABOVE MEAN": 58.0,
        "BELOW MEAN": 42.0,
        "OVERSOLD": 62.0,
        "SELL": 25.0,
        "STRONG SELL": 10.0,
        "SHORT BUILDUP": 18.0,
        "LONG UNWINDING": 30.0,
        "BEARISH": 25.0,
        "STRONG BEARISH": 10.0,
        "UNDERPERFORM": 30.0,
        "LAGGARD": 18.0,
    }
    return mapping.get(s, 50.0)


def _extract_signal_counts(summary: Dict[str, Any]) -> Dict[str, int]:
    counts = {}
    for key, value in summary.items():
        try:
            if isinstance(value, (int, float)) and key not in {
                "Stocks", "Average Momentum", "Average Z-Score",
                "Average Volatility", "Average Correlation",
                "Average Delta %", "Average Imbalance %",
                "Average Absorption", "Average CVD Change %",
                "Average Order Flow Score", "Average Quant Score",
            }:
                counts[str(key)] = int(value)
        except Exception:
            pass
    return counts


def _dominant_signal(counts: Dict[str, int]) -> str:
    if not counts:
        return "NEUTRAL"
    return max(counts.items(), key=lambda x: x[1])[0]


def _score_market(market_summary: Dict[str, Any]) -> float:
    """Convert Market Screener summary into a directional 0-100 score."""
    raw = market_summary.get("Market Score")
    if raw is not None:
        try:
            return _clamp(raw)
        except Exception:
            pass

    signal = market_summary.get("Signal", "NEUTRAL")
    return _signal_score(signal)


def _score_derivatives(derivatives_summary: Dict[str, Any]) -> float:
    signal = derivatives_summary.get("Signal", "NEUTRAL")
    score = _signal_score(signal)

    # Small adjustment from average OI change where available.
    oi_change = derivatives_summary.get("Avg OI Change %")
    try:
        score += max(-10.0, min(10.0, float(oi_change) * 0.20))
    except Exception:
        pass

    return _clamp(score)


def _score_orderflow(orderflow_summary: Dict[str, Any]) -> float:
    raw = orderflow_summary.get("Average Order Flow Score")
    if raw is not None:
        try:
            return _clamp(raw)
        except Exception:
            pass
    return _signal_score(orderflow_summary.get("Signal", "NEUTRAL"))


def _score_quant(quant_summary: Dict[str, Any]) -> float:
    raw = quant_summary.get("Average Quant Score")
    if raw is not None:
        try:
            return _clamp(raw)
        except Exception:
            pass
    return _signal_score(quant_summary.get("Signal", "NEUTRAL"))


def _regime(score: float, volatility: float, trend_strength: float) -> str:
    if score >= 68 and trend_strength >= 60:
        return "BULLISH TREND"
    if score <= 32 and trend_strength >= 60:
        return "BEARISH TREND"
    if volatility >= 75 and trend_strength < 55:
        return "HIGH-VOLATILITY / UNSTABLE"
    if 42 <= score <= 58:
        return "RANGE / NEUTRAL"
    if score > 58:
        return "BULLISH BIAS"
    return "BEARISH BIAS"


def _confidence(component_scores: Dict[str, float]) -> float:
    values = list(component_scores.values())
    if not values:
        return 50.0
    mean = _safe_mean(values)
    dispersion = _safe_mean([abs(v - mean) for v in values], 0.0)
    # Agreement raises confidence; disagreement reduces it.
    confidence = 55.0 + (abs(mean - 50.0) * 0.45) - (dispersion * 0.70)
    return round(_clamp(confidence, 25.0, 95.0), 2)


def _direction(score: float) -> str:
    if score >= 65:
        return "BULLISH"
    if score <= 35:
        return "BEARISH"
    return "NEUTRAL"


def _framework(direction: str, regime: str, volatility: float) -> str:
    if direction == "BULLISH":
        if volatility >= 70:
            return "Defined-Risk Bull Call Spread"
        if "TREND" in regime:
            return "Bull Call Spread / Call Debit Structure"
        return "Bull Put Spread / Defined-Risk Bullish Structure"

    if direction == "BEARISH":
        if volatility >= 70:
            return "Defined-Risk Bear Put Spread"
        if "TREND" in regime:
            return "Bear Put Spread / Put Debit Structure"
        return "Bear Call Spread / Defined-Risk Bearish Structure"

    if volatility >= 70:
        return "Volatility-Defined Neutral Structure"
    return "Range / Mean-Reversion Framework"


def _risk_level(confidence: float, volatility: float, dispersion: float) -> str:
    if volatility >= 75 or dispersion >= 22:
        return "HIGH"
    if volatility >= 55 or confidence < 55:
        return "MODERATE"
    return "LOW-MODERATE"


def _thesis(direction: str, regime: str, components: Dict[str, float]) -> str:
    ordered = sorted(components.items(), key=lambda x: abs(x[1] - 50.0), reverse=True)
    strongest = ordered[0][0] if ordered else "Market"

    if direction == "BULLISH":
        return (
            f"{strongest} is the strongest positive confirmation. "
            f"Combined evidence supports a {regime.lower()} with a bullish directional bias. "
            "Prefer defined-risk structures and invalidate the thesis if the underlying "
            "loses its key market structure."
        )
    if direction == "BEARISH":
        return (
            f"{strongest} is the strongest negative confirmation. "
            f"Combined evidence supports a {regime.lower()} with a bearish directional bias. "
            "Prefer defined-risk structures and invalidate the thesis if market structure "
            "reclaims the key resistance zone."
        )
    return (
        "The major IFIT components are not sufficiently aligned for a strong directional "
        "call. Treat the market as neutral/range-bound and wait for confirmation before "
        "increasing directional risk."
    )


def build_decision_snapshot(
    market_summary: Optional[Dict[str, Any]] = None,
    derivatives_summary: Optional[Dict[str, Any]] = None,
    orderflow_summary: Optional[Dict[str, Any]] = None,
    quant_summary: Optional[Dict[str, Any]] = None,
    config: Optional[DecisionConfig] = None,
) -> Dict[str, Any]:
    """
    Build one explainable IFIT decision snapshot.

    Inputs are summaries from existing engines. Missing components are allowed;
    the engine remains usable and marks the source as unavailable.
    """
    config = config or DecisionConfig()

    market_summary = market_summary or {}
    derivatives_summary = derivatives_summary or {}
    orderflow_summary = orderflow_summary or {}
    quant_summary = quant_summary or {}

    components = {
        "Market": _score_market(market_summary),
        "Derivatives": _score_derivatives(derivatives_summary),
        "Order Flow": _score_orderflow(orderflow_summary),
        "Quant": _score_quant(quant_summary),
    }

    weights = {
        "Market": 0.30,
        "Derivatives": 0.25,
        "Order Flow": 0.25,
        "Quant": 0.20,
    }

    composite = sum(components[k] * weights[k] for k in components)
    composite = round(_clamp(composite), 2)

    avg_vol = quant_summary.get("Average Volatility", 50.0)
    try:
        volatility_proxy = _clamp(float(avg_vol) * 4.0)
    except Exception:
        volatility_proxy = 50.0

    trend_strength = market_summary.get("Average Momentum", 50.0)
    try:
        trend_proxy = _clamp(50.0 + float(trend_strength) * 3.0)
    except Exception:
        trend_proxy = 50.0

    dispersion = _safe_mean(
        [abs(v - composite) for v in components.values()],
        0.0,
    )

    direction = _direction(composite)
    regime = _regime(composite, volatility_proxy, trend_proxy)
    confidence = _confidence(components)
    risk = _risk_level(confidence, volatility_proxy, dispersion)
    framework = _framework(direction, regime, volatility_proxy)

    # Simulation-safe invalidation reference. This is deliberately expressed
    # as a rule rather than a fake exact live price.
    if direction == "BULLISH":
        invalidation = "Below the latest IFIT market-structure support"
    elif direction == "BEARISH":
        invalidation = "Above the latest IFIT market-structure resistance"
    else:
        invalidation = "Breakout/breakdown of the active range"

    source_status = {
        "Market": bool(market_summary),
        "Derivatives": bool(derivatives_summary),
        "Order Flow": bool(orderflow_summary),
        "Quant": bool(quant_summary),
    }

    dominant = max(components.items(), key=lambda x: abs(x[1] - 50.0))

    return {
        "Market": config.market_name,
        "Direction": direction,
        "Decision Score": composite,
        "Confidence %": confidence,
        "Regime": regime,
        "Risk": risk,
        "Preferred Framework": framework,
        "Invalidation": invalidation,
        "Investment / Trading Thesis": _thesis(direction, regime, components),
        "Dominant Signal": dominant[0],
        "Dominant Score": round(dominant[1], 2),
        "Component Scores": {k: round(v, 2) for k, v in components.items()},
        "Component Weights": weights,
        "Component Dispersion": round(dispersion, 2),
        "Source Status": source_status,
        "Engine": "IFIT Decision Intelligence V0.9.0",
    }


def build_demo_decision() -> Dict[str, Any]:
    """Standalone deterministic demo for development/QA."""
    return build_decision_snapshot(
        market_summary={
            "Market Score": 68.0,
            "Signal": "OUTPERFORM",
            "Average Momentum": 5.5,
        },
        derivatives_summary={
            "Signal": "LONG BUILDUP",
            "Avg OI Change %": 9.0,
        },
        orderflow_summary={
            "Average Order Flow Score": 72.0,
            "Signal": "BUY",
        },
        quant_summary={
            "Average Quant Score": 69.0,
            "Signal": "BULLISH",
            "Average Volatility": 16.0,
        },
    )


if __name__ == "__main__":
    result = build_demo_decision()
    print("DECISION:", result["Direction"])
    print("SCORE:", result["Decision Score"])
    print("CONFIDENCE:", result["Confidence %"])
    print("REGIME:", result["Regime"])
    print("RISK:", result["Risk"])
    print("FRAMEWORK:", result["Preferred Framework"])
    print("COMPONENTS:", result["Component Scores"])
