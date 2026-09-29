"""
Deterministic quant layer - zero LLM dependence.
Computes rolling beta vs a benchmark, expected move, residual,
z-score against a historical distribution, and a liquidity ratio.
"""
from __future__ import annotations
import numpy as np
import pandas as pd


def rolling_beta(asset_returns: pd.Series, bench_returns: pd.Series, window: int = 30) -> float:
    """30-day rolling beta of asset vs benchmark (e.g. QQQ)."""
    aligned = pd.concat([asset_returns, bench_returns], axis=1).dropna().tail(window)
    if len(aligned) < 5:
        return 1.0  # not enough data, assume market beta
    cov = aligned.cov().iloc[0, 1]
    var = aligned.iloc[:, 1].var()
    return float(cov / var) if var > 0 else 1.0


def expected_move(beta: float, bench_move_pct: float) -> float:
    return beta * bench_move_pct


def z_score(residual_pct: float, historical_gap_std_pct: float, vol_floor_bps: float = 80.0) -> float:
    """
    Standardize the residual (actual - expected move) against the
    historical gap-distribution std dev for this symbol, with a
    defensive volatility floor so illiquid symbols don't produce
    exaggerated z-scores from a tiny denominator.
    """
    floor_pct = vol_floor_bps / 10000.0
    denom = max(historical_gap_std_pct, floor_pct)
    return residual_pct / denom


def liquidity_ratio(current_volume: float, avg_20d_volume: float) -> float:
    if avg_20d_volume <= 0:
        return 0.0
    return current_volume / avg_20d_volume


def evaluate(asset_returns: pd.Series, bench_returns: pd.Series,
             actual_move_pct: float, bench_move_pct: float,
             historical_gap_std_pct: float,
             current_volume: float, avg_20d_volume: float) -> dict:
    beta = rolling_beta(asset_returns, bench_returns)
    exp_move = expected_move(beta, bench_move_pct)
    residual = actual_move_pct - exp_move
    z = z_score(residual, historical_gap_std_pct)
    liq = liquidity_ratio(current_volume, avg_20d_volume)
    return {
        "beta": beta,
        "expected_move_pct": exp_move,
        "actual_move_pct": actual_move_pct,
        "residual_pct": residual,
        "z_score": z,
        "liquidity_ratio": liq,
    }
