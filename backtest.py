import os
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from strategy.indicators import calculate_m5_indicators, calculate_m15_indicators
from strategy.signals import ScalpingSignal
from config import format_currency

logger = logging.getLogger(__name__)

def backtest(df_m5_raw: pd.DataFrame, initial_balance: float = 10000.0, pip_value_standard: float = 10.0):
    """
    Run backtest on raw M5 OHLCV DataFrame using the new Scalping M5/M15 strategy.
    """
    print("⌛ Menghitung indikator M5...")
    df_m5 = calculate_m5_indicators(df_m5_raw.copy())

    print("⌛ Meresample data ke M15 untuk tren filter...")
    # Resample M5 to M15
    df_m15_raw = df_m5_raw.resample('15min').agg({
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
        'Volume': 'sum'
    }).dropna()
    df_m15 = calculate_m15_indicators(df_m15_raw)

    sg = ScalpingSignal()

    balance  = initial_balance
    trades   = []
    position = None

    # Mute logging inside signal generator during backtest to prevent clutter
    sig_logger = logging.getLogger('strategy.signals')
    old_level = sig_logger.level
    sig_logger.setLevel(logging.WARNING)

    print("\n⌛ Menjalankan Simulasi Backtest Scalping...")
    
    # Needs enough bars for indicators
    start_idx = 100
    if len(df_m5) <= start_idx:
        print("❌ Data M5 terlalu pendek untuk backtest. Butuh minimal 100 bar.")
        return []

    # Point & pip values
    point = 0.00001
    pip = 10 * point

    # Parameters from config
    tp_pips = 10.0
    sl_pips = 8.0
    be_pips = 5.0
    trail_start_pips = 7.0
    trail_step_pips = 3.0

    for i in range(start_idx, len(df_m5)):
        t_m5 = df_m5.index[i]
        
        # 1. Get trend from M15 candle closed before/at current M5 time
        # M15 candle starting at T closes at T + 15 min. So at t_m5, we check candles where index <= t_m5 - 15min.
        available_m15 = df_m15[df_m15.index <= t_m5 - timedelta(minutes=15)]
        if available_m15.empty:
            trend = "NEUTRAL"
        else:
            last_m15 = available_m15.iloc[-1]
            if last_m15.get("trend_bull"):
                trend = "BULL"
            elif last_m15.get("trend_bear"):
                trend = "BEAR"
            else:
                trend = "NEUTRAL"

        # 2. Check position lifecycle if open
        if position is not None:
            high = df_m5.iloc[i]["High"]
            low = df_m5.iloc[i]["Low"]
            close = df_m5.iloc[i]["Close"]
            
            entry = position["entry"]
            sl = position["sl"]
            tp = position["tp"]
            p_type = position["type"]
            ticket = position["ticket"]
            
            closed = False
            exit_price = 0.0
            pnl_pips = 0.0
            
            if p_type == "BUY":
                # Check Target Profit or Stop Loss
                if low <= sl:
                    exit_price = sl
                    pnl_pips = (exit_price - entry) / pip
                    closed = True
                    reason = "Stop Loss ❌"
                elif high >= tp:
                    exit_price = tp
                    pnl_pips = (exit_price - entry) / pip
                    closed = True
                    reason = "Take Profit ✅"
                else:
                    # Manage Breakeven (+5 pips)
                    current_max_profit = (high - entry) / pip
                    if current_max_profit >= be_pips and sl < entry:
                        position["sl"] = entry + 1 * pip  # Move SL to BE + 1 pip
                        sl = position["sl"]
                        print(f"   [🔒 BE UPDATE] Candle #{i} | Ticket: {ticket} | SL digeser ke BE+1: {sl:.5f}")
                    
                    # Manage Trailing Stop (Start at +7 pips, step 3 pips)
                    current_profit = (close - entry) / pip
                    if current_profit >= trail_start_pips:
                        new_sl = close - trail_step_pips * pip
                        if new_sl > sl:
                            position["sl"] = new_sl
                            sl = new_sl
                            print(f"   [🔄 TRAIL UPDATE] Candle #{i} | Ticket: {ticket} | SL digeser ke: {sl:.5f}")
                            
            elif p_type == "SELL":
                # Check Target Profit or Stop Loss
                if high >= sl:
                    exit_price = sl
                    pnl_pips = (entry - exit_price) / pip
                    closed = True
                    reason = "Stop Loss ❌"
                elif low <= tp:
                    exit_price = tp
                    pnl_pips = (entry - exit_price) / pip
                    closed = True
                    reason = "Take Profit ✅"
                else:
                    # Manage Breakeven (+5 pips)
                    current_max_profit = (entry - low) / pip
                    if current_max_profit >= be_pips and (sl > entry or sl == 0):
                        position["sl"] = entry - 1 * pip  # Move SL to BE - 1 pip
                        sl = position["sl"]
                        print(f"   [🔒 BE UPDATE] Candle #{i} | Ticket: {ticket} | SL digeser ke BE-1: {sl:.5f}")
                    
                    # Manage Trailing Stop (Start at +7 pips, step 3 pips)
                    current_profit = (entry - close) / pip
                    if current_profit >= trail_start_pips:
                        new_sl = close + trail_step_pips * pip
                        if new_sl < sl or sl == 0:
                            position["sl"] = new_sl
                            sl = new_sl
                            print(f"   [🔄 TRAIL UPDATE] Candle #{i} | Ticket: {ticket} | SL digeser ke: {sl:.5f}")

            if closed:
                # Lot size 0.1 lot, pip value = standard * 0.1
                profit = pnl_pips * pip_value_standard * 0.1
                balance += profit
                trades.append(profit)
                print(f"   [SCALP CLOSE] Candle #{i} | Exit: {exit_price:.5f} | P&L: {pnl_pips:+.1f} pips | Profit: {format_currency(profit)} | Alasan: {reason}")
                position = None

        # 3. Check for new signals if no position is open
        if position is None:
            window = df_m5.iloc[:i+1]
            signal = sg.get_signal(window, trend)
            
            if signal in ["BUY", "SELL"]:
                entry_price = df_m5.iloc[i]["Close"]
                ticket = 100000 + i
                
                if signal == "BUY":
                    sl = entry_price - sl_pips * pip
                    tp = entry_price + tp_pips * pip
                else:
                    sl = entry_price + sl_pips * pip
                    tp = entry_price - tp_pips * pip
                
                position = {
                    "ticket": ticket,
                    "type": signal,
                    "entry": entry_price,
                    "sl": sl,
                    "tp": tp
                }
                print(f"   [SCALP OPEN] Candle #{i} | {signal} | Entry: {entry_price:.5f} | SL: {sl:.5f} | TP: {tp:.5f} | Trend: {trend}")

    # Reset logging level
    sig_logger.setLevel(old_level)

    wins     = sum(1 for t in trades if t > 0)
    losses   = sum(1 for t in trades if t <= 0)
    win_rate = wins / len(trades) * 100 if trades else 0
    total_pnl = sum(trades)

    print("\n" + "=" * 45)
    print("📊 HASIL BACKTEST SCALPING M5/M15")
    print("=" * 45)
    print(f"Modal Awal      : {format_currency(initial_balance)}")
    print(f"Saldo Akhir     : {format_currency(balance)}")
    print(f"Total P&L       : {format_currency(total_pnl)}")
    print(f"Total Trades    : {len(trades)} (Wins: {wins}, Losses: {losses})")
    print(f"Win Rate        : {win_rate:.1f}%")
    print("=" * 45 + "\n")

    return trades

def generate_mock_history(candles_count: int = 1500) -> pd.DataFrame:
    """Generate sample M5 market candles for demonstration purposes."""
    print(f"🔧 Membuat {candles_count} bar data pasar M5 tiruan untuk EURUSD...")
    np.random.seed(1234)
    dates = [datetime.now() - timedelta(minutes=5 * i) for i in range(candles_count)]
    dates.reverse()
    
    # Generate prices with clear trends
    close_prices = np.zeros(candles_count)
    current_price = 1.0850
    for i in range(candles_count):
        # Add a bias depending on index to create trends
        bias = 0.0
        if 200 <= i < 500:
            bias = 0.0001  # Uptrend
        elif 600 <= i < 900:
            bias = -0.00015  # Downtrend
        elif 1000 <= i < 1300:
            bias = 0.00008  # Slighter uptrend
            
        current_price += bias + np.random.randn() * 0.0002
        close_prices[i] = current_price

    high_prices = close_prices + np.random.rand(candles_count) * 0.0004
    low_prices = close_prices - np.random.rand(candles_count) * 0.0004
    open_prices = np.roll(close_prices, 1)
    open_prices[0] = 1.0850
    
    # Introduce occasional spikes for ATR
    for i in range(0, candles_count, 50):
        high_prices[i] += 0.0006
        low_prices[i] -= 0.0006

    df = pd.DataFrame({
        "Open": open_prices,
        "High": high_prices,
        "Low": low_prices,
        "Close": close_prices,
        "Volume": np.random.randint(100, 1000, size=candles_count)
    }, index=dates)
    df.index.name = "time"
    return df

if __name__ == "__main__":
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        if os.path.exists(filepath):
            print(f"📂 Membaca data historis dari {filepath}...")
            if filepath.endswith('.csv'):
                df = pd.read_csv(filepath, parse_dates=True, index_col=0)
            else:
                df = pd.read_excel(filepath, parse_dates=True, index_col=0)
            backtest(df)
        else:
            print(f"❌ File {filepath} tidak ditemukan.")
    else:
        print("💡 Petunjuk: Anda bisa memasukkan file CSV sebagai parameter: `python backtest.py data.csv`")
        df_mock = generate_mock_history(1500)
        backtest(df_mock)
