import os
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from strategy.indicators import calculate_indicators
from strategy.signals import SignalGenerator
from config import format_currency



def backtest(df_raw: pd.DataFrame, initial_balance: float = 10000.0, pip_value_standard: float = 10.0):
    """
    Run backtest on raw OHLCV DataFrame.
    """
    df = calculate_indicators(df_raw.copy())
    sg = SignalGenerator()

    balance  = initial_balance
    trades   = []
    position = None

    logger_level = sg.logger.level if hasattr(sg, 'logger') else None
    # Temporarily mute logging inside signal generator to prevent flooding terminal
    import logging
    logging.getLogger('strategy.signals').setLevel(logging.WARNING)

    print("\n⌛ Menjalankan Simulasi Backtest...")
    
    # Needs at least 200 candles for EMA trend calculation filter
    start_idx = max(200, min(200, len(df) - 5))
    if len(df) <= start_idx:
        print("❌ Data terlalu pendek untuk backtest. Butuh minimal 200 bar.")
        return []

    for i in range(start_idx, len(df)):
        window = df.iloc[:i+1]
        signal = sg.get_signal(window)
        price  = df.iloc[i]["Close"]

        # BUY trigger
        if signal == "BUY" and position is None:
            position = {"type": "BUY", "entry": price, "sl": price - 0.0050, "index": i}
            print(f"   [BUY OPEN] Candle #{i} | Entry Price: {price:.5f}")

        # SELL trigger closes BUY position
        elif signal == "SELL" and position is not None:
            entry_price = position["entry"]
            pnl_pips = (price - entry_price) * 10000  # for Standard 5-digit pairs
            
            # Simple profit multiplier based on standard lots
            profit = pnl_pips * pip_value_standard * 0.1 # assuming 0.1 lot
            balance += profit
            trades.append(profit)
            
            print(f"   [BUY CLOSE] Candle #{i} | Exit Price: {price:.5f} | P&L Pips: {pnl_pips:.1f} | Profit: {format_currency(profit)} | Balance: {format_currency(balance)}")
            position = None

    # Reset logging level
    if logger_level:
        logging.getLogger('strategy.signals').setLevel(logger_level)

    wins     = sum(1 for t in trades if t > 0)
    losses   = sum(1 for t in trades if t <= 0)
    win_rate = wins / len(trades) * 100 if trades else 0
    total_pnl = sum(trades)

    print("\n" + "=" * 45)
    print("📊 HASIL BACKTEST EXPERT ADVISOR")
    print("=" * 45)
    print(f"Modal Awal      : {format_currency(initial_balance)}")
    print(f"Saldo Akhir     : {format_currency(balance)}")
    print(f"Total P&L       : {format_currency(total_pnl)}")
    print(f"Total Trades    : {len(trades)} (Wins: {wins}, Losses: {losses})")
    print(f"Win Rate        : {win_rate:.1f}%")
    print("=" * 45 + "\n")

    return trades

def generate_mock_history(candles_count: int = 500) -> pd.DataFrame:
    """Generate sample market candles for demonstration purposes."""
    print(f"🔧 Membuat {candles_count} bar data pasar tiruan untuk EURUSD...")
    np.random.seed(123)
    dates = [datetime.now() - timedelta(hours=i) for i in range(candles_count)]
    dates.reverse()
    
    # Random walk close prices
    close_prices = 1.0800 + np.cumsum(np.random.randn(candles_count) * 0.0012)
    high_prices = close_prices + np.random.rand(candles_count) * 0.0015
    low_prices = close_prices - np.random.rand(candles_count) * 0.0015
    open_prices = np.roll(close_prices, 1)
    open_prices[0] = 1.0800
    
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
            # Detect extension
            if filepath.endswith('.csv'):
                df = pd.read_csv(filepath, parse_dates=True, index_col=0)
            else:
                df = pd.read_excel(filepath, parse_dates=True, index_col=0)
            backtest(df)
        else:
            print(f"❌ File {filepath} tidak ditemukan.")
    else:
        print("💡 Petunjuk: Anda bisa memasukkan file CSV sebagai parameter: `python backtest.py data.csv`")
        df_mock = generate_mock_history(1000)
        backtest(df_mock)
