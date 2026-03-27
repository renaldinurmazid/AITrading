"""
Technical Analysis Module
Calculates technical indicators and generates signals from OHLCV data.
Uses the 'ta' library (Technical Analysis Library in Python).
"""
import logging
from typing import Optional

import numpy as np
import pandas as pd
import ta as ta_lib

logger = logging.getLogger("AITrading.TA")


class TechnicalAnalyzer:
    """
    Performs technical analysis on OHLCV data using multiple indicators.
    Generates trading signals based on indicator confluence.
    """

    def __init__(self):
        self.indicators_config = {
            # Trend
            "ema_fast": 9,
            "ema_mid": 21,
            "ema_slow": 50,
            "ema_trend": 200,
            # Momentum
            "rsi_period": 14,
            "macd_fast": 12,
            "macd_slow": 26,
            "macd_signal": 9,
            "stoch_k": 14,
            "stoch_d": 3,
            # Volatility
            "bb_period": 20,
            "bb_std": 2.0,
            "atr_period": 14,
        }

    def analyze(self, df: pd.DataFrame) -> dict:
        """
        Run full technical analysis on OHLCV dataframe.

        Returns a dict with:
        - indicators: dict of latest indicator values
        - signals: list of signal dicts
        - trend: overall trend assessment
        - strength: signal strength (0-100)
        - recommendation: BUY / SELL / HOLD
        """
        if df is None or df.empty or len(df) < 200:
            logger.warning("Insufficient data for analysis")
            return {
                "indicators": {},
                "signals": [],
                "trend": "NEUTRAL",
                "strength": 0,
                "recommendation": "HOLD",
            }

        # Calculate all indicators
        indicators = self._calculate_indicators(df)
        # Generate signals
        signals = self._generate_signals(df, indicators)
        # Determine overall trend
        trend = self._assess_trend(indicators)
        # Calculate signal strength
        strength = self._calculate_strength(signals)
        # Final recommendation
        recommendation = self._get_recommendation(signals, trend, strength)

        return {
            "indicators": indicators,
            "signals": signals,
            "trend": trend,
            "strength": strength,
            "recommendation": recommendation,
            "last_close": float(df["close"].iloc[-1]),
            "last_time": str(df.index[-1]),
        }

    def _calculate_indicators(self, df: pd.DataFrame) -> dict:
        """Calculate all technical indicators using 'ta' library."""
        c = self.indicators_config
        close = df["close"]
        high = df["high"]
        low = df["low"]
        volume = df["volume"]

        # ── EMAs ─────────────────────────────────────────────
        ema_fast = ta_lib.trend.ema_indicator(close, window=c["ema_fast"])
        ema_mid = ta_lib.trend.ema_indicator(close, window=c["ema_mid"])
        ema_slow = ta_lib.trend.ema_indicator(close, window=c["ema_slow"])
        ema_trend = ta_lib.trend.ema_indicator(close, window=c["ema_trend"])

        # ── RSI ──────────────────────────────────────────────
        rsi = ta_lib.momentum.rsi(close, window=c["rsi_period"])

        # ── MACD ─────────────────────────────────────────────
        macd_line = ta_lib.trend.macd(close, window_slow=c["macd_slow"], window_fast=c["macd_fast"])
        macd_signal_line = ta_lib.trend.macd_signal(close, window_slow=c["macd_slow"], window_fast=c["macd_fast"], window_sign=c["macd_signal"])
        macd_histogram = ta_lib.trend.macd_diff(close, window_slow=c["macd_slow"], window_fast=c["macd_fast"], window_sign=c["macd_signal"])

        # ── Stochastic ───────────────────────────────────────
        stoch_k = ta_lib.momentum.stoch(high, low, close, window=c["stoch_k"], smooth_window=c["stoch_d"])
        stoch_d = ta_lib.momentum.stoch_signal(high, low, close, window=c["stoch_k"], smooth_window=c["stoch_d"])

        # ── Bollinger Bands ──────────────────────────────────
        bb = ta_lib.volatility.BollingerBands(close, window=c["bb_period"], window_dev=c["bb_std"])
        bb_upper = bb.bollinger_hband()
        bb_middle = bb.bollinger_mavg()
        bb_lower = bb.bollinger_lband()

        # ── ATR ──────────────────────────────────────────────
        atr = ta_lib.volatility.average_true_range(high, low, close, window=c["atr_period"])

        # ── ADX ──────────────────────────────────────────────
        adx = ta_lib.trend.adx(high, low, close, window=14)
        di_plus = ta_lib.trend.adx_pos(high, low, close, window=14)
        di_minus = ta_lib.trend.adx_neg(high, low, close, window=14)

        # ── OBV ──────────────────────────────────────────────
        obv = ta_lib.volume.on_balance_volume(close, volume)

        # Gather latest values safely
        def safe_last(series):
            if series is not None and len(series) > 0:
                val = series.iloc[-1]
                return float(val) if not pd.isna(val) else None
            return None

        return {
            # Trend
            "ema_9": safe_last(ema_fast),
            "ema_21": safe_last(ema_mid),
            "ema_50": safe_last(ema_slow),
            "ema_200": safe_last(ema_trend),
            "price_vs_ema200": "ABOVE"
            if close.iloc[-1] > (safe_last(ema_trend) or 0)
            else "BELOW",
            # Momentum
            "rsi": safe_last(rsi),
            "rsi_signal": self._rsi_signal(safe_last(rsi)),
            "macd_line": safe_last(macd_line),
            "macd_signal_line": safe_last(macd_signal_line),
            "macd_histogram": safe_last(macd_histogram),
            "stoch_k": safe_last(stoch_k),
            "stoch_d": safe_last(stoch_d),
            # Volatility
            "bb_upper": safe_last(bb_upper),
            "bb_middle": safe_last(bb_middle),
            "bb_lower": safe_last(bb_lower),
            "atr": safe_last(atr),
            # Trend strength
            "adx": safe_last(adx),
            "di_plus": safe_last(di_plus),
            "di_minus": safe_last(di_minus),
            # Volume
            "obv": safe_last(obv),
            # Current price
            "current_price": float(close.iloc[-1]),
        }

    def _generate_signals(self, df: pd.DataFrame, indicators: dict) -> list:
        """Generate trading signals from indicators."""
        signals = []
        close = float(df["close"].iloc[-1])

        # ── EMA Crossover Signal ─────────────────────────────
        ema9 = indicators.get("ema_9")
        ema21 = indicators.get("ema_21")
        if ema9 and ema21:
            if ema9 > ema21:
                signals.append(
                    {"name": "EMA_CROSS", "direction": "BUY", "weight": 1.5}
                )
            else:
                signals.append(
                    {"name": "EMA_CROSS", "direction": "SELL", "weight": 1.5}
                )

        # ── EMA 200 Trend Filter ─────────────────────────────
        ema200 = indicators.get("ema_200")
        if ema200:
            if close > ema200:
                signals.append(
                    {"name": "EMA200_TREND", "direction": "BUY", "weight": 2.0}
                )
            else:
                signals.append(
                    {"name": "EMA200_TREND", "direction": "SELL", "weight": 2.0}
                )

        # ── RSI Signal ───────────────────────────────────────
        rsi = indicators.get("rsi")
        if rsi:
            if rsi < 30:
                signals.append(
                    {"name": "RSI_OVERSOLD", "direction": "BUY", "weight": 2.0}
                )
            elif rsi > 70:
                signals.append(
                    {"name": "RSI_OVERBOUGHT", "direction": "SELL", "weight": 2.0}
                )
            elif 40 <= rsi <= 60:
                signals.append(
                    {"name": "RSI_NEUTRAL", "direction": "HOLD", "weight": 0.5}
                )

        # ── MACD Signal ──────────────────────────────────────
        macd_line = indicators.get("macd_line")
        macd_signal = indicators.get("macd_signal_line")
        macd_hist = indicators.get("macd_histogram")
        if macd_line is not None and macd_signal is not None:
            if macd_line > macd_signal:
                signals.append(
                    {"name": "MACD_CROSS", "direction": "BUY", "weight": 2.0}
                )
            else:
                signals.append(
                    {"name": "MACD_CROSS", "direction": "SELL", "weight": 2.0}
                )
            if macd_hist is not None:
                if macd_hist > 0 and abs(macd_hist) > abs(macd_line) * 0.1:
                    signals.append(
                        {"name": "MACD_MOMENTUM", "direction": "BUY", "weight": 1.0}
                    )
                elif macd_hist < 0 and abs(macd_hist) > abs(macd_line) * 0.1:
                    signals.append(
                        {"name": "MACD_MOMENTUM", "direction": "SELL", "weight": 1.0}
                    )

        # ── Bollinger Bands Signal ───────────────────────────
        bb_upper = indicators.get("bb_upper")
        bb_lower = indicators.get("bb_lower")
        if bb_upper and bb_lower:
            if close <= bb_lower:
                signals.append(
                    {"name": "BB_OVERSOLD", "direction": "BUY", "weight": 1.5}
                )
            elif close >= bb_upper:
                signals.append(
                    {"name": "BB_OVERBOUGHT", "direction": "SELL", "weight": 1.5}
                )

        # ── Stochastic Signal ────────────────────────────────
        stoch_k = indicators.get("stoch_k")
        stoch_d = indicators.get("stoch_d")
        if stoch_k and stoch_d:
            if stoch_k < 20 and stoch_k > stoch_d:
                signals.append(
                    {"name": "STOCH_OVERSOLD", "direction": "BUY", "weight": 1.5}
                )
            elif stoch_k > 80 and stoch_k < stoch_d:
                signals.append(
                    {"name": "STOCH_OVERBOUGHT", "direction": "SELL", "weight": 1.5}
                )

        # ── ADX Trend Strength ───────────────────────────────
        adx = indicators.get("adx")
        di_plus = indicators.get("di_plus")
        di_minus = indicators.get("di_minus")
        if adx and di_plus and di_minus and adx > 25:
            if di_plus > di_minus:
                signals.append(
                    {"name": "ADX_TREND", "direction": "BUY", "weight": 1.5}
                )
            else:
                signals.append(
                    {"name": "ADX_TREND", "direction": "SELL", "weight": 1.5}
                )

        return signals

    def _assess_trend(self, indicators: dict) -> str:
        """Assess overall market trend."""
        ema9 = indicators.get("ema_9")
        ema21 = indicators.get("ema_21")
        ema50 = indicators.get("ema_50")
        ema200 = indicators.get("ema_200")

        if not all([ema9, ema21, ema50, ema200]):
            return "NEUTRAL"

        # Strong uptrend: EMAs aligned EMA9 > EMA21 > EMA50 > EMA200
        if ema9 > ema21 > ema50 > ema200:
            return "STRONG_UPTREND"
        elif ema9 > ema21 > ema50:
            return "UPTREND"
        # Strong downtrend
        elif ema9 < ema21 < ema50 < ema200:
            return "STRONG_DOWNTREND"
        elif ema9 < ema21 < ema50:
            return "DOWNTREND"
        else:
            return "RANGING"

    def _calculate_strength(self, signals: list) -> int:
        """Calculate overall signal strength (0-100)."""
        if not signals:
            return 0

        buy_weight = sum(
            s["weight"] for s in signals if s["direction"] == "BUY"
        )
        sell_weight = sum(
            s["weight"] for s in signals if s["direction"] == "SELL"
        )
        total_weight = buy_weight + sell_weight

        if total_weight == 0:
            return 0

        # Strength is how much the dominant side outweighs
        dominant = max(buy_weight, sell_weight)
        strength = int((dominant / total_weight) * 100)
        return min(strength, 100)

    def _get_recommendation(
        self, signals: list, trend: str, strength: int
    ) -> str:
        """Determine final recommendation."""
        buy_weight = sum(
            s["weight"] for s in signals if s["direction"] == "BUY"
        )
        sell_weight = sum(
            s["weight"] for s in signals if s["direction"] == "SELL"
        )

        # Need minimum strength for action
        if strength < 55:
            return "HOLD"

        if buy_weight > sell_weight:
            if trend in ("STRONG_UPTREND", "UPTREND"):
                return "STRONG_BUY"
            return "BUY"
        elif sell_weight > buy_weight:
            if trend in ("STRONG_DOWNTREND", "DOWNTREND"):
                return "STRONG_SELL"
            return "SELL"

        return "HOLD"

    def _rsi_signal(self, rsi: Optional[float]) -> str:
        if rsi is None:
            return "NEUTRAL"
        if rsi < 30:
            return "OVERSOLD"
        elif rsi > 70:
            return "OVERBOUGHT"
        elif rsi < 40:
            return "BEARISH"
        elif rsi > 60:
            return "BULLISH"
        return "NEUTRAL"

    def get_support_resistance(
        self, df: pd.DataFrame, lookback: int = 100
    ) -> dict:
        """Identify key support and resistance levels."""
        if df is None or len(df) < lookback:
            return {"support": [], "resistance": []}

        recent = df.tail(lookback)
        highs = recent["high"].values
        lows = recent["low"].values
        close = float(df["close"].iloc[-1])

        # Simple pivot point calculation
        pivot = (highs.max() + lows.min() + close) / 3
        r1 = 2 * pivot - lows.min()
        r2 = pivot + (highs.max() - lows.min())
        s1 = 2 * pivot - highs.max()
        s2 = pivot - (highs.max() - lows.min())

        return {
            "pivot": round(float(pivot), 5),
            "support": [round(float(s1), 5), round(float(s2), 5)],
            "resistance": [round(float(r1), 5), round(float(r2), 5)],
        }
