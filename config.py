import os
from dotenv import load_dotenv

load_dotenv()

# Try to import MetaTrader5, handle gracefully on non-Windows platforms
try:
    import MetaTrader5 as mt5
    HAS_MT5 = True
except ImportError:
    mt5 = None
    HAS_MT5 = False

# ─── Koneksi MT5 ───────────────────────────────────────
MT5_CONFIG = {
    "login":    int(os.getenv("MT5_LOGIN", 0)),
    "password": os.getenv("MT5_PASSWORD", ""),
    "server":   os.getenv("MT5_SERVER", ""),
}

# Timeframe mapping helper for fallbacks
TIMEFRAME_MAP = {
    "M1": 1,
    "M2": 2,
    "M3": 3,
    "M4": 4,
    "M5": 5,
    "M6": 6,
    "M10": 10,
    "M12": 12,
    "M15": 15,
    "M20": 20,
    "M30": 30,
    "H1": 16385,
    "H2": 16386,
    "H3": 16387,
    "H4": 16388,
    "H6": 16390,
    "H8": 16392,
    "H12": 16396,
    "D1": 16408,
    "W1": 32769,
    "MN1": 49153
}

tf_str = os.getenv("TIMEFRAME", "H1").upper()

if HAS_MT5:
    TIMEFRAME = getattr(mt5, f"TIMEFRAME_{tf_str}", mt5.TIMEFRAME_H1)
else:
    TIMEFRAME = TIMEFRAME_MAP.get(tf_str, 16385)

# ─── Parameter Trading ─────────────────────────────────
SYMBOL           = os.getenv("SYMBOL", "EURUSD")
LOT_SIZE         = float(os.getenv("LOT_SIZE", 0.01))
MAGIC_NUMBER     = 20240101                  # ID unik EA
ACCOUNT_CURRENCY = os.getenv("ACCOUNT_CURRENCY", "IDR").upper()

def format_currency(value: float) -> str:
    """Format nilai mata uang berdasarkan IDR atau mata uang lainnya."""
    if ACCOUNT_CURRENCY in ["IDR", "RP"]:
        # Standard Indonesian formatting e.g., Rp 10.000 (no decimals for IDR)
        return f"Rp {value:,.0f}".replace(",", ".")
    else:
        return f"${value:,.2f}" if ACCOUNT_CURRENCY == "USD" else f"{ACCOUNT_CURRENCY} {value:,.2f}"

# ─── Risk Management ───────────────────────────────────
MAX_RISK_PERCENT  = float(os.getenv("MAX_RISK_PERCENT", 1.0))

MAX_OPEN_TRADES   = int(os.getenv("MAX_OPEN_TRADES", 3))
STOP_LOSS_PIPS    = 50
TAKE_PROFIT_PIPS  = 100
TRAILING_STOP     = True
TRAILING_PIPS     = 20

# ─── Parameter Indikator ───────────────────────────────
EMA_FAST     = 21
EMA_SLOW     = 50
EMA_TREND    = 200
RSI_PERIOD   = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD   = 30
MACD_FAST    = 12
MACD_SLOW    = 26
MACD_SIGNAL  = 9
BB_PERIOD    = 20
BB_STD       = 2.0

# ─── Jadwal Trading ────────────────────────────────────
TRADING_SESSIONS = {
    "london":   {"start": "08:00", "end": "16:00"},
    "new_york": {"start": "13:00", "end": "21:00"},
}
AVOID_NEWS_MINUTES = 30   # Hindari 30 menit sebelum/sesudah berita

# ─── Telegram ──────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")
