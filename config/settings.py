"""
AI Trading System - Configuration Settings
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


# ─── Gemini AI ───────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
AI_MODEL = os.getenv("AI_MODEL", "gemini-2.0-flash")
AI_ANALYSIS_INTERVAL = int(os.getenv("AI_ANALYSIS_INTERVAL", "300"))

# ─── MetaTrader 5 ───────────────────────────────────────────
try:
    MT5_LOGIN = int(os.getenv("MT5_LOGIN", "0"))
except (ValueError, TypeError):
    MT5_LOGIN = 0
MT5_PASSWORD = os.getenv("MT5_PASSWORD", "")
MT5_SERVER = os.getenv("MT5_SERVER", "")
MT5_PATH = os.getenv("MT5_PATH", "")

# ─── Trading ────────────────────────────────────────────────
TRADING_MODE = os.getenv("TRADING_MODE", "demo")
MAX_RISK_PERCENT = float(os.getenv("MAX_RISK_PERCENT", "2.0"))
MAX_POSITIONS = int(os.getenv("MAX_POSITIONS", "3"))
DEFAULT_LOT_SIZE = float(os.getenv("DEFAULT_LOT_SIZE", "0.01"))

# ─── Trading Pairs ──────────────────────────────────────────
TRADING_PAIRS = [
    {
        "symbol": "EURUSD",
        "display_name": "EUR/USD",
        "pip_value": 0.0001,
        "spread_limit": 3.0,
        "lot_size": DEFAULT_LOT_SIZE,
        "sl_pips": 30,
        "tp_pips": 50,
    },
    {
        "symbol": "GBPJPY",
        "display_name": "GBP/JPY",
        "pip_value": 0.01,
        "spread_limit": 5.0,
        "lot_size": DEFAULT_LOT_SIZE,
        "sl_pips": 40,
        "tp_pips": 70,
    },
    {
        "symbol": "XAUUSD",
        "display_name": "XAU/USD",
        "pip_value": 0.01,
        "spread_limit": 50.0,
        "lot_size": DEFAULT_LOT_SIZE,
        "sl_pips": 100,
        "tp_pips": 150,
    },
]

# ─── Technical Analysis Timeframes ──────────────────────────
TIMEFRAMES = {
    "M5": 5,
    "M15": 15,
    "H1": 60,
    "H4": 240,
    "D1": 1440,
}

# ─── Logging ─────────────────────────────────────────────────
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
