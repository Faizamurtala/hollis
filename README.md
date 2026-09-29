# HOLLIS — Agentic Trading build & deployment guide

Bitget AI Base Camp Hackathon S2 · Agentic Trading track
Covered pairs: `rNVDA/USDT`, `rTSLA/USDT`, `rAAPL/USDT`, `rAMD/USDT`, `rGOOGL/USDT`

Pipeline: **event ingestion → deterministic quant engine → three-agent consensus
panel → risk-budget decision gate → paper execution → immutable audit log.**
The LLM panel never sees the quant z-score, so it can't just rationalize the
math — it has to form its own read on macro, liquidity, and cross-asset
correlation independently.

---

## 1. Local development

```bash
cd hollis
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in keys, never commit this file
```

Wire the three `NotImplementedError` stubs before running anything live:

| File | Function | What to plug in |
|---|---|---|
| `agent/consensus_panel.py` | `call_llm()` | Your LLM client — Anthropic SDK, or the hackathon's Qwen endpoint (`QWEN_BASE_URL`, model `qwen3.8-max`) |
| `agent/main.py` | `fetch_market_data()` | Bitget Agent Hub market data tools for the rToken pair + an equities source (e.g. yfinance) for the native ticker and `QQQ` |
| `agent/main.py` | `dummy_news_source()` | A real feed — RSS, a news API, or Agent Hub's `bitget-signal` `news-briefing` skill |

Test each module against a static CSV of historical data first — debugging
`risk_math.py` and `consensus_panel.py` against a fixed file is far faster
than debugging against a live stream.

## 2. Install Bitget Agent Hub

```bash
# Terminal-based (this build uses the bgc CLI from execution.py):
git clone https://github.com/BitgetLimited/agent_hub
# follow its install instructions for the bgc CLI

# Authorize an Agentic sub-account (isolated funds, OAuth, no manual API key):
# give your coding agent this prompt once, per the hackathon handbook:
#   "Please read https://www.bitget.careers/support/articles/12560603894122
#    and help me complete the Bitget Agentic account authorization process."
```

Run everything in safe mode for the entire competition:

```bash
bgc --read-only        # fully read-only session while wiring things up
bgc --paper-trading     # routes to Bitget's Demo environment once ready to place orders
```

`execution.py` already shells out with `--paper-trading --dry-run` on every
call — leave both flags in place for the whole event.

## 3. Run the loop

```bash
python agent/main.py
```

This polls every `POLL_INTERVAL_SECONDS` (default 5 min, `config.py`), and on
every fresh, symbol-matched headline runs the full pipeline once. Every
outcome — trade or `NO_TRADE` — lands in `logs/hollis_audit.jsonl`.

## 4. Containerize

```dockerfile
# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY agent/ ./agent/
CMD ["python", "agent/main.py"]
```

```bash
docker build -t hollis .
docker run -d --env-file .env --name hollis --restart unless-stopped hollis
```

## 5. Deploy for free with no card and no machine of your own (GitHub Actions)

If you can't guarantee steady power for a laptop or pay for a VPS, GitHub
Actions runs your code on a free schedule using GitHub's own machines - no
card, no server to maintain. It doesn't run *continuously* like a service
does; instead it wakes up every 15 minutes, does one evaluation pass, saves
the result, and shuts down. For a >=4 hour news-freshness window that's more
than fine.

1. Push this whole `hollis` folder to a new GitHub repo (public repos get
   the most free Actions minutes; private repos also get a free monthly
   allowance, which is enough for a 15-minute cadence).
2. In the repo, go to **Settings → Secrets and variables → Actions** and add
   your keys as repository secrets: `ANTHROPIC_API_KEY` (or
   `BITGET_QWEN_API_KEY`), `BITGET_AGENTIC_ACCOUNT_TOKEN`, and optionally
   `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID`. Never put real keys in the
   workflow file itself - secrets are the only safe place for them.
3. The workflow file is already at `.github/workflows/hollis.yml`. It
   checks out the repo, installs Python + Node, runs
   `run_once_action.py` (one pass, then exits), and commits
   `logs/hollis_audit.jsonl` and `logs/hollis_state.json` back to the repo
   automatically - so your paper-trading log lives in the repo itself and
   you can watch it grow just by refreshing the GitHub file view.
4. Go to the **Actions** tab once you've pushed, click into "hollis-poll",
   and click **Run workflow** to trigger one pass manually and confirm it
   works before waiting on the schedule.
5. Adjust the `npm install -g bitget-agent-hub` line once you know Agent
   Hub's actual install command for a headless Linux runner - the exact
   package/command may differ from the placeholder here.
6. That's it - as long as the repo exists and you don't disable the
   workflow, it keeps polling on GitHub's infrastructure regardless of
   your own laptop's power.

## 6. Deploy to an always-on host (alternative, if you later get budget)

A serverless function isn't a good fit here — this needs to run continuously
through nights and weekends, and a cold-started function can miss the exact
overnight window the whole project is built around.

```bash
# Any small VPS (DigitalOcean, Hetzner, a free-tier Fly.io app) works.
ssh you@your-vps
git clone <your-repo>
cd hollis
docker build -t hollis .
docker run -d --env-file .env --name hollis --restart unless-stopped hollis
docker logs -f hollis   # confirm it's polling
```

If you'd rather run it as a plain systemd service instead of Docker:

```ini
# /etc/systemd/system/hollis.service
[Unit]
Description=HOLLIS agentic trading loop
After=network.target

[Service]
WorkingDirectory=/opt/hollis
ExecStart=/opt/hollis/.venv/bin/python agent/main.py
EnvironmentFile=/opt/hollis/.env
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now hollis
sudo journalctl -u hollis -f
```

## 7. Minimal audit dashboard

A single page that reads `hollis_audit.jsonl` and shows recent decisions,
trade/no-trade counts, and running stats becomes your **Submission Materials
Link** demo and proves the agent has actually been running unattended.
A small FastAPI route or even a static page regenerated by a cron job both
work — judges just need something they can open and see live data in.

## 8. Alerting

A Telegram bot webhook that posts every decision (including the reasoning
behind every `NO_TRADE`) gives you visibility without babysitting logs, and
doubles as good material for X progress posts (Best Spread Award).

## 9. Before you submit

- [ ] Confirm the deadline in the official handbook table — go by that, not by
      dates repeated in other builders' X posts.
- [ ] Let the loop run unattended for **2+ weeks** before submitting; log every
      evaluation, not just the trades.
- [ ] Write the six-part project description: **thesis, target user (a
      specific segment — not "all traders"), validation data (label
      observed vs. targeted), progress, deliverables, optional AI-trading
      take**.
- [ ] Fill "Role of the LLM in Your Project" — the panel's three prompts and
      which model you used.
- [ ] One Submission Materials Link with GitHub + dashboard + `hollis_audit.jsonl`.
- [ ] A compliant X post with `#BitgetHackathon` and `@Bitget_AI`, introducing
      the actual product — not a bare retweet.
- [ ] If entering a second theme, that's a fully separate form submission with
      its own project name and materials.
