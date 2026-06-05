import time
import logging
import schedule
import pandas as pd
from datetime import datetime

from config import *

# Try to import MetaTrader5, handle gracefully on non-Windows platforms
if HAS_MT5:
    import MetaTrader5 as mt5
else:
    mt5 = None

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
        return

    # Kirim notifikasi awal sesi (sekali saja)
    session_name = reason.split("—")[0].replace("Sesi", "").strip()
    if session_name != last_session_notif:
        last_session_notif = session_name
        if HAS_MT5 and mt5 is not None:
            sym    = mt5.symbol_info(SYMBOL)
            spread = sym.spread / 10 if sym else 0.0
            trend  = get_trend_direction(SYMBOL)
        else:
            spread = 0.5
            trend  = "BULL"
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
    
    # Fallback to dummy data for local macOS validation/testing
    if df_m5.empty and not HAS_MT5:
        logger.debug("Generating mock market data for local platform validation")
        import numpy as np
        dates = pd.date_range(end=datetime.now(), periods=100, freq='5min')
        np.random.seed(42)
        close_prices = 1.0800 + np.cumsum(np.random.randn(100) * 0.0005)
        high_prices = close_prices + np.random.rand(100) * 0.0010
        low_prices = close_prices - np.random.rand(100) * 0.0010
        open_prices = np.roll(close_prices, 1)
        open_prices[0] = 1.0800
        
        df_m5 = pd.DataFrame({
            "Open": open_prices, "High": high_prices,
            "Low": low_prices, "Close": close_prices, "Volume": np.random.randint(100, 1000, size=100)
        }, index=dates)
        df_m5.index.name = "time"

    if df_m5.empty:
        logger.warning("Data candle kosong, skip siklus ini.")
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
    if HAS_MT5 and mt5 is not None:
        tick  = mt5.symbol_info_tick(SYMBOL)
        price = tick.ask if signal == "BUY" else tick.bid
    else:
        price = 1.08500
    
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
    if not HAS_MT5 or mt5 is None:
        logger.info("📋 Summary Harian: [MOCK] Profit: $0.00 | Trades: 0 | Win Rate: 0%")
        notifier.alert_daily_summary(
            balance=10000.0,
            profit=0.0,
            trades=0,
            wins=0
        )
        return

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

    # Koneksi ke MT5
    if not connector.connect():
        if not HAS_MT5:
            logger.warning("⚠️ EA berjalan dalam mode Simulasi/Mock karena keterbatasan OS.")
        else:
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

    # Jalankan siklus pertama secara langsung untuk verifikasi
    run_scalping_cycle()

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
