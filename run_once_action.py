"""
Entry point for GitHub Actions. Unlike main.py's run_forever() loop,
this runs ONE evaluation pass against fresh news and exits - GitHub
Actions calls this on a schedule (see .github/workflows/hollis.yml)
instead of HOLLIS needing to run continuously on a machine you own.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "agent"))

from main import run_once
from state import load_state


def get_news_items() -> list[dict]:
    """
    Replace with your real news source. Kept separate from main.py's
    dummy_news_source so the Actions entrypoint and the long-running
    loop can use different sources if you ever need to.
    """
    return []


if __name__ == "__main__":
    state = load_state()
    run_once(get_news_items(), state)
    print(f"Pass complete. {len(state['last_seen_headline_ids'])} headlines tracked so far.")
