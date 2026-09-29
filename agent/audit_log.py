"""
Appends every single evaluation - traded or not - to an immutable
JSONL file. This is your hackathon paper-trading log and your
Submission Materials Link deliverable.
"""
from __future__ import annotations
import json
import os
from datetime import datetime, timezone

from config import AUDIT_LOG_PATH


def log_evaluation(symbol: str, quant: dict, votes: list, decision, execution) -> None:
    os.makedirs(os.path.dirname(AUDIT_LOG_PATH), exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "symbol": symbol,
        "quant": quant,
        "votes": [vars(v) for v in votes],
        "decision": {
            "action": decision.action,
            "weighted_score": decision.weighted_score,
            "z_score": decision.z_score,
            "liquidity_ratio": decision.liquidity_ratio,
            "reasons": decision.reasons,
        },
        "execution": {
            "status": execution.status,
            "detail": execution.detail,
        },
    }
    with open(AUDIT_LOG_PATH, "a") as f:
        f.write(json.dumps(record) + "\n")
