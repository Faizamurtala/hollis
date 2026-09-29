"""
HOLLIS - Agentic Trading config
Bitget rToken pairs trade as <rTICKER>/USDT, e.g. rNVDA/USDT.
"""

# Live rToken/USDT pairs on Bitget covered by this build
SYMBOLS = [
    "rNVDA/USDT",
    "rTSLA/USDT",
    "rAAPL/USDT",
    "rAMD/USDT",
    "rGOOGL/USDT",
]

# Map each rToken pair to the native equity ticker used for
# historical backtest data (Yahoo/other equity data providers
# don't know about "rNVDA/USDT" - they know "NVDA").
NATIVE_TICKER = {
    "rNVDA/USDT": "NVDA",
    "rTSLA/USDT": "TSLA",
    "rAAPL/USDT": "AAPL",
    "rAMD/USDT": "AMD",
    "rGOOGL/USDT": "GOOGL",
}

# Benchmark used for rolling-beta / expected-move calculation
BENCHMARK = "QQQ"

# Risk gate thresholds
Z_SCORE_THRESHOLD = 2.0          # |z| must exceed this to act
MIN_LIQUIDITY_RATIO = 0.50       # volume vs 20d average
MAX_CONCURRENT_POSITIONS = 3
POSITION_SIZE_PCT = 0.03         # 3% of paper portfolio per trade

# Consensus panel weights (recalibrated over time by audit_log stats)
DEFAULT_PANEL_WEIGHTS = {
    "macro": 0.34,
    "liquidity": 0.33,
    "correlation": 0.33,
}

# Loop interval while running unattended (seconds)
POLL_INTERVAL_SECONDS = 300  # 5 minutes

# Paths
AUDIT_LOG_PATH = "logs/hollis_audit.jsonl"
