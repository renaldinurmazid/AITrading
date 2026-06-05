# ⚡ EA Scalping Forex — Python + MetaTrader 5
### Strategi Scalping M5 & M15 | Target 5–15 Pips Per Trade

> **Stack:** Python 3.10+ · MetaTrader 5 · `MetaTrader5` library · `pandas` · `ta`
> **Timeframe:** M5 (entry) + M15 (konfirmasi trend)
> **Target:** 5–15 pips per trade | SL: 8–12 pips | R:R minimal 1:1.2

---

## 📋 Daftar Isi

1. [Filosofi Scalping](#filosofi-scalping)
2. [Arsitektur Sistem](#arsitektur-sistem)
3. [Persyaratan & Instalasi](#persyaratan--instalasi)
4. [Struktur Folder Proyek](#struktur-folder-proyek)
5. [Konfigurasi EA Scalping](#konfigurasi-ea-scalping)
6. [Kode Lengkap](#kode-lengkap)
7. [Strategi & Logika Signal](#strategi--logika-signal)
8. [Risk Management Scalping](#risk-management-scalping)
9. [Session Filter](#session-filter)
10. [Notifikasi Telegram](#notifikasi-telegram)
11. [Cara Menjalankan](#cara-menjalankan)
12. [Tips Scalping Profesional](#tips-scalping-profesional)
13. [Troubleshooting](#troubleshooting)

---

## 🎯 Filosofi Scalping

```
Scalping M5/M15 bukan soal menangkap trend panjang,
tapi menangkap MOMENTUM SESAAT dengan presisi tinggi.

Prinsip utama:
  ✓ Masuk cepat, keluar lebih cepat
  ✓ Spread rendah = wajib pair mayor (EURUSD, GBPUSD)
  ✓ Hanya trading di jam London & New York (likuiditas tinggi)
  ✓ Hindari berita besar (NFP, CPI, FOMC)
  ✓ SL ketat 8-12 pips, TP realistis 5-15 pips
  ✓ Frekuensi tinggi, profit per-trade kecil
```

### Pair yang Direkomendasikan

| Pair | Spread Avg | Volatilitas | Rekomendasi |
|------|-----------|-------------|-------------|
| EURUSD | 0.1–0.3 pip | Sedang | ⭐⭐⭐ Terbaik |
| GBPUSD | 0.3–0.5 pip | Tinggi | ⭐⭐⭐ Bagus |
| USDJPY | 0.2–0.4 pip | Sedang | ⭐⭐⭐ Bagus |
| GBPJPY | 0.5–1.0 pip | Sangat Tinggi | ⭐⭐ Hati-hati |
| AUDUSD | 0.3–0.5 pip | Rendah | ⭐⭐ Cukup |

---

## 🏗️ Arsitektur Sistem

```
┌──────────────────────────────────────────────────────────────┐
│                  EA SCALPING SYSTEM                          │
│                                                              │
│   M15 Candle ──► Trend Filter (EMA 50/200)                  │
│        │                │                                    │
│        ▼                ▼                                    │
│   M5 Candle  ──► Signal Generator ──► Session Filter        │
│        │         (EMA9/21 + RSI +      (London/NY only)     │
│        │          Stoch + BB)                │               │
│        │                                    ▼               │
│        └──────────────────────► Spread Check (< 3 pips)     │
│                                             │               │
│                                             ▼               │
│                                    Risk Manager             │
│                                  (Lot + SL 8-12p            │
│                                   + TP 5-15p)               │
│                                             │               │
│                                             ▼               │
│                                     MT5 Order Send          │
│                                             │               │
│                                             ▼               │
│                                   Telegram Notifikasi       │
└──────────────────────────────────────────────────────────────┘
```

**Dual Timeframe Logic:**
- **M15** → Filter arah trend utama (EMA 50 & 200)
- **M5** → Entry signal presisi (EMA 9/21 crossover + konfirmasi)

---

## ⚙️ Persyaratan & Instalasi

### 1. Install Python Libraries

```bash
pip install MetaTrader5
pip install pandas numpy
pip install ta
pip install requests
pip install python-dotenv
pip install schedule
pip install colorlog
```

### 2. Setup MetaTrader 5

- Install MT5 dari broker
- Gunakan broker dengan **spread EURUSD < 1 pip** (ECN/STP)
- Aktifkan Algo Trading: `Tools → Options → Expert Advisors`
- Centang **Allow automated trading** dan **Allow DLL imports**
- Pastikan MT5 **aktif** saat EA berjalan

### 3. Broker yang Direkomendasikan untuk Scalping

| Broker | Tipe | Spread EURUSD | Eksekusi |
|--------|------|--------------|---------|
| IC Markets | ECN | 0.0–0.1 pip | Market |
| Pepperstone | ECN | 0.0–0.1 pip | Market |
| FP Markets | ECN | 0.0–0.2 pip | Market |

> ⚠️ Hindari broker STP/Market Maker dengan spread > 1.5 pip untuk scalping

### 4. File `.env`

```env
MT5_LOGIN=12345678
MT5_PASSWORD=YourPassword
MT5_SERVER=ICMarkets-Demo

# Simbol utama scalping
SYMBOL=EURUSD
TIMEFRAME_ENTRY=M5
TIMEFRAME_TREND=M15

# Lot & Risk
LOT_SIZE=0.01
MAX_RISK_PERCENT=0.5
MAX_OPEN_TRADES=2
MAX_SPREAD_PIPS=2.0

# Target Scalping
TP_PIPS=10
SL_PIPS=8
BREAKEVEN_PIPS=5
TRAILING_START_PIPS=7
TRAILING_STEP_PIPS=3

# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

---

## 📁 Struktur Folder Proyek

```
scalping_ea/
├── main.py                     # Entry point
├── config.py                   # Semua parameter scalping
├── .env                        # Kredensial (jangan di-commit!)
├── requirements.txt
│
├── core/
│   ├── connector.py            # Koneksi MT5
│   ├── trader.py               # Eksekusi & manage order
│   └── monitor.py              # Monitor & breakeven management
│
├── strategy/
│   ├── indicators.py           # Indikator M5 & M15
│   ├── signals.py              # Logic signal scalping
│   └── session_filter.py       # Filter jam trading
│
├── risk/
│   └── manager.py              # Risk & lot calculation
│
├── utils/
│   ├── logger.py
│   └── notifier.py             # Telegram alerts
│
└── logs/
    └── scalping_ea.log
```

---

## 🔧 Konfigurasi EA Scalping

### `config.py`

```python
import os
from dotenv import load_dotenv
import MetaTrader5 as mt5

load_dotenv()

# ─── Koneksi MT5 ───────────────────────────────────────
MT5_CONFIG = {
    "login":    int(os.getenv("MT5_LOGIN", 0)),
    "password": os.getenv("MT5_PASSWORD", ""),
    "server":   os.getenv("MT5_SERVER", ""),
}

# ─── Simbol & Timeframe ────────────────────────────────
SYMBOL          = os.getenv("SYMBOL", "EURUSD")
TF_ENTRY        = mt5.TIMEFRAME_M5    # M5 untuk entry
TF_TREND        = mt5.TIMEFRAME_M15   # M15 untuk filter trend
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
```

---

## 💻 Kode Lengkap

### `strategy/indicators.py` — Indikator Dual Timeframe

```python
import pandas as pd
import MetaTrader5 as mt5
from ta.trend import EMAIndicator, MACD
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands, AverageTrueRange
from config import *

def get_candles(symbol: str, timeframe, n: int = 150) -> pd.DataFrame:
    """Ambil data OHLCV dari MT5."""
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, n)
    if rates is None or len(rates) == 0:
        return pd.DataFrame()
    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df.set_index("time", inplace=True)
    df.rename(columns={
        "open": "Open", "high": "High",
        "low": "Low", "close": "Close",
        "tick_volume": "Volume"
    }, inplace=True)
    return df

def calculate_m5_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Hitung indikator untuk M5 (entry signal).
    Indikator: EMA 9/21, RSI 7, Stochastic 5/3/3, Bollinger Bands 20, ATR 7
    """
    if df.empty or len(df) < 30:
        return df

    close = df["Close"]
    high  = df["High"]
    low   = df["Low"]

    # ── EMA Fast & Slow ────────────────────────────────
    df["ema_fast"] = EMAIndicator(close, window=EMA_FAST_M5).ema_indicator()
    df["ema_slow"] = EMAIndicator(close, window=EMA_SLOW_M5).ema_indicator()

    # ── RSI Pendek (lebih sensitif untuk scalping) ─────
    df["rsi"] = RSIIndicator(close, window=RSI_PERIOD_M5).rsi()

    # ── Stochastic Oscillator ──────────────────────────
    stoch = StochasticOscillator(
        high=high, low=low, close=close,
        window=STOCH_K, smooth_window=STOCH_D
    )
    df["stoch_k"] = stoch.stoch()
    df["stoch_d"] = stoch.stoch_signal()

    # ── Bollinger Bands ────────────────────────────────
    bb = BollingerBands(close, window=BB_PERIOD, window_dev=2)
    df["bb_upper"] = bb.bollinger_hband()
    df["bb_lower"] = bb.bollinger_lband()
    df["bb_mid"]   = bb.bollinger_mavg()
    df["bb_pct"]   = bb.bollinger_pband()  # 0=lower, 1=upper

    # ── ATR untuk filter volatilitas ───────────────────
    df["atr"] = AverageTrueRange(high, low, close, window=7).average_true_range()

    # ── EMA Crossover ──────────────────────────────────
    df["cross_up"]   = (df["ema_fast"] > df["ema_slow"]) & \
                       (df["ema_fast"].shift(1) <= df["ema_slow"].shift(1))
    df["cross_down"] = (df["ema_fast"] < df["ema_slow"]) & \
                       (df["ema_fast"].shift(1) >= df["ema_slow"].shift(1))

    return df

def calculate_m15_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Hitung indikator untuk M15 (trend filter).
    Hanya butuh EMA 50 & 200 untuk menentukan arah trend.
    """
    if df.empty or len(df) < 210:
        return df

    close = df["Close"]
    df["ema_mid"]   = EMAIndicator(close, window=EMA_MID_M15).ema_indicator()
    df["ema_trend"] = EMAIndicator(close, window=EMA_TREND_M15).ema_indicator()

    df["trend_bull"] = df["ema_mid"] > df["ema_trend"]
    df["trend_bear"] = df["ema_mid"] < df["ema_trend"]

    return df

def get_trend_direction(symbol: str) -> str:
    """Ambil arah trend dari M15."""
    df_m15 = get_candles(symbol, TF_TREND, n=220)
    if df_m15.empty:
        return "NEUTRAL"

    df_m15 = calculate_m15_indicators(df_m15)
    if df_m15.empty:
        return "NEUTRAL"

    last = df_m15.iloc[-1]
    if last["trend_bull"]:
        return "BULL"
    elif last["trend_bear"]:
        return "BEAR"
    return "NEUTRAL"
```

---

### `strategy/signals.py` — Signal Scalping

```python
import pandas as pd
import logging
from config import *

logger = logging.getLogger(__name__)

class ScalpingSignal:
    """
    Strategi Scalping Dual Timeframe:

    ─── SETUP BUY ───────────────────────────────────────
    1. M15: EMA 50 > EMA 200  → trend BULLISH
    2. M5:  EMA 9 crossover ke atas EMA 21
    3. M5:  RSI 7 antara 40–65 (momentum naik, belum OB)
    4. M5:  Stochastic %K < 80 dan sedang naik
    5. M5:  Harga di atas BB midline
    6. M5:  ATR > minimum (ada volatilitas cukup)

    ─── SETUP SELL ──────────────────────────────────────
    1. M15: EMA 50 < EMA 200  → trend BEARISH
    2. M5:  EMA 9 crossover ke bawah EMA 21
    3. M5:  RSI 7 antara 35–60 (momentum turun, belum OS)
    4. M5:  Stochastic %K > 20 dan sedang turun
    5. M5:  Harga di bawah BB midline
    6. M5:  ATR > minimum (ada volatilitas cukup)
    """

    def __init__(self):
        self.MIN_ATR_PIPS = 3   # Minimal 3 pip ATR agar worth scalping

    def get_signal(self, df_m5: pd.DataFrame, trend: str) -> str:
        """
        Evaluasi signal scalping.
        Return: 'BUY', 'SELL', atau 'HOLD'
        """
        if df_m5.empty or len(df_m5) < 25:
            return "HOLD"

        cur  = df_m5.iloc[-1]
        prev = df_m5.iloc[-2]

        # ── Filter ATR (volatilitas minimum) ──────────
        sym   = __import__('MetaTrader5', fromlist=['symbol_info']).symbol_info(SYMBOL)
        point = sym.point if sym else 0.00001
        pip   = 10 * point
        atr_pips = cur["atr"] / pip

        if atr_pips < self.MIN_ATR_PIPS:
            logger.debug(f"ATR terlalu kecil: {atr_pips:.1f} pips — HOLD")
            return "HOLD"

        # ── Signal BUY ─────────────────────────────────
        if trend == "BULL":
            buy_score = 0
            buy_score += 1 if cur["cross_up"] else 0                   # EMA crossover
            buy_score += 1 if 40 <= cur["rsi"] <= 65 else 0            # RSI zona
            buy_score += 1 if cur["stoch_k"] < STOCH_OB else 0         # Stoch belum OB
            buy_score += 1 if cur["stoch_k"] > cur["stoch_d"] else 0   # Stoch naik
            buy_score += 1 if cur["Close"] > cur["bb_mid"] else 0       # Di atas BB mid
            buy_score += 1 if cur["ema_fast"] > cur["ema_slow"] else 0 # EMA alignment

            logger.debug(f"[BUY] Score: {buy_score}/6 | RSI: {cur['rsi']:.1f} | "
                         f"Stoch: {cur['stoch_k']:.1f} | ATR: {atr_pips:.1f}p")

            # Minimal 4/6 kondisi + wajib ada crossover
            if buy_score >= 4 and cur["cross_up"]:
                logger.info(f"⚡ SCALP BUY | Score: {buy_score}/6 | "
                            f"RSI: {cur['rsi']:.1f} | ATR: {atr_pips:.1f}p")
                return "BUY"

        # ── Signal SELL ────────────────────────────────
        elif trend == "BEAR":
            sell_score = 0
            sell_score += 1 if cur["cross_down"] else 0                # EMA crossover
            sell_score += 1 if 35 <= cur["rsi"] <= 60 else 0           # RSI zona
            sell_score += 1 if cur["stoch_k"] > STOCH_OS else 0        # Stoch belum OS
            sell_score += 1 if cur["stoch_k"] < cur["stoch_d"] else 0  # Stoch turun
            sell_score += 1 if cur["Close"] < cur["bb_mid"] else 0      # Di bawah BB mid
            sell_score += 1 if cur["ema_fast"] < cur["ema_slow"] else 0 # EMA alignment

            logger.debug(f"[SELL] Score: {sell_score}/6 | RSI: {cur['rsi']:.1f} | "
                         f"Stoch: {cur['stoch_k']:.1f} | ATR: {atr_pips:.1f}p")

            if sell_score >= 4 and cur["cross_down"]:
                logger.info(f"⚡ SCALP SELL | Score: {sell_score}/6 | "
                            f"RSI: {cur['rsi']:.1f} | ATR: {atr_pips:.1f}p")
                return "SELL"

        return "HOLD"

    def get_market_snapshot(self, df_m5: pd.DataFrame, trend: str) -> dict:
        """Ambil snapshot kondisi pasar untuk logging & Telegram."""
        if df_m5.empty:
            return {}
        cur = df_m5.iloc[-1]
        return {
            "trend_m15": trend,
            "rsi":       round(cur.get("rsi", 0), 1),
            "stoch_k":   round(cur.get("stoch_k", 0), 1),
            "stoch_d":   round(cur.get("stoch_d", 0), 1),
            "bb_pct":    round(cur.get("bb_pct", 0), 2),
            "ema_cross": "UP" if cur.get("cross_up") else
                         "DOWN" if cur.get("cross_down") else "NONE",
        }
```

---

### `strategy/session_filter.py` — Filter Jam Trading

```python
from datetime import datetime, time
import pytz
import logging
from config import *

logger = logging.getLogger(__name__)

# Jam berita besar yang harus dihindari (UTC)
# Update manual atau integrasikan dengan API kalender ekonomi
HIGH_IMPACT_TIMES = [
    # Format: (HH, MM, "Nama Event")
    # Contoh waktu tetap — update tiap minggu
    # (13, 30, "NFP"),
    # (14, 00, "FOMC"),
]

class SessionFilter:
    """Filter trading berdasarkan sesi pasar dan jam berita."""

    def __init__(self):
        self.utc = pytz.utc

    def get_utc_now(self) -> datetime:
        return datetime.now(self.utc)

    def is_london_session(self) -> bool:
        now = self.get_utc_now().time()
        return time(7, 0) <= now <= time(16, 0)

    def is_ny_session(self) -> bool:
        now = self.get_utc_now().time()
        return time(12, 0) <= now <= time(20, 0)

    def is_overlap_session(self) -> bool:
        """London-NY overlap: jam paling aktif dan likuid."""
        now = self.get_utc_now().time()
        return time(12, 0) <= now <= time(16, 0)

    def is_asian_session(self) -> bool:
        """Sesi Asia — hindari untuk scalping (spread lebar, range sempit)."""
        now = self.get_utc_now().time()
        return time(0, 0) <= now < time(7, 0)

    def is_near_high_impact_news(self, buffer_minutes: int = 30) -> tuple:
        """
        Cek apakah dalam rentang waktu berita high impact.
        Return: (bool, nama_event)
        """
        now = self.get_utc_now()
        for hour, minute, name in HIGH_IMPACT_TIMES:
            news_time = now.replace(hour=hour, minute=minute, second=0)
            diff = abs((now - news_time).total_seconds() / 60)
            if diff <= buffer_minutes:
                return True, name
        return False, ""

    def is_friday_close(self) -> bool:
        """Hindari 2 jam sebelum penutupan pasar Jumat (21:00 UTC)."""
        now = self.get_utc_now()
        return now.weekday() == 4 and now.hour >= 19

    def is_monday_open(self) -> bool:
        """Hindari 1 jam pertama pasar Senin (gap risk)."""
        now = self.get_utc_now()
        return now.weekday() == 0 and now.hour < 1

    def can_trade(self) -> tuple:
        """
        Validasi semua kondisi waktu trading.
        Return: (bool, alasan)
        """
        # Jangan trade sesi Asia
        if self.is_asian_session():
            return False, "Sesi Asia — spread lebar, skip"

        # Jangan trade Jumat malam
        if self.is_friday_close():
            return False, "Jumat close — hindari gap akhir pekan"

        # Jangan trade Senin dini hari
        if self.is_monday_open():
            return False, "Senin open — gap risk tinggi"

        # Cek berita besar
        near_news, event_name = self.is_near_high_impact_news()
        if near_news:
            return False, f"Dekat berita {event_name} — trading dihentikan"

        # Harus di sesi London atau NY
        if not (self.is_london_session() or self.is_ny_session()):
            return False, "Di luar jam London & NY"

        # Prioritas: overlap sesi
        session = "OVERLAP ⭐" if self.is_overlap_session() else \
                  "LONDON" if self.is_london_session() else "NEW YORK"
        return True, f"Sesi {session} — trading aktif"
```

---

### `risk/manager.py` — Risk Management Scalping

```python
import MetaTrader5 as mt5
import math
import logging
from config import *

logger = logging.getLogger(__name__)

class ScalpingRiskManager:
    """
    Risk management khusus scalping:
    - Lot berbasis % risk dari balance
    - SL fixed 8-12 pips
    - TP 5-15 pips (R:R minimal 1:1.2)
    - Breakeven otomatis setelah +5 pips
    - Max 2 posisi simultan
    """

    def check_spread(self, symbol: str) -> tuple:
        """
        Cek apakah spread saat ini acceptable untuk scalping.
        Tolak jika spread > MAX_SPREAD_PIPS.
        """
        tick = mt5.symbol_info_tick(symbol)
        sym  = mt5.symbol_info(symbol)
        if not tick or not sym:
            return False, 99.0

        spread_pips = sym.spread / 10  # Convert points ke pips
        if spread_pips > MAX_SPREAD_PIPS:
            logger.warning(f"⚠️ Spread terlalu lebar: {spread_pips:.1f} pips > {MAX_SPREAD_PIPS} pips")
            return False, spread_pips

        return True, spread_pips

    def calculate_lot(self, symbol: str, sl_pips: float) -> float:
        """
        Hitung lot size berdasarkan max risk per trade.
        Untuk scalping: biasanya 0.5% dari balance.
        """
        acc     = mt5.account_info()
        sym     = mt5.symbol_info(symbol)
        if not acc or not sym:
            return sym.volume_min if sym else 0.01

        risk_money     = acc.balance * (MAX_RISK_PERCENT / 100)
        pip_value      = sym.trade_tick_value
        pip_val_per_lot = pip_value * 10

        lot = risk_money / (sl_pips * pip_val_per_lot)
        lot = math.floor(lot / sym.volume_step) * sym.volume_step
        lot = max(sym.volume_min, min(lot, sym.volume_max))
        lot = round(lot, 2)

        logger.info(f"📦 Lot Size | Balance: ${acc.balance:.0f} | "
                    f"Risk: ${risk_money:.2f} ({MAX_RISK_PERCENT}%) | "
                    f"SL: {sl_pips}p | Lot: {lot}")
        return lot

    def get_sl_tp(self, symbol: str, signal: str,
                  price: float) -> tuple:
        """
        Hitung level SL dan TP dalam harga aktual.
        SL: 8 pips | TP: 10 pips (R:R = 1:1.25)
        """
        sym   = mt5.symbol_info(symbol)
        point = sym.point
        pip   = 10 * point

        sl_price = tp_price = 0.0
        if signal == "BUY":
            sl_price = round(price - SL_PIPS * pip, sym.digits)
            tp_price = round(price + TP_PIPS * pip, sym.digits)
        elif signal == "SELL":
            sl_price = round(price + SL_PIPS * pip, sym.digits)
            tp_price = round(price - TP_PIPS * pip, sym.digits)

        rr = round(TP_PIPS / SL_PIPS, 2)
        logger.info(f"🎯 SL: {sl_price} ({SL_PIPS}p) | TP: {tp_price} ({TP_PIPS}p) | R:R 1:{rr}")
        return sl_price, tp_price

    def count_open_trades(self) -> int:
        positions = mt5.positions_get(magic=MAGIC_NUMBER)
        return len(positions) if positions else 0

    def is_trade_allowed(self, symbol: str) -> tuple:
        """Validasi semua kondisi sebelum buka posisi."""
        # Cek max trades
        open_t = self.count_open_trades()
        if open_t >= MAX_OPEN_TRADES:
            return False, f"Max {MAX_OPEN_TRADES} posisi terbuka"

        # Cek spread
        spread_ok, spread_val = self.check_spread(symbol)
        if not spread_ok:
            return False, f"Spread {spread_val:.1f}p terlalu lebar"

        # Cek margin
        acc = mt5.account_info()
        if acc.margin_level > 0 and acc.margin_level < 200:
            return False, f"Margin level rendah: {acc.margin_level:.0f}%"

        return True, f"OK | Spread: {spread_val:.1f}p | Posisi: {open_t}/{MAX_OPEN_TRADES}"
```

---

### `core/trader.py` — Eksekusi & Manajemen Order

```python
import MetaTrader5 as mt5
import logging
from config import *

logger = logging.getLogger(__name__)

class ScalpingTrader:
    """Eksekusi order scalping dengan manajemen breakeven & trailing stop."""

    def open_trade(self, symbol: str, signal: str, lot: float,
                   sl: float, tp: float) -> dict:
        """Buka posisi scalping baru."""
        tick = mt5.symbol_info_tick(symbol)
        sym  = mt5.symbol_info(symbol)
        if not tick or not sym:
            return {}

        if signal == "BUY":
            order_type = mt5.ORDER_TYPE_BUY
            price      = tick.ask
        elif signal == "SELL":
            order_type = mt5.ORDER_TYPE_SELL
            price      = tick.bid
        else:
            return {}

        request = {
            "action":       mt5.TRADE_ACTION_DEAL,
            "symbol":       symbol,
            "volume":       lot,
            "type":         order_type,
            "price":        price,
            "sl":           sl,
            "tp":           tp,
            "deviation":    10,           # Scalping butuh eksekusi ketat
            "magic":        MAGIC_NUMBER,
            "comment":      f"SCALP-{signal[:1]}",
            "type_time":    mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            logger.info(f"✅ SCALP {signal} OPEN | Ticket: {result.order} | "
                        f"Price: {price} | SL: {sl} | TP: {tp} | Lot: {lot}")
            return {
                "ticket": result.order,
                "signal": signal,
                "price":  price,
                "sl": sl, "tp": tp,
                "lot": lot,
            }

        logger.error(f"❌ Order gagal [{result.retcode}]: {result.comment}")
        return {}

    def manage_breakeven(self, symbol: str):
        """
        Geser SL ke breakeven (harga entry) setelah profit BREAKEVEN_PIPS.
        Ini melindungi profit awal dari scalping.
        """
        positions = mt5.positions_get(symbol=symbol)
        if not positions:
            return

        sym   = mt5.symbol_info(symbol)
        tick  = mt5.symbol_info_tick(symbol)
        point = sym.point
        pip   = 10 * point

        for pos in positions:
            if pos.magic != MAGIC_NUMBER:
                continue

            entry      = pos.price_open
            current_p  = tick.bid if pos.type == 0 else tick.ask
            profit_pips = 0

            if pos.type == 0:   # BUY
                profit_pips = (current_p - entry) / pip
                if profit_pips >= BREAKEVEN_PIPS and pos.sl < entry:
                    new_sl = round(entry + 1 * pip, sym.digits)  # BE +1 pip
                    self._modify_sl_tp(pos.ticket, new_sl, pos.tp)
                    logger.info(f"🔒 BREAKEVEN | Ticket: {pos.ticket} | "
                                f"Profit: {profit_pips:.1f}p | SL → {new_sl}")

            elif pos.type == 1:  # SELL
                profit_pips = (entry - current_p) / pip
                if profit_pips >= BREAKEVEN_PIPS and (pos.sl > entry or pos.sl == 0):
                    new_sl = round(entry - 1 * pip, sym.digits)  # BE -1 pip
                    self._modify_sl_tp(pos.ticket, new_sl, pos.tp)
                    logger.info(f"🔒 BREAKEVEN | Ticket: {pos.ticket} | "
                                f"Profit: {profit_pips:.1f}p | SL → {new_sl}")

    def manage_trailing_stop(self, symbol: str):
        """
        Trailing stop aktif setelah profit TRAILING_START pips.
        Geser SL setiap TRAILING_STEP pips mengikuti harga.
        """
        positions = mt5.positions_get(symbol=symbol)
        if not positions:
            return

        sym   = mt5.symbol_info(symbol)
        tick  = mt5.symbol_info_tick(symbol)
        point = sym.point
        pip   = 10 * point

        for pos in positions:
            if pos.magic != MAGIC_NUMBER:
                continue

            entry = pos.price_open

            if pos.type == 0:   # BUY
                current   = tick.bid
                profit_p  = (current - entry) / pip
                if profit_p >= TRAILING_START:
                    new_sl = round(current - TRAILING_STEP * pip, sym.digits)
                    if new_sl > pos.sl:
                        self._modify_sl_tp(pos.ticket, new_sl, pos.tp)
                        logger.debug(f"🔄 TRAIL BUY | Ticket: {pos.ticket} | "
                                     f"SL: {pos.sl} → {new_sl}")

            elif pos.type == 1:  # SELL
                current   = tick.ask
                profit_p  = (entry - current) / pip
                if profit_p >= TRAILING_START:
                    new_sl = round(current + TRAILING_STEP * pip, sym.digits)
                    if new_sl < pos.sl or pos.sl == 0:
                        self._modify_sl_tp(pos.ticket, new_sl, pos.tp)
                        logger.debug(f"🔄 TRAIL SELL | Ticket: {pos.ticket} | "
                                     f"SL: {pos.sl} → {new_sl}")

    def _modify_sl_tp(self, ticket: int, sl: float, tp: float):
        request = {
            "action":   mt5.TRADE_ACTION_SLTP,
            "position": ticket,
            "sl":       sl,
            "tp":       tp,
        }
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.warning(f"Gagal modify SL/TP [{result.retcode}]: {result.comment}")

    def close_all_positions(self, symbol: str, reason: str = "EA-Close"):
        """Tutup semua posisi (dipakai saat sesi tutup atau darurat)."""
        positions = mt5.positions_get(symbol=symbol)
        if not positions:
            return

        for pos in positions:
            if pos.magic != MAGIC_NUMBER:
                continue
            tick = mt5.symbol_info_tick(symbol)
            close_type  = mt5.ORDER_TYPE_SELL if pos.type == 0 \
                          else mt5.ORDER_TYPE_BUY
            close_price = tick.bid if pos.type == 0 else tick.ask
            request = {
                "action":       mt5.TRADE_ACTION_DEAL,
                "symbol":       symbol,
                "volume":       pos.volume,
                "type":         close_type,
                "position":     pos.ticket,
                "price":        close_price,
                "deviation":    10,
                "magic":        MAGIC_NUMBER,
                "comment":      reason,
                "type_time":    mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            result = mt5.order_send(request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                logger.info(f"✅ Posisi {pos.ticket} ditutup | "
                            f"Profit: ${pos.profit:.2f} | Alasan: {reason}")
```

---

### `utils/notifier.py` — Telegram Alert Scalping

```python
import requests
import logging
from datetime import datetime
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)

class TelegramNotifier:

    BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

    def send(self, text: str) -> bool:
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            return False
        try:
            resp = requests.post(
                f"{self.BASE_URL}/sendMessage",
                json={"chat_id": TELEGRAM_CHAT_ID,
                      "text": text, "parse_mode": "HTML"},
                timeout=8
            )
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"Telegram error: {e}")
            return False

    def alert_trade_open(self, signal: str, symbol: str, price: float,
                         sl: float, tp: float, lot: float,
                         ticket: int, spread: float, session: str):
        e = "🟢" if signal == "BUY" else "🔴"
        sl_p = abs(round((price - sl) / 0.0001))
        tp_p = abs(round((tp - price) / 0.0001))
        rr   = round(tp_p / sl_p, 1) if sl_p else 0
        now  = datetime.utcnow().strftime("%H:%M:%S UTC")

        msg = (
            f"{e} <b>SCALP {signal} — {symbol}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⏰ Waktu   : <code>{now}</code>\n"
            f"📍 Sesi    : <code>{session}</code>\n"
            f"💵 Entry   : <code>{price}</code>\n"
            f"🛡️ SL      : <code>{sl}</code> ({sl_p}p)\n"
            f"🎯 TP      : <code>{tp}</code> ({tp_p}p)\n"
            f"⚖️ R:R     : <code>1:{rr}</code>\n"
            f"📦 Lot     : <code>{lot}</code>\n"
            f"📊 Spread  : <code>{spread:.1f} pips</code>\n"
            f"🎫 Ticket  : <code>{ticket}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚡ <i>EA Scalping Python</i>"
        )
        self.send(msg)

    def alert_trade_close(self, ticket: int, symbol: str,
                          profit: float, pips: float, reason: str):
        e = "✅" if profit >= 0 else "❌"
        msg = (
            f"{e} <b>SCALP CLOSE — {symbol}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎫 Ticket  : <code>{ticket}</code>\n"
            f"📐 Pips    : <code>{pips:+.1f}</code>\n"
            f"💰 Profit  : <code>${profit:+.2f}</code>\n"
            f"📋 Alasan  : <code>{reason}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━"
        )
        self.send(msg)

    def alert_session_start(self, session: str, symbol: str,
                             spread: float, trend: str):
        msg = (
            f"🚀 <b>SESI TRADING DIMULAI</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🌍 Sesi    : <b>{session}</b>\n"
            f"📌 Simbol  : <b>{symbol}</b>\n"
            f"📊 Spread  : <code>{spread:.1f} pips</code>\n"
            f"📈 Trend   : <code>{trend}</code>\n"
            f"⚡ EA Scalping siap berburu pip!"
        )
        self.send(msg)

    def alert_daily_summary(self, balance: float, profit: float,
                             trades: int, wins: int):
        win_rate = round(wins / trades * 100, 1) if trades else 0
        e = "📈" if profit >= 0 else "📉"
        msg = (
            f"{e} <b>RINGKASAN HARIAN</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💼 Balance   : <code>${balance:.2f}</code>\n"
            f"💰 Profit    : <code>${profit:+.2f}</code>\n"
            f"📋 Trades    : <code>{trades}</code>\n"
            f"🏆 Win Rate  : <code>{win_rate}%</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━"
        )
        self.send(msg)
```

---

### `main.py` — Siklus Utama Scalping

```python
import time
import logging
import schedule
from datetime import datetime

import MetaTrader5 as mt5

from config import SYMBOL, TF_ENTRY, MAGIC_NUMBER
from core.connector import MT5Connector
from core.trader import ScalpingTrader
from strategy.indicators import get_candles, calculate_m5_indicators, get_trend_direction
from strategy.signals import ScalpingSignal
from strategy.session_filter import SessionFilter
from risk.manager import ScalpingRiskManager
from utils.notifier import TelegramNotifier
from utils.logger import setup_logger

logger = setup_logger("logs/scalping_ea.log")

connector = MT5Connector()
trader    = ScalpingTrader()
signal_g  = ScalpingSignal()
session_f = SessionFilter()
risk_mgr  = ScalpingRiskManager()
notifier  = TelegramNotifier()

last_session_notif = ""

def run_scalping_cycle():
    """Siklus utama EA scalping — dijalankan setiap 10 detik."""
    global last_session_notif

    # 1. Cek apakah jam trading aktif
    can_trade, reason = session_f.can_trade()

    # Tutup posisi jika sesi berakhir
    if not can_trade:
        logger.debug(f"⏸️  {reason}")
        # Tutup posisi yang sudah breakeven jika sesi tutup
        # trader.close_all_positions(SYMBOL, "Session End")
        return

    # Kirim notifikasi awal sesi (sekali saja)
    session_name = reason.split("|")[0].strip()
    if session_name != last_session_notif:
        last_session_notif = session_name
        sym    = mt5.symbol_info(SYMBOL)
        spread = sym.spread / 10 if sym else 0
        trend  = get_trend_direction(SYMBOL)
        notifier.alert_session_start(session_name, SYMBOL, spread, trend)

    # 2. Manage posisi yang sudah ada
    trader.manage_breakeven(SYMBOL)
    trader.manage_trailing_stop(SYMBOL)

    # 3. Cek apakah boleh buka posisi baru
    allowed, allow_reason = risk_mgr.is_trade_allowed(SYMBOL)
    if not allowed:
        logger.debug(f"🚫 {allow_reason}")
        return

    # 4. Ambil data & hitung indikator M5
    df_m5 = get_candles(SYMBOL, TF_ENTRY, n=100)
    if df_m5.empty:
        return
    df_m5 = calculate_m5_indicators(df_m5)

    # 5. Ambil arah trend dari M15
    trend = get_trend_direction(SYMBOL)

    # 6. Evaluasi signal scalping
    signal = signal_g.get_signal(df_m5, trend)
    if signal == "HOLD":
        return

    snap = signal_g.get_market_snapshot(df_m5, trend)
    logger.info(f"⚡ Signal {signal} | {snap}")

    # 7. Hitung SL, TP, Lot
    tick  = mt5.symbol_info_tick(SYMBOL)
    price = tick.ask if signal == "BUY" else tick.bid
    sl, tp = risk_mgr.get_sl_tp(SYMBOL, signal, price)
    lot    = risk_mgr.calculate_lot(SYMBOL, SL_PIPS)

    # 8. Eksekusi order
    result = trader.open_trade(
        symbol=SYMBOL, signal=signal,
        lot=lot, sl=sl, tp=tp
    )

    # 9. Notifikasi Telegram
    if result:
        _, spread_val = risk_mgr.check_spread(SYMBOL)
        notifier.alert_trade_open(
            signal=signal, symbol=SYMBOL,
            price=result["price"], sl=sl, tp=tp,
            lot=lot, ticket=result["ticket"],
            spread=spread_val, session=session_name
        )


def daily_summary():
    """Kirim summary harian jam 21:00 UTC."""
    acc = mt5.account_info()
    if not acc:
        return

    since = datetime.now().replace(hour=0, minute=0, second=0)
    history = mt5.history_deals_get(since, datetime.now()) or []
    deals   = [d for d in history if d.magic == MAGIC_NUMBER and d.entry == 1]
    profits = [d.profit for d in deals]
    wins    = sum(1 for p in profits if p > 0)

    notifier.alert_daily_summary(
        balance=acc.balance,
        profit=sum(profits),
        trades=len(profits),
        wins=wins
    )


def main():
    logger.info("=" * 58)
    logger.info("  ⚡ EA SCALPING FOREX M5/M15 — STARTING")
    logger.info("=" * 58)

    if not connector.connect():
        logger.critical("Gagal konek MT5. EA berhenti.")
        return

    # Siklus setiap 10 detik (cocok untuk M5 scalping)
    schedule.every(10).seconds.do(run_scalping_cycle)
    schedule.every().day.at("21:00").do(daily_summary)

    notifier.send(
        f"⚡ <b>EA Scalping aktif!</b>\n"
        f"📌 {SYMBOL} | M5/M15 | Target: {TP_PIPS}p TP / {SL_PIPS}p SL"
    )

    logger.info(f"✅ EA aktif | {SYMBOL} | Siklus: 10 detik | "
                f"TP: {TP_PIPS}p | SL: {SL_PIPS}p")

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("⛔ EA dihentikan.")
        trader.close_all_positions(SYMBOL, "EA-Stop")
    finally:
        connector.disconnect()
        notifier.send("⛔ <b>EA Scalping dihentikan.</b>")


if __name__ == "__main__":
    main()
```

---

## 📊 Strategi & Logika Signal

### Dual Timeframe System

```
M15 (Trend Filter)          M5 (Entry Signal)
─────────────────           ──────────────────────────────
EMA 50 > EMA 200            EMA 9 crossover ke atas EMA 21
→ Trend BULLISH        +    RSI 7 antara 40–65
→ Hanya cari BUY            Stochastic %K < 80 & naik
                            Close > BB Midline
                            ATR > 3 pips
                                  │
                                  ▼
                            Score ≥ 4/6 + ada crossover
                                  │
                                  ▼
                              OPEN BUY ⚡
```

### Parameter Indikator Scalping

| Indikator | M5 (Entry) | M15 (Trend) | Alasan |
|-----------|-----------|-------------|--------|
| EMA Fast | 9 | — | Responsif terhadap pergerakan cepat |
| EMA Slow | 21 | — | Konfirmasi arah jangka pendek |
| EMA Trend | — | 50 / 200 | Filter arah makro |
| RSI | 7 period | — | Lebih sensitif untuk scalping |
| Stochastic | 5/3/3 | — | Deteksi momentum sesaat |
| Bollinger Bands | 20/2σ | — | Filter posisi harga |
| ATR | 7 period | — | Validasi ada volatilitas |

---

## 🛡️ Risk Management Scalping

### Target Per Trade

```
┌─────────────────────────────────────────┐
│         PARAMETER SCALPING              │
│                                         │
│  TP        : 10 pips  (bisa 5–15)      │
│  SL        : 8 pips                    │
│  Risk:Reward : 1 : 1.25                │
│  Max Risk  : 0.5% per trade            │
│  Breakeven : setelah +5 pips           │
│  Trailing  : mulai +7 pips, step 3p   │
│  Max Posisi: 2 simultan                │
│  Max Spread: 2.0 pips                  │
└─────────────────────────────────────────┘
```

### Manajemen Posisi Scalping

```
Entry @ 1.09000
    │
    ├── +5 pips → SL digeser ke Breakeven (1.09001)
    │
    ├── +7 pips → Trailing Stop aktif
    │              (SL ikut harga, jarak 3 pip)
    │
    └── +10 pips → TP tercapai ✅
```

### Kalkulasi Lot

```
Balance     = $1,000
Risk        = 0.5% → $5
SL          = 8 pips
Pip Value   = $10/lot (EURUSD)

Lot = $5 ÷ (8 × $10) = 0.06 lot → dibulatkan ke 0.06
```

---

## 🕐 Session Filter

### Jam Trading yang Diizinkan (UTC)

```
00:00 ──── 07:00 ──── 12:00 ──── 16:00 ──── 20:00 ──── 24:00
   │           │           │           │           │
   [  ASIA  ] [ LONDON   ][  OVERLAP  ][  NEW YORK ][ TUTUP ]
   ❌ Skip    ✅ Trading  ⭐ Prioritas  ✅ Trading  ❌ Skip
```

| Sesi | Jam UTC | Status | Alasan |
|------|---------|--------|--------|
| Asia | 00:00–07:00 | ❌ Skip | Spread lebar, range sempit |
| London | 07:00–16:00 | ✅ Aktif | Likuiditas tinggi |
| Overlap | 12:00–16:00 | ⭐ Prioritas | Volume tertinggi |
| New York | 12:00–20:00 | ✅ Aktif | Volatilitas baik |
| Jumat 19:00+ | — | ❌ Skip | Gap akhir pekan |
| Senin 00:00–01:00 | — | ❌ Skip | Gap risk tinggi |

---

## 📱 Notifikasi Telegram

### Contoh Alert Trade Open

```
🟢 SCALP BUY — EURUSD
━━━━━━━━━━━━━━━━━━━━━━
⏰ Waktu   : 14:35:20 UTC
📍 Sesi    : OVERLAP ⭐
💵 Entry   : 1.08520
🛡️ SL      : 1.08440 (8p)
🎯 TP      : 1.08620 (10p)
⚖️ R:R     : 1:1.3
📦 Lot     : 0.06
📊 Spread  : 0.3 pips
🎫 Ticket  : 789012
━━━━━━━━━━━━━━━━━━━━━━
⚡ EA Scalping Python
```

---

## ▶️ Cara Menjalankan

### Langkah 1 — Persiapan

```bash
git clone https://github.com/yourname/scalping_ea.git
cd scalping_ea
pip install -r requirements.txt
cp .env.example .env
# Edit .env dengan data akun Anda
```

### Langkah 2 — Pastikan MT5 Ready

```
✓ MT5 terbuka & login ke akun demo
✓ Algo Trading diaktifkan (ikon robot di toolbar)
✓ EURUSD ada di Market Watch
✓ Koneksi internet stabil
```

### Langkah 3 — Jalankan EA

```bash
# Foreground (lihat log real-time)
python main.py

# Background di Windows
start /B pythonw main.py

# Background di Linux
nohup python main.py &
```

### Langkah 4 — Monitor

```bash
# Pantau log real-time
tail -f logs/scalping_ea.log
```

### Output Normal EA

```
══════════════════════════════════════════════════════════
  ⚡ EA SCALPING FOREX M5/M15 — STARTING
══════════════════════════════════════════════════════════
2024-01-15 12:00:05 [INFO] ✅ Terhubung MT5 | Balance: $1,000.00
2024-01-15 12:00:05 [INFO] ✅ EA aktif | EURUSD | TP: 10p | SL: 8p
2024-01-15 12:00:10 [DEBUG] ⏸️  Sesi Asia — spread lebar, skip
...
2024-01-15 14:00:10 [INFO] ⚡ Signal BUY | trend: BULL | rsi: 52.3
2024-01-15 14:00:10 [INFO] 📦 Lot Size | Risk: $5.00 | Lot: 0.06
2024-01-15 14:00:11 [INFO] ✅ SCALP BUY OPEN | Ticket: 789012 | 1.08520
2024-01-15 14:05:20 [INFO] 🔒 BREAKEVEN | Ticket: 789012 | Profit: 5.2p
2024-01-15 14:08:45 [INFO] 🔄 TRAIL BUY | SL: 1.08501 → 1.08551
```

---

## 💡 Tips Scalping Profesional

### Wajib Dilakukan

- **Demo dulu minimal 2 minggu** — pastikan profitable sebelum live
- **ECN broker** — spread harus < 1 pip saat jam aktif
- **VPS** — latency rendah ke server broker (< 10ms)
- **Koneksi internet stabil** — gunakan kabel, bukan WiFi
- **Monitor spread real-time** — spread spike = jangan entry

### Parameter yang Bisa Dioptimalkan

| Parameter | Default | Range | Keterangan |
|-----------|---------|-------|-----------|
| TP_PIPS | 10 | 5–15 | Sesuaikan dengan volatilitas harian |
| SL_PIPS | 8 | 6–12 | Lebih ketat = lebih banyak stop out |
| MAX_SPREAD | 2.0 | 1.0–3.0 | Turunkan saat sesi overlap |
| BREAKEVEN | 5 | 3–7 | Lebih cepat = lebih aman |
| MAX_RISK | 0.5% | 0.3–1% | Mulai dari 0.3% saat pertama live |

### Red Flag — Hentikan EA Jika

```
❌ Drawdown > 5% dalam sehari
❌ 5 loss berturut-turut tanpa win
❌ Spread EURUSD > 3 pips terus-menerus
❌ Berita besar dalam 30 menit ke depan
❌ Koneksi internet tidak stabil
```

---

## 🔧 Troubleshooting

| Masalah | Kemungkinan Penyebab | Solusi |
|---------|---------------------|--------|
| Order gagal (10004) | Requote | Turunkan `deviation` ke 5 |
| Order gagal (10006) | Request rejected | Cek koneksi & restart MT5 |
| Spread selalu lebar | Broker tidak cocok | Ganti ke broker ECN |
| Signal terlalu jarang | ATR terlalu tinggi | Turunkan `MIN_ATR_PIPS` ke 2 |
| Signal terlalu sering | Kondisi terlalu longgar | Naikkan threshold score ke 5/6 |
| Breakeven tidak jalan | SL sudah di BE | Normal — sudah terlindungi |
| MT5 tidak konek | MT5 belum dibuka | Buka & login MT5 dulu |
| `pytz` not found | Library kurang | `pip install pytz` |

---

## ⚠️ Disclaimer

> **PERINGATAN:** Scalping adalah strategi trading berisiko tinggi yang membutuhkan eksekusi cepat, spread rendah, dan disiplin ketat. EA ini dibuat untuk **tujuan edukasi**. Selalu:
>
> - Test di **akun demo** minimal 2–4 minggu
> - Mulai live dengan **lot terkecil** (0.01)
> - Gunakan **modal yang siap hilang**
> - Performa masa lalu **tidak menjamin** hasil di masa depan
> - Scalping tidak cocok untuk semua kondisi pasar

---

*⚡ EA Scalping Forex Python · Versi 2.0 · M5/M15 Strategy*
*Target: 5–15 pips · SL: 8 pips · Max Risk: 0.5%/trade*