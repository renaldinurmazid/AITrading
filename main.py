import os
import time
import logging
import schedule
from datetime import datetime

from config import SYMBOL, TIMEFRAME, MAGIC_NUMBER, TRAILING_STOP, HAS_MT5, format_currency


from core.connector import MT5Connector
from core.trader import Trader
from core.monitor import PositionMonitor
from strategy.indicators import get_candles, calculate_indicators
from strategy.signals import SignalGenerator
from risk.manager import RiskManager
from utils.notifier import TelegramNotifier
from utils.logger import setup_logger

if HAS_MT5:
    import MetaTrader5 as mt5
else:
    mt5 = None

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
    
    # Fallback to dummy data for local macOS validation/testing
    if df.empty and not HAS_MT5:
        logger.debug("Generating mock market data for local platform validation")
        import numpy as np
        dates = pd.date_range(end=datetime.now(), periods=300, freq='h')

        np.random.seed(42)
        close_prices = 1.1000 + np.cumsum(np.random.randn(300) * 0.0005)
        high_prices = close_prices + np.random.rand(300) * 0.0010
        low_prices = close_prices - np.random.rand(300) * 0.0010
        open_prices = np.roll(close_prices, 1)
        open_prices[0] = 1.1000
        
        df = pd.DataFrame({
            "Open": open_prices, "High": high_prices,
            "Low": low_prices, "Close": close_prices, "Volume": np.random.randint(100, 1000, size=300)
        }, index=dates)
        df.index.name = "time"

    if df.empty:
        logger.warning("Data candle kosong, skip siklus ini.")
        return

    # 2. Hitung indikator
    df = calculate_indicators(df)

    # 3. Cek signal
    signal = signal_gen.get_signal(df)
    strength = signal_gen.get_signal_strength(df)
    logger.info(f"📊 Signal: {signal} | {strength}")

    # Log current open positions for transparency
    monitor.log_open_positions_summary()

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
    if not HAS_MT5 or mt5 is None:
        logger.info(f"📋 Laporan harian: [MOCK] Profit: {format_currency(0.0)} | Trades: 0 | Win Rate: 0%")
        notifier.notify_daily_report(
            balance=10000.0,
            equity=10000.0,
            daily_profit=0.0,
            total_trades=0,
            win_rate=0.0
        )
        return

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
    logger.info(f"📋 Laporan harian dikirim | Profit: {format_currency(sum(profits))}")


def main():
    logger.info("=" * 55)
    logger.info("   🤖 EA Trading Forex Python — STARTING")
    logger.info("=" * 55)

    # Koneksi ke MT5
    if not connector.connect():
        if not HAS_MT5:
            logger.warning("⚠️ EA berjalan dalam mode Simulasi/Mock karena keterbatasan OS.")
        else:
            logger.critical("❌ Gagal terhubung ke MT5. EA berhenti.")
            return

    # Jadwal: jalankan setiap 60 detik (sesuaikan dengan timeframe)
    schedule.every(60).seconds.do(run_ea)
    schedule.every().day.at("22:00").do(daily_report)

    notifier.send_message("🤖 <b>EA Trading Python aktif!</b>\n"
                          f"📌 Simbol: {SYMBOL} | TF: {os.getenv('TIMEFRAME', 'H1').upper()}")

    logger.info(f"✅ EA aktif | Simbol: {SYMBOL} | Monitoring dimulai...")

    # Run the EA cycle once immediately on start for validation
    run_ea()

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
    import pandas as pd # Import pandas here as it is needed in run_ea fallback
    main()
