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
                self.trade_tick_value = 1.0
                self.volume_min = 0.01
                self.volume_max = 500.0
                self.volume_step = 0.01
        
        def account_info(self):
            return self.AccountInfo()
        def symbol_info(self, symbol):
            return self.SymbolInfo()
        def positions_get(self, **kwargs):
            return []
    mt5 = MockMT5()

class RiskManager:
    """Kalkulasi lot size dan level SL/TP berbasis ATR & risk percent."""

    def calculate_lot_size(self, symbol: str, sl_pips: float,
                           risk_percent: float = MAX_RISK_PERCENT) -> float:
        """
        Hitung lot size berdasarkan risk percent dari balance.
        Formula: Lot = (Balance * Risk%) / (SL in pips * pip value)
        """
        account = mt5.account_info()
        sym_info = mt5.symbol_info(symbol)

        if account is None or sym_info is None:
            logger.error("Gagal ambil info akun/simbol untuk kalkulasi lot")
            return sym_info.volume_min if sym_info else 0.01

        balance    = account.balance
        risk_money = balance * (risk_percent / 100)
        point      = sym_info.point
        pip_value  = sym_info.trade_tick_value

        # Pip value per lot = (10 * point / point) * tick_value
        pip_val_per_lot = (10 * point / point) * pip_value
        sl_money        = sl_pips * pip_val_per_lot

        if sl_money <= 0:
            return sym_info.volume_min

        raw_lot = risk_money / sl_money

        # Normalisasi ke volume step broker
        step    = sym_info.volume_step
        lot     = math.floor(raw_lot / step) * step
        lot     = max(sym_info.volume_min, min(lot, sym_info.volume_max))
        lot     = round(lot, 2)

        logger.info(f"💰 Kalkulasi Lot | Balance: ${balance:.2f} | "
                    f"Risk: ${risk_money:.2f} | SL: {sl_pips} pips | Lot: {lot}")
        return lot

    def calculate_sl_tp_atr(self, df, signal: str, atr_multiplier_sl: float = 1.5,
                             atr_multiplier_tp: float = 3.0) -> tuple:
        """
        Hitung SL dan TP dinamis berdasarkan ATR.
        SL = ATR * 1.5 | TP = ATR * 3.0 (Risk:Reward = 1:2)
        """
        if df.empty or "atr" not in df.columns or df["atr"].isna().all():
            return STOP_LOSS_PIPS, TAKE_PROFIT_PIPS

        atr    = df.iloc[-1]["atr"]
        sl_pts = round(atr * atr_multiplier_sl, 5)
        tp_pts = round(atr * atr_multiplier_tp, 5)

        sym    = mt5.symbol_info(SYMBOL)
        point  = sym.point if sym else 0.00001
        sl_pips = round(sl_pts / (10 * point))
        tp_pips = round(tp_pts / (10 * point))

        logger.debug(f"ATR-based | SL: {sl_pips} pips | TP: {tp_pips} pips | R:R 1:2")
        return sl_pips, tp_pips

    def count_open_trades(self, symbol: str = None) -> int:
        """Hitung jumlah posisi terbuka."""
        if HAS_MT5:
            import MetaTrader5 as native_mt5
            positions = native_mt5.positions_get(symbol=symbol) if symbol \
                        else native_mt5.positions_get(magic=MAGIC_NUMBER)
            return len(positions) if positions else 0
        else:
            positions = mt5.positions_get(symbol=symbol)
            return len(positions) if positions else 0

    def is_trade_allowed(self, symbol: str) -> tuple:
        """Validasi apakah trade boleh dibuka."""
        open_trades = self.count_open_trades(symbol)

        if open_trades >= MAX_OPEN_TRADES:
            return False, f"Max trade ({MAX_OPEN_TRADES}) sudah tercapai"

        acc = mt5.account_info()
        if acc is None:
            return False, "Gagal mendapatkan info akun"

        if acc.margin_level > 0 and acc.margin_level < 150:
            return False, f"Margin level terlalu rendah: {acc.margin_level:.1f}%"

        return True, "OK"
