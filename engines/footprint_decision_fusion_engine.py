from typing import Any, Dict

def footprint_decision_score(footprint=None):
    if not footprint:
        return 50.0
    state = str(footprint.get("Auction State", "BALANCED")).upper()
    confidence = float(footprint.get("Decision Confidence", footprint.get("Auction Confidence", 50.0)) or 50.0)
    directional = {
        "INITIATIVE BUYING": 80.0,
        "INITIATIVE SELLING": 20.0,
        "IMBALANCE EXPANSION": 75.0,
        "FAILED AUCTION": 50.0,
        "ABSORPTION": 50.0,
        "EXHAUSTION": 50.0,
        "ROTATION": 50.0,
        "BALANCED": 50.0,
    }
    score = directional.get(state, 50.0)
    signal = str(footprint.get("Decision Signal", "")).upper()
    if "BUY" in signal and state != "INITIATIVE SELLING":
        score = max(score, 70.0)
    elif "SELL" in signal and state != "INITIATIVE BUYING":
        score = min(score, 30.0)
    w = max(0.0, min(confidence, 100.0)) / 100.0
    return round(50.0 + (score - 50.0) * w, 2)

def fuse_decision_snapshot(base_decision: Dict[str, Any], footprint_decision=None):
    result = dict(base_decision or {})
    old_scores = dict(result.get("Component Scores", {}))
    old_weights = dict(result.get("Component Weights", {}))
    weights = {
        "Market": old_weights.get("Market", 0.30) * 0.80,
        "Derivatives": old_weights.get("Derivatives", 0.25) * 0.80,
        "Order Flow": old_weights.get("Order Flow", 0.25) * 0.80,
        "Quant": old_weights.get("Quant", 0.20) * 0.80,
        "Footprint": 0.20,
    }
    scores = {
        "Market": old_scores.get("Market", 50.0),
        "Derivatives": old_scores.get("Derivatives", 50.0),
        "Order Flow": old_scores.get("Order Flow", 50.0),
        "Quant": old_scores.get("Quant", 50.0),
        "Footprint": footprint_decision_score(footprint_decision),
    }
    composite = round(sum(scores[k] * weights[k] for k in scores), 2)
    direction = "BULLISH" if composite >= 60 else ("BEARISH" if composite <= 40 else "NEUTRAL")
    result["Direction"] = direction
    result["Decision Score"] = composite
    result["Component Scores"] = {k: round(v, 2) for k, v in scores.items()}
    result["Component Weights"] = {k: round(v, 4) for k, v in weights.items()}
    result["Footprint State"] = (footprint_decision or {}).get("Auction State", "UNAVAILABLE")
    result["Footprint Confidence"] = float((footprint_decision or {}).get("Decision Confidence", 0) or 0)
    result["Footprint Signal"] = (footprint_decision or {}).get("Decision Signal", "UNAVAILABLE")
    result["Footprint Thesis"] = (footprint_decision or {}).get("Thesis", "Footprint intelligence unavailable.")
    result["Footprint Risk"] = (footprint_decision or {}).get("Risk / Invalidation", "Footprint confirmation unavailable.")
    result["Source Status"] = dict(result.get("Source Status", {}))
    result["Source Status"]["Footprint"] = bool(footprint_decision)
    result["Engine"] = "IFIT Decision Intelligence V0.9.0 + Footprint Fusion V0.6"
    return result

# V0.6 Native Footprint Builder
from engines.order_flow_footprint_engine import (
    build_footprint_data,
    build_bar_footprint,
    footprint_summary,
)
from engines.footprint_intelligence_engine import (
    classify_footprint_intelligence,
    footprint_intelligence_summary,
)
from engines.footprint_auction_intelligence_engine import (
    build_advanced_auction_snapshot,
    auction_intelligence_summary,
)
from engines.footprint_decision_intelligence_engine import (
    build_footprint_decision_intelligence,
    decision_intelligence_summary,
)


def build_footprint_decision_for_fusion(
    periods: int = 60,
    levels: int = 24,
) -> Dict[str, Any]:
    df = build_footprint_data(periods=periods, levels=levels)
    bars = build_bar_footprint(periods=periods, levels=levels)
    summary = footprint_summary(df)

    intelligence_df = classify_footprint_intelligence(df)
    intelligence = footprint_intelligence_summary(intelligence_df)

    latest_bar = df[df["Bar"] == df["Bar"].max()].copy()
    current_bar = bars.iloc[-1].to_dict() if len(bars) else {}
    previous_bar = bars.iloc[-2].to_dict() if len(bars) >= 2 else {}

    current_poc = float(summary.get("POC", current_bar.get("POC", 0.0)) or 0.0)
    previous_poc = float(previous_bar.get("POC", current_poc) or current_poc)
    current_price = float(current_bar.get("Price", 0.0) or 0.0)
    previous_price = float(previous_bar.get("Price", current_price) or current_price)
    current_cvd = float(current_bar.get("CVD", 0.0) or 0.0)
    previous_cvd = float(previous_bar.get("CVD", current_cvd) or current_cvd)

    auction_snapshot = build_advanced_auction_snapshot(
        latest_bar,
        current_bar=current_bar,
        previous_bar=previous_bar,
        previous_poc=previous_poc,
        current_poc=current_poc,
        price_change=current_price - previous_price,
        cvd_change=current_cvd - previous_cvd,
    )
    auction = auction_intelligence_summary(auction_snapshot)

    return build_footprint_decision_intelligence(
        auction,
        footprint_summary=summary,
        footprint_intelligence=intelligence,
    )


def footprint_fusion_display(decision: Dict[str, Any]) -> Dict[str, Any]:
    summary = decision_intelligence_summary(decision)
    return {
        "Market State": summary.get("Market State", decision.get("Market State", "N/A")),
        "Signal": summary.get("Signal", decision.get("Decision Signal", "N/A")),
        "Confidence": float(summary.get("Confidence", decision.get("Decision Confidence", 0)) or 0),
        "Auction State": decision.get("Auction State", "N/A"),
        "Thesis": summary.get("Thesis", decision.get("Thesis", "N/A")),
        "Confirmation": summary.get("Confirmation", decision.get("Confirmation", "Await confirmation")),
        "Strategy Context": summary.get("Strategy Context", decision.get("Strategy Context", "N/A")),
        "Risk / Invalidation": summary.get("Risk / Invalidation", decision.get("Risk / Invalidation", "N/A")),
        "POC Migration": decision.get("POC Migration", "N/A"),
        "Delta Flip": decision.get("Delta Flip", "N/A"),
        "CVD Divergence": decision.get("CVD Divergence", "N/A"),
        "Failed Auction": decision.get("Failed Auction", "N/A"),
    }
