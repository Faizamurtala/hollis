"""
HOLLIS main loop.
EVENT -> QUANT -> CONSENSUS PANEL -> DECISION GATE -> PAPER EXECUTION -> AUDIT LOG
Runs continuously (poll interval in config.py) so it produces a real,
unattended paper-trading log for the hackathon's >=2 week window.
"""
from __future__ import annotations
import time
import logging

from config import POLL_INTERVAL_SECONDS
from event_listener import poll_feeds
from risk_math import evaluate as quant_evaluate
from consensus_panel import run_panel
from decision_engine import decide
from execution import execute
from audit_log import log_evaluation
from state import load_state, save_state

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("hollis")


def fetch_market_data(symbol: str) -> dict:
    """
    Wire this to your real market data source (Bitget Agent Hub's
    market data tools for the rToken pair, plus an equities source
    for the native ticker and QQQ). Returns everything risk_math and
    consensus_panel need for one evaluation pass.
    """
    raise NotImplementedError("Wire this to live/paper market data feeds.")


def run_once(raw_news_items: list[dict], state: dict) -> None:
    events = poll_feeds(raw_news_items)
    for event in events:
        headline_id = f"{event.symbol}:{event.headline}"
        if headline_id in state["last_seen_headline_ids"]:
            continue  # already acted on this exact headline before a restart
        try:
            data = fetch_market_data(event.symbol)
            quant = quant_evaluate(
                data["asset_returns"], data["bench_returns"],
                data["actual_move_pct"], data["bench_move_pct"],
                data["historical_gap_std_pct"],
                data["current_volume"], data["avg_20d_volume"],
            )
            votes = run_panel(
                headline=event.headline, event_type=data.get("event_type", "unknown"),
                liquidity_ratio_val=quant["liquidity_ratio"], spread_bps=data.get("spread_bps", 0.0),
                rtoken_move_pct=data["actual_move_pct"], native_move_pct=data.get("native_move_pct", 0.0),
                lag_hours=data.get("lag_hours", 0.0),
            )
            decision = decide(event.symbol, votes, quant)
            result = execute(decision)
            log_evaluation(event.symbol, quant, votes, decision, result)
            log.info("%s -> %s (%s)", event.symbol, decision.action, result.status)

            state["last_seen_headline_ids"].append(headline_id)
            state["last_seen_headline_ids"] = state["last_seen_headline_ids"][-500:]  # keep it bounded
            state["last_prices"][event.symbol] = {
                "actual_move_pct": data["actual_move_pct"],
                "z_score": quant["z_score"],
            }
        except Exception:
            log.exception("Evaluation failed for %s", event.symbol)
    save_state(state)  # persist once per cycle, not per event - cheap and reboot-safe


def run_forever(news_source) -> None:
    """news_source: callable returning fresh raw_news_items each poll."""
    state = load_state()
    log.info("HOLLIS starting - polling every %ss (resumed state: %d known headlines)",
              POLL_INTERVAL_SECONDS, len(state["last_seen_headline_ids"]))
    while True:
        run_once(news_source(), state)
        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    def dummy_news_source():
        return []  # replace with a real feed before running unattended
    run_forever(dummy_news_source)
