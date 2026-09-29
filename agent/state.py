"""
Tiny persistence layer so a laptop reboot doesn't wipe out
whatever HOLLIS was tracking in memory. Saved to disk every
cycle, reloaded automatically on startup.
"""
from __future__ import annotations
import json
import os

STATE_PATH = "logs/hollis_state.json"

_default_state = {
    "last_seen_headline_ids": [],   # avoid re-acting on the same headline twice
    "last_prices": {},              # symbol -> last observed price/volume snapshot
    "panel_weights": None,          # None = use config.DEFAULT_PANEL_WEIGHTS
}


def load_state() -> dict:
    if not os.path.exists(STATE_PATH):
        return dict(_default_state)
    try:
        with open(STATE_PATH, "r") as f:
            data = json.load(f)
        merged = dict(_default_state)
        merged.update(data)
        return merged
    except Exception:
        # corrupted or half-written file - don't crash the whole agent over it
        return dict(_default_state)


def save_state(state: dict) -> None:
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    tmp_path = STATE_PATH + ".tmp"
    with open(tmp_path, "w") as f:
        json.dump(state, f)
    os.replace(tmp_path, STATE_PATH)  # atomic on Windows and POSIX - avoids a half-written file if power cuts mid-save
