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
        self.MIN_ATR_PIPS = 3.0   # Minimal 3 pip ATR agar worth scalping

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
        if HAS_MT5:
            import MetaTrader5 as native_mt5
            sym = native_mt5.symbol_info(SYMBOL)
            point = sym.point if sym else 0.00001
        else:
            point = 0.00001
        pip   = 10 * point
        atr_pips = cur["atr"] / pip if "atr" in cur else 0.0

        if atr_pips < self.MIN_ATR_PIPS:
            logger.debug(f"ATR terlalu kecil: {atr_pips:.1f} pips — HOLD")
            return "HOLD"

        # ── Signal BUY ─────────────────────────────────
        if trend == "BULL":
            buy_score = 0
            buy_score += 1 if cur.get("cross_up") else 0                   # EMA crossover
            buy_score += 1 if 40 <= cur.get("rsi", 50) <= 65 else 0        # RSI zona
            buy_score += 1 if cur.get("stoch_k", 50) < STOCH_OB else 0     # Stoch belum OB
            buy_score += 1 if cur.get("stoch_k", 50) > cur.get("stoch_d", 50) else 0   # Stoch naik
            buy_score += 1 if cur.get("Close", 0) > cur.get("bb_mid", 0) else 0       # Di atas BB mid
            buy_score += 1 if cur.get("ema_fast", 0) > cur.get("ema_slow", 0) else 0 # EMA alignment

            logger.debug(f"[BUY] Score: {buy_score}/6 | RSI: {cur.get('rsi', 0):.1f} | "
                         f"Stoch: {cur.get('stoch_k', 0):.1f} | ATR: {atr_pips:.1f}p")

            # Minimal 4/6 kondisi + wajib ada crossover
            if buy_score >= 4 and cur.get("cross_up"):
                logger.info(f"⚡ SCALP BUY | Score: {buy_score}/6 | "
                            f"RSI: {cur.get('rsi', 0):.1f} | ATR: {atr_pips:.1f}p")
                return "BUY"

        # ── Signal SELL ────────────────────────────────
        elif trend == "BEAR":
            sell_score = 0
            sell_score += 1 if cur.get("cross_down") else 0                # EMA crossover
            sell_score += 1 if 35 <= cur.get("rsi", 50) <= 60 else 0       # RSI zona
            sell_score += 1 if cur.get("stoch_k", 50) > STOCH_OS else 0    # Stoch belum OS
            sell_score += 1 if cur.get("stoch_k", 50) < cur.get("stoch_d", 50) else 0  # Stoch turun
            sell_score += 1 if cur.get("Close", 0) < cur.get("bb_mid", 0) else 0      # Di bawah BB mid
            sell_score += 1 if cur.get("ema_fast", 0) < cur.get("ema_slow", 0) else 0 # EMA alignment

            logger.debug(f"[SELL] Score: {sell_score}/6 | RSI: {cur.get('rsi', 0):.1f} | "
                         f"Stoch: {cur.get('stoch_k', 0):.1f} | ATR: {atr_pips:.1f}p")

            if sell_score >= 4 and cur.get("cross_down"):
                logger.info(f"⚡ SCALP SELL | Score: {sell_score}/6 | "
                            f"RSI: {cur.get('rsi', 0):.1f} | ATR: {atr_pips:.1f}p")
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
