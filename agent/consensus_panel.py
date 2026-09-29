"""
Three specialist agents vote independently:
  - macro: reads only the headline + event type
  - liquidity: reads only order-book depth / volume ratio
  - correlation: reads only rToken vs native-stock divergence

None of them sees the risk_math z-score. This is deliberate -
it keeps the panel from just rationalizing the quant signal
instead of forming an independent judgment.

Swap `call_llm` for whichever client you're using (Anthropic,
OpenAI-compatible Qwen endpoint from the hackathon, etc).
"""
from __future__ import annotations
import json
from dataclasses import dataclass

VOTE_OPTIONS = ("BULLISH", "BEARISH", "NEUTRAL")


@dataclass
class AgentVote:
    agent: str
    vote: str          # one of VOTE_OPTIONS
    confidence: float  # 0.0 - 1.0
    rationale: str


def call_llm(system_prompt: str, user_prompt: str) -> str:
    """
    Placeholder - wire this to your LLM provider.
    Must return raw text; each agent function parses it as JSON below.
    Keep max_tokens small (~150) - these are one-line verdicts, not essays.
    """
    raise NotImplementedError("Wire this to your LLM client (see README).")


def _ask(agent_name: str, system_prompt: str, user_prompt: str) -> AgentVote:
    raw = call_llm(system_prompt, user_prompt)
    try:
        data = json.loads(raw)
        vote = data["vote"].upper()
        if vote not in VOTE_OPTIONS:
            vote = "NEUTRAL"
        return AgentVote(agent_name, vote, float(data.get("confidence", 0.5)), data.get("rationale", ""))
    except Exception:
        return AgentVote(agent_name, "NEUTRAL", 0.0, "parse_error")


def macro_agent(headline: str, event_type: str) -> AgentVote:
    system = (
        "You are a macro news analyst. Given one headline, classify its "
        "directional impact on the named equity as BULLISH, BEARISH, or NEUTRAL. "
        'Respond ONLY as JSON: {"vote": "...", "confidence": 0.0-1.0, "rationale": "one sentence"}'
    )
    user = f"Headline: {headline}\nEvent type: {event_type}"
    return _ask("macro", system, user)


def liquidity_agent(liquidity_ratio: float, spread_bps: float) -> AgentVote:
    system = (
        "You are a market microstructure analyst. Given only liquidity metrics "
        "(no news, no price direction), judge whether current conditions favor "
        "a directional bet (BULLISH liquidity = supportive, BEARISH = hostile/thin, "
        'NEUTRAL = unclear). Respond ONLY as JSON: {"vote": "...", "confidence": 0.0-1.0, "rationale": "one sentence"}'
    )
    user = f"Liquidity ratio vs 20d avg: {liquidity_ratio:.2f}\nSpread: {spread_bps:.1f} bps"
    return _ask("liquidity", system, user)


def correlation_agent(rtoken_move_pct: float, native_move_pct: float, lag_hours: float) -> AgentVote:
    system = (
        "You are a cross-market correlation analyst. Given how much the rToken "
        "has moved versus how much the native listed stock has moved (or is "
        "expected to move once it opens), judge whether the rToken is likely "
        "overreacting (fade it), underreacting (follow it), or in line. "
        'Respond ONLY as JSON: {"vote": "...", "confidence": 0.0-1.0, "rationale": "one sentence"}'
    )
    user = (
        f"rToken move: {rtoken_move_pct:+.2f}%\n"
        f"Native stock move: {native_move_pct:+.2f}%\n"
        f"Hours since native market close: {lag_hours:.1f}"
    )
    return _ask("correlation", system, user)


def run_panel(headline: str, event_type: str, liquidity_ratio_val: float, spread_bps: float,
              rtoken_move_pct: float, native_move_pct: float, lag_hours: float) -> list[AgentVote]:
    return [
        macro_agent(headline, event_type),
        liquidity_agent(liquidity_ratio_val, spread_bps),
        correlation_agent(rtoken_move_pct, native_move_pct, lag_hours),
    ]
