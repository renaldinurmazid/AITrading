# 🤖 EA Trading Forex — Python + MetaTrader 5
### Automated Expert Advisor dengan Analisa Teknikal & Fundamental

> **Stack:** Python 3.10+ · MetaTrader 5 · `MetaTrader5` library · `pandas` · `ta-lib`

---

## 📋 Daftar Isi

1. [Arsitektur Sistem](#arsitektur-sistem)
2. [Persyaratan & Instalasi](#persyaratan--instalasi)
3. [Struktur Folder Proyek](#struktur-folder-proyek)
4. [Konfigurasi EA](#konfigurasi-ea)
5. [Kode EA Lengkap](#kode-ea-lengkap)
6. [Modul Analisa Teknikal](#modul-analisa-teknikal)
7. [Modul Risk Management](#modul-risk-management)
8. [Modul Notifikasi Telegram](#modul-notifikasi-telegram)
9. [Cara Menjalankan](#cara-menjalankan)
10. [Strategi Trading yang Digunakan](#strategi-trading-yang-digunakan)
11. [Backtest & Optimasi](#backtest--optimasi)
12. [Troubleshooting](#troubleshooting)

---

## 🏗️ Arsitektur Sistem

```
┌─────────────────────────────────────────────────────────┐
│                    EA Trading System                    │
│                                                         │
│  ┌──────────────┐    ┌──────────────┐   ┌────────────┐ │
│  │   Python EA  │◄──►│  MT5 Bridge  │◄──►│ MetaTrader │ │
│  │  (Strategy)  │    │  (mt5 lib)   │   │   5 App    │ │
│  └──────┬───────┘    └──────────────┘   └────────────┘ │
│         │                                               │
│  ┌──────▼───────┐    ┌──────────────┐   ┌────────────┐ │
│  │   Technical  │    │     Risk     │   │  Telegram  │ │
│  │   Analysis   │    │  Management  │   │   Alerts   │ │
│  └──────────────┘    └──────────────┘   └────────────┘ │
└─────────────────────────────────────────────────────────┘
```

**Alur Kerja:**
1. EA terhubung ke MetaTrader 5 via library Python resmi
2. Setiap tick/interval, EA mengambil data OHLCV dari MT5
3. Indikator teknikal dihitung (EMA, RSI, MACD, Bollinger Bands)
4. Signal BUY/SELL divalidasi dengan filter trend & volume
5. Risk management menentukan lot size, SL, TP
6. Order dikirim ke MT5 dan dimonitor
7. Notifikasi dikirim ke Telegram

---

## ⚙️ Persyaratan & Instalasi

### 1. Software Yang Dibutuhkan

| Software | Versi | Keterangan |
|----------|-------|-----------|
| Python | 3.10+ | [python.org](https://python.org) |
| MetaTrader 5 | Latest | Dari broker Anda |
| pip | Latest | Package manager Python |

### 2. Instalasi Python Libraries

```bash
pip install MetaTrader5
pip install pandas numpy
pip install ta          # Technical Analysis library
pip install requests    # Untuk notifikasi Telegram
pip install python-dotenv
pip install schedule
pip install colorlog
```

### 3. Setup MetaTrader 5

- Install MT5 dari broker Anda
- Login ke akun **demo** terlebih dahulu
- Aktifkan **Algo Trading** di MT5:
  - `Tools` → `Options` → `Expert Advisors`
  - Centang: *Allow automated trading*
  - Centang: *Allow DLL imports*
- Pastikan MT5 **running** saat EA Python dijalankan

### 4. Konfigurasi `.env`

Buat file `.env` di root folder proyek:

```env
MT5_LOGIN=12345678
MT5_PASSWORD=YourPassword
MT5_SERVER=BrokerName-Demo

TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

SYMBOL=EURUSD
TIMEFRAME=H1
LOT_SIZE=0.01
MAX_RISK_PERCENT=1.0
MAX_OPEN_TRADES=3
```

---

## 📁 Struktur Folder Proyek

```
forex_ea/
├── main.py                 # Entry point utama
├── config.py               # Konfigurasi & parameter
├── .env                    # Variabel lingkungan (rahasia)
├── requirements.txt        # Daftar dependencies
│
├── core/
│   ├── __init__.py
│   ├── connector.py        # Koneksi MT5
│   ├── trader.py           # Eksekusi order
│   └── monitor.py          # Monitor posisi terbuka
│
├── strategy/
│   ├── __init__.py
│   ├── signals.py          # Logic signal BUY/SELL
│   └── indicators.py       # Kalkulasi indikator teknikal
│
├── risk/
│   ├── __init__.py
│   └── manager.py          # Risk & money management
│
├── utils/
│   ├── __init__.py
│   ├── logger.py           # Logging
│   └── notifier.py         # Telegram notifikasi
│
└── logs/
    └── ea_trading.log      # Log file
```

---

## 🔧 Konfigurasi EA

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

# ─── Parameter Trading ─────────────────────────────────
SYMBOL       = os.getenv("SYMBOL", "EURUSD")
TIMEFRAME    = mt5.TIMEFRAME_H1          # H1 default
LOT_SIZE     = float(os.getenv("LOT_SIZE", 0.01))
MAGIC_NUMBER = 20240101                  # ID unik EA

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
```

---

## 💻 Kode EA Lengkap

### `core/connector.py` — Koneksi MT5

```python
import MetaTrader5 as mt5
import logging
from config import MT5_CONFIG, SYMBOL

logger = logging.getLogger(__name__)

class MT5Connector:
    """Mengelola koneksi ke MetaTrader 5."""

    def __init__(self):
        self.connected = False

    def connect(self) -> bool:
        """Inisiasi koneksi ke MT5."""
        if not mt5.initialize():
            logger.error(f"MT5 initialize gagal: {mt5.last_error()}")
            return False

        authorized = mt5.login(
            login=MT5_CONFIG["login"],
            password=MT5_CONFIG["password"],
            server=MT5_CONFIG["server"],
        )
        if not authorized:
            logger.error(f"Login MT5 gagal: {mt5.last_error()}")
            mt5.shutdown()
            return False

        account = mt5.account_info()
        logger.info(f"✅ Terhubung ke MT5 | Akun: {account.login} | "
                    f"Server: {account.server} | Balance: ${account.balance:.2f}")
        self.connected = True
        return True

    def disconnect(self):
        """Putus koneksi dari MT5."""
        mt5.shutdown()
        self.connected = False
        logger.info("🔌 Koneksi MT5 diputus.")

    def get_account_info(self) -> dict:
        """Ambil informasi akun trading."""
        info = mt5.account_info()
        if info is None:
            return {}
        return {
            "balance":   info.balance,
            "equity":    info.equity,
            "margin":    info.margin,
            "free_margin": info.margin_free,
            "profit":    info.profit,
            "leverage":  info.leverage,
        }

    def get_symbol_info(self, symbol: str = SYMBOL) -> dict:
        """Ambil informasi simbol."""
        sym = mt5.symbol_info(symbol)
        if sym is None:
            logger.error(f"Simbol {symbol} tidak ditemukan!")
            return {}
        if not sym.visible:
            mt5.symbol_select(symbol, True)
        return {
            "bid":        sym.bid,
            "ask":        sym.ask,
            "spread":     sym.spread,
            "point":      sym.point,
            "digits":     sym.digits,
            "volume_min": sym.volume_min,
            "volume_step": sym.volume_step,
        }
```

---

### `strategy/indicators.py` — Indikator Teknikal

```python
import pandas as pd
import numpy as np
import MetaTrader5 as mt5
from ta.trend import EMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands, AverageTrueRange
from config import *

def get_candles(symbol: str, timeframe, n_candles: int = 300) -> pd.DataFrame:
    """Ambil data candle dari MT5 dan konversi ke DataFrame."""
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, n_candles)
    if rates is None or len(rates) == 0:
        return pd.DataFrame()

    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df.set_index("time", inplace=True)
    df.rename(columns={
        "open": "Open", "high": "High",
        "low": "Low", "close": "Close", "tick_volume": "Volume"
    }, inplace=True)
    return df

def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Hitung semua indikator teknikal.
    Indikator: EMA 21/50/200, RSI 14, MACD, Bollinger Bands, ATR
    """
    if df.empty:
        return df

    close = df["Close"]
    high  = df["High"]
    low   = df["Low"]

    # ── EMA ────────────────────────────────────────────
    df["ema_fast"]  = EMAIndicator(close, window=EMA_FAST).ema_indicator()
    df["ema_slow"]  = EMAIndicator(close, window=EMA_SLOW).ema_indicator()
    df["ema_trend"] = EMAIndicator(close, window=EMA_TREND).ema_indicator()

    # ── RSI ────────────────────────────────────────────
    rsi = RSIIndicator(close, window=RSI_PERIOD)
    df["rsi"] = rsi.rsi()

    # ── MACD ───────────────────────────────────────────
    macd_indicator = MACD(close,
                          window_slow=MACD_SLOW,
                          window_fast=MACD_FAST,
                          window_sign=MACD_SIGNAL)
    df["macd"]        = macd_indicator.macd()
    df["macd_signal"] = macd_indicator.macd_signal()
    df["macd_hist"]   = macd_indicator.macd_diff()

    # ── Bollinger Bands ────────────────────────────────
    bb = BollingerBands(close, window=BB_PERIOD, window_dev=BB_STD)
    df["bb_upper"] = bb.bollinger_hband()
    df["bb_lower"] = bb.bollinger_lband()
    df["bb_mid"]   = bb.bollinger_mavg()
    df["bb_width"] = bb.bollinger_wband()

    # ── ATR (untuk SL dinamis) ─────────────────────────
    atr = AverageTrueRange(high, low, close, window=14)
    df["atr"] = atr.average_true_range()

    # ── Trend Filter ───────────────────────────────────
    df["trend_up"]   = (df["ema_fast"] > df["ema_slow"]) & \
                       (df["ema_slow"] > df["ema_trend"])
    df["trend_down"] = (df["ema_fast"] < df["ema_slow"]) & \
                       (df["ema_slow"] < df["ema_trend"])

    return df
```

---

### `strategy/signals.py` — Signal BUY/SELL

```python
import pandas as pd
import logging
from config import *

logger = logging.getLogger(__name__)

class SignalGenerator:
    """
    Strategi: EMA Crossover + RSI Filter + MACD Confirmation
    
    BUY  : EMA fast > EMA slow (crossover ke atas) + RSI tidak overbought
           + MACD histogram positif + harga di atas EMA 200
    
    SELL : EMA fast < EMA slow (crossover ke bawah) + RSI tidak oversold
           + MACD histogram negatif + harga di bawah EMA 200
    """

    def get_signal(self, df: pd.DataFrame) -> str:
        """
        Evaluasi kondisi pasar dan hasilkan signal.
        Return: 'BUY', 'SELL', atau 'HOLD'
        """
        if df.empty or len(df) < EMA_TREND + 10:
            return "HOLD"

        cur  = df.iloc[-1]   # candle terbaru
        prev = df.iloc[-2]   # candle sebelumnya

        # ── Deteksi EMA Crossover ──────────────────────
        buy_crossover  = (prev["ema_fast"] <= prev["ema_slow"]) and \
                         (cur["ema_fast"]  >  cur["ema_slow"])
        sell_crossover = (prev["ema_fast"] >= prev["ema_slow"]) and \
                         (cur["ema_fast"]  <  cur["ema_slow"])

        # ── Kondisi BUY ───────────────────────────────
        buy_conditions = [
            buy_crossover,                           # EMA crossover ke atas
            cur["rsi"] < RSI_OVERBOUGHT,             # RSI belum overbought
            cur["rsi"] > 40,                         # RSI tidak terlalu lemah
            cur["macd_hist"] > 0,                    # MACD histogram positif
            cur["Close"] > cur["ema_trend"],         # Harga di atas EMA 200
            cur["trend_up"],                         # Konfirmasi trend naik
        ]

        # ── Kondisi SELL ──────────────────────────────
        sell_conditions = [
            sell_crossover,                          # EMA crossover ke bawah
            cur["rsi"] > RSI_OVERSOLD,               # RSI belum oversold
            cur["rsi"] < 60,                         # RSI tidak terlalu kuat
            cur["macd_hist"] < 0,                    # MACD histogram negatif
            cur["Close"] < cur["ema_trend"],         # Harga di bawah EMA 200
            cur["trend_down"],                       # Konfirmasi trend turun
        ]

        buy_score  = sum(buy_conditions)
        sell_score = sum(sell_conditions)

        logger.debug(f"Buy score: {buy_score}/6 | Sell score: {sell_score}/6")
        logger.debug(f"RSI: {cur['rsi']:.1f} | MACD Hist: {cur['macd_hist']:.5f}")

        # Minimal 5 dari 6 kondisi terpenuhi
        if buy_score >= 5:
            logger.info(f"🟢 SIGNAL BUY | Score: {buy_score}/6 | "
                        f"RSI: {cur['rsi']:.1f}")
            return "BUY"

        if sell_score >= 5:
            logger.info(f"🔴 SIGNAL SELL | Score: {sell_score}/6 | "
                        f"RSI: {cur['rsi']:.1f}")
            return "SELL"

        return "HOLD"

    def get_signal_strength(self, df: pd.DataFrame) -> dict:
        """Hitung kekuatan signal untuk reporting."""
        if df.empty:
            return {}
        cur = df.iloc[-1]
        return {
            "rsi":       round(cur["rsi"], 2),
            "macd_hist": round(cur["macd_hist"], 5),
            "ema_spread": round(cur["ema_fast"] - cur["ema_slow"], 5),
            "atr":       round(cur["atr"], 5),
            "trend":     "UP" if cur["trend_up"] else
                         "DOWN" if cur["trend_down"] else "SIDEWAYS",
        }
```

---

### `risk/manager.py` — Risk Management

```python
import MetaTrader5 as mt5
import logging
import math
from config import *

logger = logging.getLogger(__name__)

class RiskManager:
    """Kalkulasi lot size dan level SL/TP berbasis ATR & risk percent."""

    def calculate_lot_size(self, symbol: str, sl_pips: float,
                           risk_percent: float = MAX_RISK_PERCENT) -> float:
        """
        Hitung lot size berdasarkan risk percent dari balance.
        Formula: Lot = (Balance * Risk%) / (SL in pips * pip value)
        """
        account = mt5.account_info()
        sym_info = mt5.symbol_info(symbol)

        if account is None or sym_info is None:
            logger.error("Gagal ambil info akun/simbol untuk kalkulasi lot")
            return sym_info.volume_min if sym_info else 0.01

        balance    = account.balance
        risk_money = balance * (risk_percent / 100)
        point      = sym_info.point
        pip_value  = sym_info.trade_tick_value

        # Pip value per lot = (1 pip / point) * tick_value
        pip_val_per_lot = (10 * point / point) * pip_value
        sl_money        = sl_pips * pip_val_per_lot

        if sl_money <= 0:
            return sym_info.volume_min

        raw_lot = risk_money / sl_money

        # Normalisasi ke volume step broker
        step    = sym_info.volume_step
        lot     = math.floor(raw_lot / step) * step
        lot     = max(sym_info.volume_min, min(lot, sym_info.volume_max))
        lot     = round(lot, 2)

        logger.info(f"💰 Kalkulasi Lot | Balance: ${balance:.2f} | "
                    f"Risk: ${risk_money:.2f} | SL: {sl_pips} pips | Lot: {lot}")
        return lot

    def calculate_sl_tp_atr(self, df, signal: str, atr_multiplier_sl: float = 1.5,
                             atr_multiplier_tp: float = 3.0) -> tuple:
        """
        Hitung SL dan TP dinamis berdasarkan ATR.
        SL = ATR * 1.5 | TP = ATR * 3.0 (Risk:Reward = 1:2)
        """
        if df.empty:
            return STOP_LOSS_PIPS, TAKE_PROFIT_PIPS

        atr    = df.iloc[-1]["atr"]
        sl_pts = round(atr * atr_multiplier_sl, 5)
        tp_pts = round(atr * atr_multiplier_tp, 5)

        sym    = mt5.symbol_info(SYMBOL)
        point  = sym.point if sym else 0.00001
        sl_pips = round(sl_pts / (10 * point))
        tp_pips = round(tp_pts / (10 * point))

        logger.debug(f"ATR-based | SL: {sl_pips} pips | TP: {tp_pips} pips | R:R 1:2")
        return sl_pips, tp_pips

    def count_open_trades(self, symbol: str = None) -> int:
        """Hitung jumlah posisi terbuka."""
        positions = mt5.positions_get(symbol=symbol) if symbol \
                    else mt5.positions_get(magic=MAGIC_NUMBER)
        return len(positions) if positions else 0

    def is_trade_allowed(self, symbol: str) -> tuple:
        """Validasi apakah trade boleh dibuka."""
        open_trades = self.count_open_trades(symbol)

        if open_trades >= MAX_OPEN_TRADES:
            return False, f"Max trade ({MAX_OPEN_TRADES}) sudah tercapai"

        acc = mt5.account_info()
        if acc.margin_level > 0 and acc.margin_level < 150:
            return False, f"Margin level terlalu rendah: {acc.margin_level:.1f}%"

        return True, "OK"
```

---

### `core/trader.py` — Eksekusi Order

```python
import MetaTrader5 as mt5
import logging
from config import *

logger = logging.getLogger(__name__)

class Trader:
    """Mengirim dan mengelola order ke MetaTrader 5."""

    def open_trade(self, symbol: str, signal: str,
                   lot: float, sl_pips: float, tp_pips: float,
                   comment: str = "EA-Python") -> dict:
        """
        Buka posisi baru.
        signal: 'BUY' atau 'SELL'
        """
        sym_info = mt5.symbol_info_tick(symbol)
        if sym_info is None:
            logger.error(f"Tidak bisa ambil tick untuk {symbol}")
            return {}

        point = mt5.symbol_info(symbol).point
        pip   = 10 * point

        if signal == "BUY":
            order_type = mt5.ORDER_TYPE_BUY
            price      = sym_info.ask
            sl         = round(price - sl_pips * pip, 5)
            tp         = round(price + tp_pips * pip, 5)
        elif signal == "SELL":
            order_type = mt5.ORDER_TYPE_SELL
            price      = sym_info.bid
            sl         = round(price + sl_pips * pip, 5)
            tp         = round(price - tp_pips * pip, 5)
        else:
            return {}

        request = {
            "action":      mt5.TRADE_ACTION_DEAL,
            "symbol":      symbol,
            "volume":      lot,
            "type":        order_type,
            "price":       price,
            "sl":          sl,
            "tp":          tp,
            "deviation":   20,
            "magic":       MAGIC_NUMBER,
            "comment":     comment,
            "type_time":   mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)

        if result.retcode == mt5.TRADE_RETCODE_DONE:
            logger.info(f"✅ ORDER {signal} | Ticket: {result.order} | "
                        f"Price: {price} | SL: {sl} | TP: {tp} | Lot: {lot}")
            return {
                "ticket": result.order,
                "signal": signal,
                "price":  price,
                "sl": sl, "tp": tp,
                "lot": lot,
            }
        else:
            logger.error(f"❌ Order gagal | Retcode: {result.retcode} | "
                         f"Comment: {result.comment}")
            return {}

    def close_position(self, ticket: int) -> bool:
        """Tutup posisi berdasarkan ticket number."""
        position = mt5.positions_get(ticket=ticket)
        if not position:
            logger.warning(f"Posisi ticket {ticket} tidak ditemukan")
            return False

        pos = position[0]
        sym_info = mt5.symbol_info_tick(pos.symbol)
        close_type = mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY
        close_price = sym_info.bid if pos.type == 0 else sym_info.ask

        request = {
            "action":      mt5.TRADE_ACTION_DEAL,
            "symbol":      pos.symbol,
            "volume":      pos.volume,
            "type":        close_type,
            "position":    ticket,
            "price":       close_price,
            "deviation":   20,
            "magic":       MAGIC_NUMBER,
            "comment":     "EA-Close",
            "type_time":   mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            logger.info(f"✅ Posisi {ticket} ditutup | Profit: {pos.profit:.2f}")
            return True

        logger.error(f"❌ Gagal tutup posisi {ticket}: {result.comment}")
        return False

    def update_trailing_stop(self, symbol: str = SYMBOL):
        """Update trailing stop untuk semua posisi terbuka."""
        positions = mt5.positions_get(symbol=symbol)
        if not positions:
            return

        sym_info = mt5.symbol_info(symbol)
        point    = sym_info.point
        pip      = 10 * point
        tick     = mt5.symbol_info_tick(symbol)

        for pos in positions:
            if pos.magic != MAGIC_NUMBER:
                continue

            if pos.type == 0:   # BUY
                new_sl = round(tick.bid - TRAILING_PIPS * pip, 5)
                if new_sl > pos.sl:
                    self._modify_sl(pos.ticket, new_sl)

            elif pos.type == 1:  # SELL
                new_sl = round(tick.ask + TRAILING_PIPS * pip, 5)
                if new_sl < pos.sl or pos.sl == 0:
                    self._modify_sl(pos.ticket, new_sl)

    def _modify_sl(self, ticket: int, new_sl: float):
        """Modifikasi SL sebuah posisi."""
        request = {
            "action":   mt5.TRADE_ACTION_SLTP,
            "position": ticket,
            "sl":       new_sl,
        }
        result = mt5.order_send(request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            logger.debug(f"✅ Trailing stop diupdate | Ticket: {ticket} | SL: {new_sl}")
```

---

### `utils/notifier.py` — Notifikasi Telegram

```python
import requests
import logging
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)

class TelegramNotifier:
    """Kirim notifikasi trading ke Telegram."""

    BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

    def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            return False
        try:
            resp = requests.post(
                f"{self.BASE_URL}/sendMessage",
                json={"chat_id": TELEGRAM_CHAT_ID,
                      "text": text,
                      "parse_mode": parse_mode},
                timeout=10
            )
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"Telegram error: {e}")
            return False

    def notify_trade_open(self, signal: str, symbol: str,
                          price: float, sl: float, tp: float,
                          lot: float, ticket: int):
        emoji = "🟢" if signal == "BUY" else "🔴"
        msg = (
            f"{emoji} <b>TRADE OPEN — {signal}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📌 Simbol  : <b>{symbol}</b>\n"
            f"💵 Harga   : <code>{price}</code>\n"
            f"🛡️ SL      : <code>{sl}</code>\n"
            f"🎯 TP      : <code>{tp}</code>\n"
            f"📦 Lot     : <code>{lot}</code>\n"
            f"🎫 Ticket  : <code>{ticket}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⚡ EA Python Auto-Trader"
        )
        self.send_message(msg)

    def notify_trade_close(self, symbol: str, ticket: int,
                           profit: float, pips: float):
        emoji = "✅" if profit >= 0 else "❌"
        msg = (
            f"{emoji} <b>TRADE CLOSED</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📌 Simbol  : <b>{symbol}</b>\n"
            f"🎫 Ticket  : <code>{ticket}</code>\n"
            f"💰 Profit  : <code>${profit:.2f}</code>\n"
            f"📐 Pips    : <code>{pips:.1f}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
        self.send_message(msg)

    def notify_daily_report(self, balance: float, equity: float,
                            daily_profit: float, total_trades: int,
                            win_rate: float):
        emoji = "📈" if daily_profit >= 0 else "📉"
        msg = (
            f"{emoji} <b>LAPORAN HARIAN</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💼 Balance   : <code>${balance:.2f}</code>\n"
            f"📊 Equity    : <code>${equity:.2f}</code>\n"
            f"💰 Profit    : <code>${daily_profit:.2f}</code>\n"
            f"📋 Trades    : <code>{total_trades}</code>\n"
            f"🎯 Win Rate  : <code>{win_rate:.1f}%</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
        self.send_message(msg)
```

---

### `main.py` — Entry Point Utama

```python
import time
import logging
import schedule
from datetime import datetime

import MetaTrader5 as mt5

from config import SYMBOL, TIMEFRAME, MAGIC_NUMBER, TRAILING_STOP
from core.connector import MT5Connector
from core.trader import Trader
from core.monitor import PositionMonitor
from strategy.indicators import get_candles, calculate_indicators
from strategy.signals import SignalGenerator
from risk.manager import RiskManager
from utils.notifier import TelegramNotifier
from utils.logger import setup_logger

logger = setup_logger()

# ─── Inisiasi Komponen ─────────────────────────────────
connector = MT5Connector()
trader    = Trader()
monitor   = PositionMonitor()
signal_gen = SignalGenerator()
risk_mgr  = RiskManager()
notifier  = TelegramNotifier()


def run_ea():
    """Siklus utama EA — dijalankan setiap candle baru."""
    logger.info(f"⏰ Siklus EA | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 1. Ambil data market
    df = get_candles(SYMBOL, TIMEFRAME, n_candles=300)
    if df.empty:
        logger.warning("Data candle kosong, skip siklus ini.")
        return

    # 2. Hitung indikator
    df = calculate_indicators(df)

    # 3. Cek signal
    signal = signal_gen.get_signal(df)
    strength = signal_gen.get_signal_strength(df)
    logger.info(f"📊 Signal: {signal} | {strength}")

    if signal == "HOLD":
        # Update trailing stop meski tidak ada sinyal baru
        if TRAILING_STOP:
            trader.update_trailing_stop(SYMBOL)
        return

    # 4. Validasi apakah boleh trade
    allowed, reason = risk_mgr.is_trade_allowed(SYMBOL)
    if not allowed:
        logger.info(f"⚠️ Trade tidak diizinkan: {reason}")
        return

    # 5. Kalkulasi SL, TP, dan lot size
    sl_pips, tp_pips = risk_mgr.calculate_sl_tp_atr(df, signal)
    lot = risk_mgr.calculate_lot_size(SYMBOL, sl_pips)

    # 6. Eksekusi order
    result = trader.open_trade(
        symbol=SYMBOL,
        signal=signal,
        lot=lot,
        sl_pips=sl_pips,
        tp_pips=tp_pips,
        comment=f"EA-{signal[:1]}-{MAGIC_NUMBER}"
    )

    # 7. Kirim notifikasi
    if result:
        notifier.notify_trade_open(
            signal=signal,
            symbol=SYMBOL,
            price=result["price"],
            sl=result["sl"],
            tp=result["tp"],
            lot=result["lot"],
            ticket=result["ticket"]
        )


def daily_report():
    """Kirim laporan harian setiap jam 22:00."""
    acc = mt5.account_info()
    if acc is None:
        return

    history = mt5.history_deals_get(
        datetime.now().replace(hour=0, minute=0),
        datetime.now()
    )
    deals    = [d for d in (history or []) if d.magic == MAGIC_NUMBER]
    profits  = [d.profit for d in deals if d.entry == 1]
    wins     = sum(1 for p in profits if p > 0)
    win_rate = (wins / len(profits) * 100) if profits else 0

    notifier.notify_daily_report(
        balance=acc.balance,
        equity=acc.equity,
        daily_profit=sum(profits),
        total_trades=len(profits),
        win_rate=win_rate
    )
    logger.info(f"📋 Laporan harian dikirim | Profit: ${sum(profits):.2f}")


def main():
    logger.info("=" * 55)
    logger.info("   🤖 EA Trading Forex Python — STARTING")
    logger.info("=" * 55)

    # Koneksi ke MT5
    if not connector.connect():
        logger.critical("❌ Gagal terhubung ke MT5. EA berhenti.")
        return

    # Jadwal: jalankan setiap 60 detik (sesuaikan dengan timeframe)
    schedule.every(60).seconds.do(run_ea)
    schedule.every().day.at("22:00").do(daily_report)

    notifier.send_message("🤖 <b>EA Trading Python aktif!</b>\n"
                          f"📌 Simbol: {SYMBOL} | TF: H1")

    logger.info(f"✅ EA aktif | Simbol: {SYMBOL} | Monitoring dimulai...")

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("⛔ EA dihentikan oleh user.")
    except Exception as e:
        logger.critical(f"❌ Error tidak terduga: {e}", exc_info=True)
    finally:
        connector.disconnect()
        notifier.send_message("⛔ <b>EA Trading Python berhenti.</b>")


if __name__ == "__main__":
    main()
```

---

### `utils/logger.py` — Setup Logging

```python
import logging
import colorlog
from pathlib import Path

def setup_logger(log_file: str = "logs/ea_trading.log") -> logging.Logger:
    Path("logs").mkdir(exist_ok=True)

    formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s [%(levelname)s]%(reset)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            "DEBUG":    "cyan",
            "INFO":     "green",
            "WARNING":  "yellow",
            "ERROR":    "red",
            "CRITICAL": "bold_red",
        }
    )

    handler_console = colorlog.StreamHandler()
    handler_console.setFormatter(formatter)

    handler_file = logging.FileHandler(log_file, encoding="utf-8")
    handler_file.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s"
    ))

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(handler_console)
    logger.addHandler(handler_file)

    return logger
```

---

## 📊 Modul Analisa Teknikal

### Indikator yang Digunakan

| Indikator | Parameter | Fungsi |
|-----------|-----------|--------|
| EMA 21 | Fast | Trend jangka pendek |
| EMA 50 | Slow | Trend jangka menengah |
| EMA 200 | Trend Filter | Konfirmasi trend utama |
| RSI 14 | 14 period | Filter overbought/oversold |
| MACD | 12/26/9 | Konfirmasi momentum |
| Bollinger Bands | 20/2σ | Volatilitas & reversal |
| ATR 14 | 14 period | SL/TP dinamis |

### Logika Sinyal

```
SIGNAL BUY  (minimal 5/6 kondisi):
  ✓ EMA 21 crossover ke atas EMA 50
  ✓ RSI < 70 (belum overbought)
  ✓ RSI > 40 (momentum positif)
  ✓ MACD histogram positif
  ✓ Harga di atas EMA 200
  ✓ EMA 21 > EMA 50 > EMA 200

SIGNAL SELL (minimal 5/6 kondisi):
  ✓ EMA 21 crossover ke bawah EMA 50
  ✓ RSI > 30 (belum oversold)
  ✓ RSI < 60 (momentum negatif)
  ✓ MACD histogram negatif
  ✓ Harga di bawah EMA 200
  ✓ EMA 21 < EMA 50 < EMA 200
```

---

## 🛡️ Modul Risk Management

### Kalkulasi Lot Size (Risk-Based)

```
Lot = (Balance × Risk%) ÷ (SL in pips × Pip Value per Lot)

Contoh:
  Balance    = $10,000
  Risk       = 1% → $100
  SL         = 50 pips
  Pip Value  = $10/lot (EURUSD standard)

  Lot = $100 ÷ (50 × $10) = 0.2 lot
```

### Parameter Proteksi

| Parameter | Nilai Default | Keterangan |
|-----------|--------------|-----------|
| Max Risk per Trade | 1% | Dari balance |
| Max Open Trades | 3 | Simultan |
| SL (ATR-based) | ATR × 1.5 | Dinamis |
| TP (ATR-based) | ATR × 3.0 | R:R = 1:2 |
| Trailing Stop | 20 pips | Otomatis |
| Min Margin Level | 150% | Circuit breaker |

---

## 📱 Modul Notifikasi Telegram

### Setup Bot Telegram

1. Buka Telegram → cari **@BotFather**
2. Ketik `/newbot` → ikuti instruksi → dapat **BOT_TOKEN**
3. Kirim pesan ke bot Anda
4. Buka `https://api.telegram.org/bot<TOKEN>/getUpdates`
5. Salin **chat_id** dari response JSON
6. Masukkan ke file `.env`

### Jenis Notifikasi

| Event | Isi Pesan |
|-------|-----------|
| Trade Open | Simbol, arah, price, SL, TP, lot, ticket |
| Trade Close | Simbol, ticket, profit/loss, pips |
| Laporan Harian | Balance, equity, total profit, win rate |
| Error/Alert | Pesan error dengan stack trace |

---

## ▶️ Cara Menjalankan

### Langkah 1 — Clone & Install

```bash
git clone https://github.com/yourname/forex_ea.git
cd forex_ea
pip install -r requirements.txt
```

### Langkah 2 — Konfigurasi

```bash
cp .env.example .env
# Edit .env dengan akun MT5 dan token Telegram Anda
```

### Langkah 3 — Pastikan MT5 Running

- Buka MetaTrader 5
- Login ke akun demo
- Aktifkan Algo Trading (tombol toolbar)

### Langkah 4 — Jalankan EA

```bash
python main.py
```

### Output yang Diharapkan

```
═══════════════════════════════════════════════════════
   🤖 EA Trading Forex Python — STARTING
═══════════════════════════════════════════════════════
2024-01-15 09:00:00 [INFO] ✅ Terhubung ke MT5 | Akun: 12345678 | Balance: $10,000.00
2024-01-15 09:00:01 [INFO] ✅ EA aktif | Simbol: EURUSD | Monitoring dimulai...
2024-01-15 09:01:00 [INFO] ⏰ Siklus EA | 2024-01-15 09:01:00
2024-01-15 09:01:01 [INFO] 📊 Signal: HOLD | {'rsi': 52.3, 'trend': 'UP'}
2024-01-15 09:02:00 [INFO] ⏰ Siklus EA | 2024-01-15 09:02:00
2024-01-15 09:02:01 [INFO] 📊 Signal: BUY | Score: 6/6
2024-01-15 09:02:02 [INFO] 💰 Kalkulasi Lot | Balance: $10,000.00 | Risk: $100.00 | Lot: 0.10
2024-01-15 09:02:02 [INFO] ✅ ORDER BUY | Ticket: 123456 | Price: 1.09250 | SL: 1.09000 | TP: 1.09750
```

### Jalankan sebagai Background Process (Windows)

```batch
@echo off
pythonw main.py
```

### Jalankan sebagai Background Process (Linux/Mac)

```bash
nohup python main.py > /dev/null 2>&1 &
echo "EA berjalan di background, PID: $!"
```

---

## 📈 Backtest & Optimasi

### Backtest Sederhana dengan Script

```python
# backtest.py
import pandas as pd
from strategy.indicators import calculate_indicators
from strategy.signals import SignalGenerator

def backtest(df_raw: pd.DataFrame, initial_balance: float = 10000):
    df = calculate_indicators(df_raw.copy())
    sg = SignalGenerator()

    balance  = initial_balance
    trades   = []
    position = None

    for i in range(200, len(df)):
        window = df.iloc[:i+1]
        signal = sg.get_signal(window)
        price  = df.iloc[i]["Close"]

        if signal == "BUY" and position is None:
            position = {"type": "BUY", "entry": price, "sl": price - 0.0050}

        elif signal == "SELL" and position is not None:
            pnl = (price - position["entry"]) * 10000  # dalam pips
            trades.append(pnl)
            balance += pnl
            position = None

    wins     = sum(1 for t in trades if t > 0)
    win_rate = wins / len(trades) * 100 if trades else 0
    total_pnl = sum(trades)

    print(f"Total Trades  : {len(trades)}")
    print(f"Win Rate      : {win_rate:.1f}%")
    print(f"Total P&L     : {total_pnl:.0f} pips")
    print(f"Final Balance : ${balance:.2f}")

    return trades
```

### Tips Optimasi

- **Forward Test** dulu di akun demo minimal **1 bulan** sebelum live
- Uji di minimal **3 pair** berbeda (EURUSD, GBPUSD, USDJPY)
- Atur `MAX_RISK_PERCENT = 0.5%` saat pertama kali live
- Monitor **drawdown** — hentikan EA jika drawdown > 10%
- Optimalkan parameter EMA dan RSI per pair secara terpisah

---

## 🔧 Troubleshooting

| Masalah | Solusi |
|---------|--------|
| `MT5 initialize gagal` | Pastikan MT5 sudah terbuka dan login |
| `Login MT5 gagal` | Cek kredensial di file `.env` |
| `Order gagal (10004)` | Requote — naikkan `deviation` ke 30 |
| `Order gagal (10014)` | Volume tidak valid — cek min lot broker |
| `Simbol tidak ditemukan` | Tambah simbol di Market Watch MT5 |
| `Telegram tidak terkirim` | Cek BOT_TOKEN dan CHAT_ID di `.env` |
| `Library ta tidak ada` | Jalankan `pip install ta` |
| Signal tidak muncul | Kurangi threshold dari 5/6 menjadi 4/6 |

---

## ⚠️ Disclaimer

> **PERINGATAN:** Trading forex mengandung risiko tinggi. EA ini dibuat untuk tujuan **edukasi dan penelitian**. Selalu:
> - Test di **akun demo** terlebih dahulu
> - Gunakan **risk management** yang ketat
> - Jangan gunakan uang yang tidak siap untuk hilang
> - Performa masa lalu **tidak menjamin** performa masa depan

---

*Dibuat dengan ❤️ untuk trader Indonesia*
*Versi: 1.0.0 | Python 3.10+ | MetaTrader 5*