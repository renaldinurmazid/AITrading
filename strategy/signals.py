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
        # Validasi ukuran data
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
            bool(buy_crossover),                      # EMA crossover ke atas
            bool(cur["rsi"] < RSI_OVERBOUGHT),        # RSI belum overbought
            bool(cur["rsi"] > 40),                    # RSI tidak terlalu lemah
            bool(cur["macd_hist"] > 0),               # MACD histogram positif
            bool(cur["Close"] > cur["ema_trend"]),    # Harga di atas EMA 200
            bool(cur["trend_up"]),                    # Konfirmasi trend naik
        ]

        # ── Kondisi SELL ──────────────────────────────
        sell_conditions = [
            bool(sell_crossover),                     # EMA crossover ke bawah
            bool(cur["rsi"] > RSI_OVERSOLD),          # RSI belum oversold
            bool(cur["rsi"] < 60),                    # RSI tidak terlalu kuat
            bool(cur["macd_hist"] < 0),               # MACD histogram negatif
            bool(cur["Close"] < cur["ema_trend"]),    # Harga di bawah EMA 200
            bool(cur["trend_down"]),                  # Konfirmasi trend turun
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
        if df.empty or len(df) == 0:
            return {}
        cur = df.iloc[-1]
        
        # Safe default values if columns are missing
        rsi_val = cur.get("rsi", 50.0)
        macd_hist_val = cur.get("macd_hist", 0.0)
        ema_fast_val = cur.get("ema_fast", 0.0)
        ema_slow_val = cur.get("ema_slow", 0.0)
        atr_val = cur.get("atr", 0.0)
        
        trend_up_val = cur.get("trend_up", False)
        trend_down_val = cur.get("trend_down", False)
        
        return {
            "rsi":       round(rsi_val, 2),
            "macd_hist": round(macd_hist_val, 5),
            "ema_spread": round(ema_fast_val - ema_slow_val, 5),
            "atr":       round(atr_val, 5),
            "trend":     "UP" if trend_up_val else
                         "DOWN" if trend_down_val else "SIDEWAYS",
        }
