import logging
from config import *

logger = logging.getLogger(__name__)

if HAS_MT5:
    import MetaTrader5 as mt5
else:
    # Safe mock definitions for constants
    class MockMT5:
        ORDER_TYPE_BUY = 0
        ORDER_TYPE_SELL = 1
        TRADE_ACTION_DEAL = 1
        TRADE_ACTION_SLTP = 6
        ORDER_TIME_GTC = 0
        ORDER_FILLING_IOC = 1
        TRADE_RETCODE_DONE = 10009
        
        def symbol_info_tick(self, symbol): return None
        def symbol_info(self, symbol): return None
        def order_send(self, request): return None
        def positions_get(self, **kwargs): return []
    mt5 = MockMT5()

class Trader:
    """Mengirim dan mengelola order ke MetaTrader 5."""

    def open_trade(self, symbol: str, signal: str,
                   lot: float, sl_pips: float, tp_pips: float,
                   comment: str = "EA-Python") -> dict:
        """
        Buka posisi baru.
        signal: 'BUY' atau 'SELL'
        """
        if not HAS_MT5:
            logger.warning(f"⚠️ [MOCK TRADE] Buka posisi {signal} | Simbol: {symbol} | Lot: {lot} | SL: {sl_pips} pips | TP: {tp_pips} pips")
            # Return a simulated result for testing
            import random
            mock_ticket = random.randint(100000, 999999)
            return {
                "ticket": mock_ticket,
                "signal": signal,
                "price":  1.1000,
                "sl": 1.0950 if signal == "BUY" else 1.1050,
                "tp": 1.1100 if signal == "BUY" else 1.0900,
                "lot": lot,
            }

        sym_info = mt5.symbol_info_tick(symbol)
        if sym_info is None:
            logger.error(f"Tidak bisa ambil tick untuk {symbol}")
            return {}

        point_info = mt5.symbol_info(symbol)
        if point_info is None:
            logger.error(f"Tidak bisa ambil data point untuk {symbol}")
            return {}
        
        point = point_info.point
        pip   = 10 * point

        if signal == "BUY":
            order_type = mt5.ORDER_TYPE_BUY
            price      = sym_info.ask
            sl         = round(price - sl_pips * pip, 5)
            tp         = round(price + tp_pips * pip, 5)
        elif signal == "SELL":
            order_type = mt5.ORDER_TYPE_SELL
            price      = sym_info.bid
            sl         = round(price + sl_pips * pip, 5)
            tp         = round(price - tp_pips * pip, 5)
        else:
            return {}

        request = {
            "action":      mt5.TRADE_ACTION_DEAL,
            "symbol":      symbol,
            "volume":      lot,
            "type":        order_type,
            "price":       price,
            "sl":          sl,
            "tp":          tp,
            "deviation":   20,
            "magic":       MAGIC_NUMBER,
            "comment":     comment,
            "type_time":   mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)

        if result is None:
            logger.error("Gagal mengirim order: order_send menghasilkan None")
            return {}

        if result.retcode == mt5.TRADE_RETCODE_DONE:
            logger.info(f"✅ ORDER {signal} | Ticket: {result.order} | "
                        f"Price: {price} | SL: {sl} | TP: {tp} | Lot: {lot}")
            return {
                "ticket": result.order,
                "signal": signal,
                "price":  price,
                "sl": sl, "tp": tp,
                "lot": lot,
            }
        else:
            logger.error(f"❌ Order gagal | Retcode: {result.retcode} | "
                         f"Comment: {result.comment}")
            return {}

    def close_position(self, ticket: int) -> bool:
        """Tutup posisi berdasarkan ticket number."""
        if not HAS_MT5:
            logger.warning(f"⚠️ [MOCK CLOSE] Tutup posisi Ticket: {ticket}")
            return True

        position = mt5.positions_get(ticket=ticket)
        if not position:
            logger.warning(f"Posisi ticket {ticket} tidak ditemukan")
            return False

        pos = position[0]
        sym_info = mt5.symbol_info_tick(pos.symbol)
        close_type = mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY
        close_price = sym_info.bid if pos.type == 0 else sym_info.ask

        request = {
            "action":      mt5.TRADE_ACTION_DEAL,
            "symbol":      pos.symbol,
            "volume":      pos.volume,
            "type":        close_type,
            "position":    ticket,
            "price":       close_price,
            "deviation":   20,
            "magic":       MAGIC_NUMBER,
            "comment":     "EA-Close",
            "type_time":   mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            logger.info(f"✅ Posisi {ticket} ditutup | Profit: {pos.profit:.2f}")
            return True

        logger.error(f"❌ Gagal tutup posisi {ticket}: {result.comment}")
        return False

    def update_trailing_stop(self, symbol: str = SYMBOL):
        """Update trailing stop untuk semua posisi terbuka."""
        if not HAS_MT5:
            return

        positions = mt5.positions_get(symbol=symbol)
        if not positions:
            return

        sym_info = mt5.symbol_info(symbol)
        point    = sym_info.point
        pip      = 10 * point
        tick     = mt5.symbol_info_tick(symbol)

        for pos in positions:
            if pos.magic != MAGIC_NUMBER:
                continue

            if pos.type == 0:   # BUY
                new_sl = round(tick.bid - TRAILING_PIPS * pip, 5)
                if new_sl > pos.sl:
                    self._modify_sl(pos.ticket, new_sl)

            elif pos.type == 1:  # SELL
                new_sl = round(tick.ask + TRAILING_PIPS * pip, 5)
                if new_sl < pos.sl or pos.sl == 0:
                    self._modify_sl(pos.ticket, new_sl)

    def _modify_sl(self, ticket: int, new_sl: float):
        """Modifikasi SL sebuah posisi."""
        if not HAS_MT5:
            return

        request = {
            "action":   mt5.TRADE_ACTION_SLTP,
            "position": ticket,
            "sl":       new_sl,
        }
        result = mt5.order_send(request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            logger.debug(f"✅ Trailing stop diupdate | Ticket: {ticket} | SL: {new_sl}")
