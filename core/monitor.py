import logging
from config import MAGIC_NUMBER, HAS_MT5

logger = logging.getLogger(__name__)

if HAS_MT5:
    import MetaTrader5 as mt5
else:
    mt5 = None

class PositionMonitor:
    """Memantau posisi trading yang terbuka dan statistik akun."""

    def __init__(self):
        pass

    def get_open_positions(self, symbol: str = None) -> list:
        """Mendapatkan daftar semua posisi terbuka."""
        if not HAS_MT5 or mt5 is None:
            return []
        
        try:
            if symbol:
                positions = mt5.positions_get(symbol=symbol)
            else:
                positions = mt5.positions_get()
                
            if positions is None:
                return []
                
            # Filter berdasarkan magic number agar EA hanya memantau posisinya sendiri
            return [p for p in positions if p.magic == MAGIC_NUMBER]
        except Exception as e:
            logger.error(f"Gagal mendapatkan posisi terbuka: {e}")
            return []

    def log_open_positions_summary(self):
        """Mencetak ringkasan posisi terbuka ke log."""
        positions = self.get_open_positions()
        if not positions:
            logger.info("ℹ️ Tidak ada posisi terbuka yang dipantau oleh EA.")
            return

        logger.info(f"📊 Ringkasan Posisi Terbuka (Total: {len(positions)}):")
        for pos in positions:
            pos_type = "BUY" if pos.type == 0 else "SELL"
            pnl_status = "Profit" if pos.profit >= 0 else "Loss"
            logger.info(
                f"  Ticket: {pos.ticket} | Simbol: {pos.symbol} | Type: {pos_type} | "
                f"Volume: {pos.volume} | Entry: {pos.price_open} | Cur: {pos.price_current} | "
                f"SL: {pos.sl} | TP: {pos.tp} | P&L: ${pos.profit:.2f} ({pnl_status})"
            )

    def get_total_floating_profit(self) -> float:
        """Menghitung total floating profit/loss dari posisi terbuka."""
        positions = self.get_open_positions()
        return sum(pos.profit for pos in positions)
