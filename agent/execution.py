"""
Executes approved decisions as PAPER orders through Bitget Agent Hub.
Safe-mode defaults on throughout: dryRun and --paper-trading are the
expectation for the entire hackathon window, not just for testing.

Two integration options - pick one and delete the other:

1) MCP Server (if HOLLIS runs inside an MCP-aware client): call the
   Agent Hub trading tools directly the way you'd call any other tool.

2) `bgc` CLI (if HOLLIS runs as a standalone script/service): shell out
   to the CLI, which is the pattern used below.
"""
from __future__ import annotations
import subprocess
import json
from dataclasses import dataclass

from config import POSITION_SIZE_PCT
from decision_engine import Decision


@dataclass
class ExecutionResult:
    symbol: str
    action: str
    status: str          # "PAPER_FILLED", "NO_TRADE", "ERROR"
    detail: str


def place_paper_order(symbol: str, side: str, size_pct: float = POSITION_SIZE_PCT) -> ExecutionResult:
    """
    Shells out to the bgc CLI in paper-trading / dryRun mode.
    Adjust the command to match whatever bgc's actual order syntax is
    once you've run `bgc --help` against your installed version.
    """
    cmd = [
        "bgc", "order", "place",
        "--symbol", symbol,
        "--side", side,
        "--size-pct", str(size_pct),
        "--paper-trading",
        "--dry-run",  # remove only after you've verified the pipeline end-to-end
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if proc.returncode == 0:
            return ExecutionResult(symbol, side, "PAPER_FILLED", proc.stdout.strip())
        return ExecutionResult(symbol, side, "ERROR", proc.stderr.strip())
    except FileNotFoundError:
        return ExecutionResult(symbol, side, "ERROR", "bgc CLI not found - is Agent Hub installed?")
    except subprocess.TimeoutExpired:
        return ExecutionResult(symbol, side, "ERROR", "bgc order timed out")


def execute(decision: Decision) -> ExecutionResult:
    if decision.action == "NO_TRADE":
        return ExecutionResult(decision.symbol, "NO_TRADE", "NO_TRADE", "; ".join(decision.reasons))
    side = "buy" if decision.action == "LONG" else "sell"
    return place_paper_order(decision.symbol, side)
