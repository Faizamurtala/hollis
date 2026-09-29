"""
Combines the consensus panel's votes with the risk_math z-score
behind a fixed risk-budget gate. If the gate fails, the decision
is NO_TRADE - and that gets logged just like a trade would.
"""
from __future__ import annotations
from dataclasses import dataclass, field

from config import Z_SCORE_THRESHOLD, MIN_LIQUIDITY_RATIO, DEFAULT_PANEL_WEIGHTS
from consensus_panel import AgentVote

VOTE_SCORE = {"BULLISH": 1.0, "NEUTRAL": 0.0, "BEARISH": -1.0}


@dataclass
class Decision:
    symbol: str
    action: str  # "LONG", "SHORT", "NO_TRADE"
    weighted_score: float
    z_score: float
    liquidity_ratio: float
    reasons: list[str] = field(default_factory=list)


def weighted_consensus(votes: list[AgentVote], weights: dict[str, float] = None) -> float:
    weights = weights or DEFAULT_PANEL_WEIGHTS
    total = 0.0
    for v in votes:
        w = weights.get(v.agent, 0.0)
        total += w * v.confidence * VOTE_SCORE.get(v.vote, 0.0)
    return total  # roughly -1.0 .. +1.0


def decide(symbol: str, votes: list[AgentVote], quant: dict,
           consensus_threshold: float = 0.35) -> Decision:
    score = weighted_consensus(votes)
    z = quant["z_score"]
    liq = quant["liquidity_ratio"]
    reasons: list[str] = []

    if abs(z) < Z_SCORE_THRESHOLD:
        reasons.append(f"|z|={abs(z):.2f} below threshold {Z_SCORE_THRESHOLD}")
    if liq < MIN_LIQUIDITY_RATIO:
        reasons.append(f"liquidity_ratio={liq:.2f} below floor {MIN_LIQUIDITY_RATIO}")
    if abs(score) < consensus_threshold:
        reasons.append(f"panel consensus too weak ({score:+.2f})")

    if reasons:
        return Decision(symbol, "NO_TRADE", score, z, liq, reasons)

    action = "LONG" if score > 0 else "SHORT"
    reasons.append(f"panel={score:+.2f}, z={z:+.2f}, liq={liq:.2f} all cleared the gate")
    return Decision(symbol, action, score, z, liq, reasons)
