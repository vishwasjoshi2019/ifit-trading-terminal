from __future__ import annotations

from typing import Any, Dict

def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

def build_footprint_decision_intelligence(auction_summary: Dict[str, Any], footprint_summary=None, footprint_intelligence=None) -> Dict[str, Any]:
    a = auction_summary or {}
    state = str(a.get('Auction State', 'BALANCED')).upper()
    confidence = _num(a.get('Auction Confidence', 0))
    poc = str(a.get('POC Migration', 'NONE')).upper()
    failed = str(a.get('Failed Auction', 'NONE')).upper()
    flip = str(a.get('Delta Flip', 'NONE')).upper()
    cvd = str(a.get('CVD Divergence', 'NONE')).upper()
    mapping = {
        'INITIATIVE BUYING': ('BULLISH AUCTION','BUY-SIDE FLOW','Aggressive buyers are accepting higher prices.','Trend continuation / pullback confirmation'),
        'INITIATIVE SELLING': ('BEARISH AUCTION','SELL-SIDE FLOW','Aggressive sellers are accepting lower prices.','Trend continuation / rally rejection'),
        'ABSORPTION': ('ABSORPTION / REVERSAL WATCH','ABSORPTION','Aggressive flow is being absorbed at the auction.','Wait for confirmation away from absorption zone'),
        'EXHAUSTION': ('EXHAUSTION / REVERSAL WATCH','EXHAUSTION','Aggressive participation is showing signs of exhaustion.','Wait for reversal confirmation'),
        'FAILED AUCTION': ('FAILED AUCTION','FAILED AUCTION','Price discovery failed beyond the auction area.','Re-entry / rejection confirmation'),
        'IMBALANCE EXPANSION': ('IMBALANCE EXPANSION','IMBALANCE','One-sided order-flow pressure is expanding.','Momentum confirmation'),
        'ROTATION': ('ROTATION','ROTATIONAL','Two-way trade is dominating the auction.','Mean-reversion / range context'),
    }
    market_state, signal, thesis, strategy = mapping.get(state, ('BALANCED AUCTION','NO DECISIVE FLOW','Order flow is not showing a decisive auction state.','Wait for auction imbalance'))
    score = confidence + (5 if poc in ('UP','DOWN') else 0) + (5 if failed != 'NONE' else 0) + (3 if flip != 'NONE' else 0) + (3 if cvd != 'NONE' else 0)
    score = max(0.0, min(100.0, score))
    confirmations = []
    if poc != 'NONE': confirmations.append('POC migration ' + poc)
    if flip != 'NONE': confirmations.append('delta ' + flip)
    if cvd != 'NONE': confirmations.append(cvd)
    if failed != 'NONE': confirmations.append(failed)
    return {'Market State': market_state, 'Auction State': state, 'Decision Signal': signal, 'Decision Confidence': round(score,1), 'Thesis': thesis, 'Confirmation': ', '.join(confirmations) if confirmations else 'Await confirmation', 'Risk / Invalidation': 'Invalidation: auction state fails to persist and price returns through the active auction zone.', 'Strategy Context': strategy, 'POC Migration': poc, 'CVD Divergence': cvd, 'Delta Flip': flip, 'Failed Auction': failed, 'Source': 'CHT Footprint V0.4'}

def decision_intelligence_summary(decision: Dict[str, Any]) -> Dict[str, Any]:
    return {'Market State': decision.get('Market State','N/A'), 'Signal': decision.get('Decision Signal','N/A'), 'Confidence': decision.get('Decision Confidence',0), 'Thesis': decision.get('Thesis','N/A'), 'Confirmation': decision.get('Confirmation','Await confirmation'), 'Risk / Invalidation': decision.get('Risk / Invalidation','N/A'), 'Strategy Context': decision.get('Strategy Context','N/A')}
