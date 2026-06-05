import logging
import math
from config import *

logger = logging.getLogger(__name__)

if HAS_MT5:
    import MetaTrader5 as mt5
else:
    # Mock data definitions for risk manager on macOS/testing
    class MockMT5:
        class AccountInfo:
            def __init__(self):
                self.balance = 10000.0
                self.margin_level = 999.0
        class SymbolInfo:
            def __init__(self):
                self.point = 0.00001
                self.digits = 5
                self.trade_tick_value = 1.0
                self.volume_min = 0.01
                self.volume_max = 500.0
                self.volume_step = 0.01
                self.spread = 5.0  # 5 points = 0.5 pips
        class SymbolInfoTick:
            def __init__(self):
                self.bid = 1.08500
                self.ask = 1.08505
        
        def account_info(self):
            return self.AccountInfo()
        def symbol_info(self, symbol):
            return self.SymbolInfo()
        def symbol_info_tick(self, symbol):
            return self.SymbolInfoTick()
        def positions_get(self, **kwargs):
            return []
    mt5 = MockMT5()

class ScalpingRiskManager:
    """
    Risk management khusus scalping:
    - Lot berbasis % risk dari balance
    - SL fixed 8-12 pips
    - TP 5-15 pips (R:R minimal 1:1.2)
    - Breakeven otomatis setelah +5 pips
    - Max 2 posisi simultan
    """

    def check_spread(self, symbol: str) -> tuple:
        """
        Cek apakah spread saat ini acceptable untuk scalping.
        Tolak jika spread > MAX_SPREAD_PIPS.
        """
        tick = mt5.symbol_info_tick(symbol)
        sym  = mt5.symbol_info(symbol)
        if not tick or not sym:
            return False, 99.0

        spread_pips = sym.spread / 10  # Convert points ke pips
        if spread_pips > MAX_SPREAD_PIPS:
            logger.warning(f"⚠️ Spread terlalu lebar: {spread_pips:.1f} pips > {MAX_SPREAD_PIPS} pips")
            return False, spread_pips

        return True, spread_pips

    def calculate_lot(self, symbol: str, sl_pips: float) -> float:
        """
        Hitung lot size berdasarkan max risk per trade.
        Untuk scalping: biasanya 0.5% dari balance.
        """
        acc     = mt5.account_info()
        sym     = mt5.symbol_info(symbol)
        if not acc or not sym:
            return sym.volume_min if sym else 0.01

        risk_money     = acc.balance * (MAX_RISK_PERCENT / 100)
        pip_value      = sym.trade_tick_value
        pip_val_per_lot = pip_value * 10

        lot = risk_money / (sl_pips * pip_val_per_lot)
        lot = math.floor(lot / sym.volume_step) * sym.volume_step
        lot = max(sym.volume_min, min(lot, sym.volume_max))
        lot = round(lot, 2)

        logger.info(f"📦 Lot Size | Balance: ${acc.balance:.0f} | "
                    f"Risk: ${risk_money:.2f} ({MAX_RISK_PERCENT}%) | "
                    f"SL: {sl_pips}p | Lot: {lot}")
        return lot

    def get_sl_tp(self, symbol: str, signal: str,
                  price: float) -> tuple:
        """
        Hitung level SL dan TP dalam harga aktual.
        SL: 8 pips | TP: 10 pips (R:R = 1:1.25)
        """
        sym   = mt5.symbol_info(symbol)
        point = sym.point if sym else 0.00001
        pip   = 10 * point
        digits = sym.digits if sym else 5

        sl_price = tp_price = 0.0
        if signal == "BUY":
            sl_price = round(price - SL_PIPS * pip, digits)
            tp_price = round(price + TP_PIPS * pip, digits)
        elif signal == "SELL":
            sl_price = round(price + SL_PIPS * pip, digits)
            tp_price = round(price - TP_PIPS * pip, digits)

        rr = round(TP_PIPS / SL_PIPS, 2)
        logger.info(f"🎯 SL: {sl_price} ({SL_PIPS}p) | TP: {tp_price} ({TP_PIPS}p) | R:R 1:{rr}")
        return sl_price, tp_price

    def count_open_trades(self) -> int:
        positions = mt5.positions_get(magic=MAGIC_NUMBER)
        return len(positions) if positions else 0

    def is_trade_allowed(self, symbol: str) -> tuple:
        """Validasi semua kondisi sebelum buka posisi."""
        # Cek max trades
        open_t = self.count_open_trades()
        if open_t >= MAX_OPEN_TRADES:
            return False, f"Max {MAX_OPEN_TRADES} posisi terbuka"

        # Cek spread
        spread_ok, spread_val = self.check_spread(symbol)
        if not spread_ok:
            return False, f"Spread {spread_val:.1f}p terlalu lebar"

        # Cek margin
        acc = mt5.account_info()
        if acc is None:
            return False, "Gagal mendapatkan info akun"
        if acc.margin_level > 0 and acc.margin_level < 200:
            return False, f"Margin level rendah: {acc.margin_level:.0f}%"

        return True, f"OK | Spread: {spread_val:.1f}p | Posisi: {open_t}/{MAX_OPEN_TRADES}"
