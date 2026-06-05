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

# ─── Simbol & Timeframe ────────────────────────────────
SYMBOL          = os.getenv("SYMBOL", "EURUSD")
if HAS_MT5 and mt5 is not None:
    TF_ENTRY    = mt5.TIMEFRAME_M5    # M5 untuk entry
    TF_TREND    = mt5.TIMEFRAME_M15   # M15 untuk filter trend
else:
    TF_ENTRY    = 5
    TF_TREND    = 15
MAGIC_NUMBER    = 20240501            # ID unik EA scalping

# ─── Parameter Scalping ────────────────────────────────
TP_PIPS         = int(os.getenv("TP_PIPS", 10))        # Target 5-15 pips
SL_PIPS         = int(os.getenv("SL_PIPS", 8))         # Stop loss 8-12 pips
BREAKEVEN_PIPS  = int(os.getenv("BREAKEVEN_PIPS", 5))  # Geser SL ke BE setelah +5p
TRAILING_START  = int(os.getenv("TRAILING_START_PIPS", 7))   # Mulai trailing
TRAILING_STEP   = int(os.getenv("TRAILING_STEP_PIPS", 3))    # Langkah trailing

# ─── Risk Management ───────────────────────────────────
MAX_RISK_PERCENT = float(os.getenv("MAX_RISK_PERCENT", 0.5))  # 0.5% per trade
MAX_OPEN_TRADES  = int(os.getenv("MAX_OPEN_TRADES", 2))
MAX_SPREAD_PIPS  = float(os.getenv("MAX_SPREAD_PIPS", 2.0))  # Reject jika spread > 2p
LOT_SIZE         = float(os.getenv("LOT_SIZE", 0.01))

# ─── Indikator M5 (Entry) ──────────────────────────────
EMA_FAST_M5      = 9     # EMA cepat untuk entry
EMA_SLOW_M5      = 21    # EMA lambat untuk entry
RSI_PERIOD_M5    = 7     # RSI lebih pendek untuk scalping
RSI_OB           = 70    # Overbought
RSI_OS           = 30    # Oversold
STOCH_K          = 5     # Stochastic %K
STOCH_D          = 3     # Stochastic %D
STOCH_SMOOTH     = 3
STOCH_OB         = 80    # Stoch overbought
STOCH_OS         = 20    # Stoch oversold
BB_PERIOD        = 20    # Bollinger Bands

# ─── Indikator M15 (Trend Filter) ──────────────────────
EMA_MID_M15      = 50    # Trend menengah
EMA_TREND_M15    = 200   # Trend utama

# ─── Session Trading (UTC+0) ───────────────────────────
LONDON_OPEN      = "07:00"
LONDON_CLOSE     = "16:00"
NY_OPEN          = "12:00"
NY_CLOSE         = "20:00"
OVERLAP_START    = "12:00"  # London-NY overlap (paling aktif)
OVERLAP_END      = "16:00"

# ─── Telegram ──────────────────────────────────────────
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID", "")

# ─── Format Currency Utility ───────────────────────────
ACCOUNT_CURRENCY = os.getenv("ACCOUNT_CURRENCY", "USD").upper()

def format_currency(value: float) -> str:
    """Format nilai mata uang."""
    if ACCOUNT_CURRENCY in ["IDR", "RP"]:
        return f"Rp {value:,.0f}".replace(",", ".")
    else:
        return f"${value:,.2f}" if ACCOUNT_CURRENCY == "USD" else f"{ACCOUNT_CURRENCY} {value:,.2f}"

