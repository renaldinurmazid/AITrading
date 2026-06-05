import pandas as pd
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands, AverageTrueRange
from config import *

if HAS_MT5:
    import MetaTrader5 as mt5
else:
    mt5 = None

def get_candles(symbol: str, timeframe, n: int = 150) -> pd.DataFrame:
    """Ambil data OHLCV dari MT5."""
    if not HAS_MT5 or mt5 is None:
        return pd.DataFrame()
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
    df["ema_fast"] = EMAIndicator(close, window=min(EMA_FAST_M5, len(df))).ema_indicator()
    df["ema_slow"] = EMAIndicator(close, window=min(EMA_SLOW_M5, len(df))).ema_indicator()

    # ── RSI Pendek (lebih sensitif untuk scalping) ─────
    df["rsi"] = RSIIndicator(close, window=min(RSI_PERIOD_M5, len(df))).rsi()

    # ── Stochastic Oscillator ──────────────────────────
    stoch = StochasticOscillator(
        high=high, low=low, close=close,
        window=min(STOCH_K, len(df)), smooth_window=min(STOCH_D, len(df))
    )
    df["stoch_k"] = stoch.stoch()
    df["stoch_d"] = stoch.stoch_signal()

    # ── Bollinger Bands ────────────────────────────────
    bb = BollingerBands(close, window=min(BB_PERIOD, len(df)), window_dev=2)
    df["bb_upper"] = bb.bollinger_hband()
    df["bb_lower"] = bb.bollinger_lband()
    df["bb_mid"]   = bb.bollinger_mavg()
    df["bb_pct"]   = bb.bollinger_pband()  # 0=lower, 1=upper

    # ── ATR untuk filter volatilitas ───────────────────
    df["atr"] = AverageTrueRange(high, low, close, window=min(7, len(df))).average_true_range()

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
    if df.empty or len(df) < min(EMA_TREND_M15 + 10, len(df)):
        return df

    close = df["Close"]
    df["ema_mid"]   = EMAIndicator(close, window=min(EMA_MID_M15, len(df))).ema_indicator()
    df["ema_trend"] = EMAIndicator(close, window=min(EMA_TREND_M15, len(df))).ema_indicator()

    df["trend_bull"] = df["ema_mid"] > df["ema_trend"]
    df["trend_bear"] = df["ema_mid"] < df["ema_trend"]

    return df

def get_trend_direction(symbol: str) -> str:
    """Ambil arah trend dari M15."""
    if not HAS_MT5 or mt5 is None:
        return "BULL"  # Default mock untuk macOS development

    df_m15 = get_candles(symbol, TF_TREND, n=220)
    if df_m15.empty:
        return "NEUTRAL"

    df_m15 = calculate_m15_indicators(df_m15)
    if df_m15.empty or "trend_bull" not in df_m15.columns:
        return "NEUTRAL"

    last = df_m15.iloc[-1]
    if last["trend_bull"]:
        return "BULL"
    elif last["trend_bear"]:
        return "BEAR"
    return "NEUTRAL"
