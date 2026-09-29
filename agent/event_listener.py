"""
Polls news/macro feeds, enforces a freshness cutoff, and resolves
each headline to one of the covered rToken symbols with zero LLM
tokens spent on stories that don't match anything we cover.
"""
from __future__ import annotations
import time
from datetime import datetime, timezone
from dataclasses import dataclass

from config import SYMBOLS, NATIVE_TICKER

FRESHNESS_CUTOFF_HOURS = 4


@dataclass
class NewsEvent:
    symbol: str
    headline: str
    source: str
    published_at: datetime


def is_fresh(published_at: datetime, cutoff_hours: int = FRESHNESS_CUTOFF_HOURS) -> bool:
    age_hours = (datetime.now(timezone.utc) - published_at).total_seconds() / 3600
    return age_hours <= cutoff_hours


def resolve_symbol(headline: str) -> str | None:
    """
    Zero-token entity resolver: cheap keyword match against the
    native ticker / company name before any LLM call happens.
    Replace with a proper NER pass if you outgrow keyword matching.
    """
    headline_upper = headline.upper()
    company_hint = {
        "NVDA": ["NVIDIA", "NVDA"],
        "TSLA": ["TESLA", "TSLA"],
        "AAPL": ["APPLE", "AAPL"],
        "AMD": ["AMD", "ADVANCED MICRO"],
        "GOOGL": ["GOOGLE", "ALPHABET", "GOOGL"],
    }
    for symbol in SYMBOLS:
        native = NATIVE_TICKER[symbol]
        hints = company_hint.get(native, [native])
        if any(h in headline_upper for h in hints):
            return symbol
    return None


def poll_feeds(raw_items: list[dict]) -> list[NewsEvent]:
    """
    raw_items: [{"headline": str, "source": str, "published_at": datetime}, ...]
    Wire this to your actual news source (RSS, NewsAPI, Bitget Agent Hub's
    bitget-signal news-briefing skill, etc). Kept generic here so you can
    swap providers without touching the rest of the pipeline.
    """
    events: list[NewsEvent] = []
    for item in raw_items:
        if not is_fresh(item["published_at"]):
            continue
        symbol = resolve_symbol(item["headline"])
        if symbol is None:
            continue  # SKIPPED_NO_ASSET_MATCH - zero LLM tokens spent
        events.append(NewsEvent(
            symbol=symbol,
            headline=item["headline"],
            source=item["source"],
            published_at=item["published_at"],
        ))
    return events
