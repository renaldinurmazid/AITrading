import pandas as pd
import numpy as np
from ta.trend import EMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands, AverageTrueRange
from config import *

if HAS_MT5:
    import MetaTrader5 as mt5
else:
    mt5 = None

def get_candles(symbol: str, timeframe, n_candles: int = 300) -> pd.DataFrame:
    """Ambil data candle dari MT5 dan konversi ke DataFrame."""
    if not HAS_MT5 or mt5 is None:
        # Returns an empty DataFrame on macOS/Linux since MT5 is unavailable
        return pd.DataFrame()

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
    if df.empty or len(df) < 2:
        return df

    close = df["Close"]
    high  = df["High"]
    low   = df["Low"]

    # Calculate indicators, handling potential small DataFrame boundary checks
    # ── EMA ────────────────────────────────────────────
    df["ema_fast"]  = EMAIndicator(close, window=min(EMA_FAST, len(df))).ema_indicator()
    df["ema_slow"]  = EMAIndicator(close, window=min(EMA_SLOW, len(df))).ema_indicator()
    df["ema_trend"] = EMAIndicator(close, window=min(EMA_TREND, len(df))).ema_indicator()

    # ── RSI ────────────────────────────────────────────
    rsi = RSIIndicator(close, window=min(RSI_PERIOD, len(df)))
    df["rsi"] = rsi.rsi()

    # ── MACD ───────────────────────────────────────────
    macd_indicator = MACD(close,
                          window_slow=min(MACD_SLOW, len(df)),
                          window_fast=min(MACD_FAST, len(df)),
                          window_sign=min(MACD_SIGNAL, len(df)))
    df["macd"]        = macd_indicator.macd()
    df["macd_signal"] = macd_indicator.macd_signal()
    df["macd_hist"]   = macd_indicator.macd_diff()

    # ── Bollinger Bands ────────────────────────────────
    bb = BollingerBands(close, window=min(BB_PERIOD, len(df)), window_dev=BB_STD)
    df["bb_upper"] = bb.bollinger_hband()
    df["bb_lower"] = bb.bollinger_lband()
    df["bb_mid"]   = bb.bollinger_mavg()
    df["bb_width"] = bb.bollinger_wband()

    # ── ATR (untuk SL dinamis) ─────────────────────────
    atr = AverageTrueRange(high, low, close, window=min(14, len(df)))
    df["atr"] = atr.average_true_range()

    # ── Trend Filter ───────────────────────────────────
    df["trend_up"]   = (df["ema_fast"] > df["ema_slow"]) & \
                       (df["ema_slow"] > df["ema_trend"])
    df["trend_down"] = (df["ema_fast"] < df["ema_slow"]) & \
                       (df["ema_slow"] < df["ema_trend"])

    return df
