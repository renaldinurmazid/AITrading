import logging
from config import *

logger = logging.getLogger(__name__)

if HAS_MT5:
    import MetaTrader5 as mt5
else:
    # Safe mock for non-Windows platforms (like macOS) to allow compilation/backtesting
    class MockPosition:
        def __init__(self):
            self.ticket = 123456
            self.magic = MAGIC_NUMBER
            self.symbol = SYMBOL
            self.volume = 0.01
            self.type = 0  # 0: BUY, 1: SELL
            self.price_open = 1.08500
            self.price_current = 1.08580
            self.sl = 1.08420
            self.tp = 1.08620
            self.profit = 5.0
            
    class MockOrderResult:
        def __init__(self):
            self.retcode = 10009  # mt5.TRADE_RETCODE_DONE
            self.order = 123456
            self.comment = "Mock Success"

    class MockMT5:
        ORDER_TYPE_BUY = 0
        ORDER_TYPE_SELL = 1
        TRADE_ACTION_DEAL = 1
        TRADE_ACTION_SLTP = 6
        ORDER_TIME_GTC = 0
        ORDER_FILLING_IOC = 1
        TRADE_RETCODE_DONE = 10009
        
        def symbol_info_tick(self, symbol):
            class Tick:
                bid = 1.08580
                ask = 1.08585
            return Tick()
            
        def symbol_info(self, symbol):
            class Sym:
                point = 0.00001
                digits = 5
                spread = 3.0
            return Sym()
            
        def order_send(self, request):
            return MockOrderResult()
            
        def positions_get(self, **kwargs):
            return [MockPosition()]
            
    mt5 = MockMT5()

class ScalpingTrader:
    """Eksekusi order scalping dengan manajemen breakeven & trailing stop."""

    def open_trade(self, symbol: str, signal: str, lot: float,
                   sl: float, tp: float) -> dict:
        """Buka posisi scalping baru."""
        if not HAS_MT5:
            logger.warning(f"⚠️ [MOCK TRADE] Buka posisi {signal} | Simbol: {symbol} | Lot: {lot} | SL: {sl} | TP: {tp}")
            return {
                "ticket": 123456,
                "signal": signal,
                "price":  1.08500,
                "sl": sl, "tp": tp,
                "lot": lot,
            }

        tick = mt5.symbol_info_tick(symbol)
        sym  = mt5.symbol_info(symbol)
        if not tick or not sym:
            return {}

        if signal == "BUY":
            order_type = mt5.ORDER_TYPE_BUY
            price      = tick.ask
        elif signal == "SELL":
            order_type = mt5.ORDER_TYPE_SELL
            price      = tick.bid
        else:
            return {}

        request = {
            "action":       mt5.TRADE_ACTION_DEAL,
            "symbol":       symbol,
            "volume":       lot,
            "type":         order_type,
            "price":        price,
            "sl":           sl,
            "tp":           tp,
            "deviation":    10,           # Scalping butuh eksekusi ketat
            "magic":        MAGIC_NUMBER,
            "comment":      f"SCALP-{signal[:1]}",
            "type_time":    mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)
        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            logger.info(f"✅ SCALP {signal} OPEN | Ticket: {result.order} | "
                        f"Price: {price} | SL: {sl} | TP: {tp} | Lot: {lot}")
            return {
                "ticket": result.order,
                "signal": signal,
                "price":  price,
                "sl": sl, "tp": tp,
                "lot": lot,
            }

        retcode = result.retcode if result else "None"
        comment = result.comment if result else "No response"
        logger.error(f"❌ Order gagal [{retcode}]: {comment}")
        return {}

    def manage_breakeven(self, symbol: str):
        """
        Geser SL ke breakeven (harga entry) setelah profit BREAKEVEN_PIPS.
        Ini melindungi profit awal dari scalping.
        """
        positions = mt5.positions_get(symbol=symbol)
        if not positions:
            return

        sym   = mt5.symbol_info(symbol)
        tick  = mt5.symbol_info_tick(symbol)
        if not sym or not tick:
            return
        point = sym.point
        pip   = 10 * point

        for pos in positions:
            if pos.magic != MAGIC_NUMBER:
                continue

            entry      = pos.price_open
            current_p  = tick.bid if pos.type == 0 else tick.ask
            profit_pips = 0

            if pos.type == 0:   # BUY
                profit_pips = (current_p - entry) / pip
                if profit_pips >= BREAKEVEN_PIPS and pos.sl < entry:
                    new_sl = round(entry + 1 * pip, sym.digits)  # BE +1 pip
                    self._modify_sl_tp(pos.ticket, new_sl, pos.tp)
                    logger.info(f"🔒 BREAKEVEN | Ticket: {pos.ticket} | "
                                f"Profit: {profit_pips:.1f}p | SL → {new_sl}")

            elif pos.type == 1:  # SELL
                profit_pips = (entry - current_p) / pip
                if profit_pips >= BREAKEVEN_PIPS and (pos.sl > entry or pos.sl == 0):
                    new_sl = round(entry - 1 * pip, sym.digits)  # BE -1 pip
                    self._modify_sl_tp(pos.ticket, new_sl, pos.tp)
                    logger.info(f"🔒 BREAKEVEN | Ticket: {pos.ticket} | "
                                f"Profit: {profit_pips:.1f}p | SL → {new_sl}")

    def manage_trailing_stop(self, symbol: str):
        """
        Trailing stop aktif setelah profit TRAILING_START pips.
        Geser SL setiap TRAILING_STEP pips mengikuti harga.
        """
        positions = mt5.positions_get(symbol=symbol)
        if not positions:
            return

        sym   = mt5.symbol_info(symbol)
        tick  = mt5.symbol_info_tick(symbol)
        if not sym or not tick:
            return
        point = sym.point
        pip   = 10 * point

        for pos in positions:
            if pos.magic != MAGIC_NUMBER:
                continue

            entry = pos.price_open

            if pos.type == 0:   # BUY
                current   = tick.bid
                profit_p  = (current - entry) / pip
                if profit_p >= TRAILING_START:
                    new_sl = round(current - TRAILING_STEP * pip, sym.digits)
                    if new_sl > pos.sl:
                        self._modify_sl_tp(pos.ticket, new_sl, pos.tp)
                        logger.debug(f"🔄 TRAIL BUY | Ticket: {pos.ticket} | "
                                     f"SL: {pos.sl} → {new_sl}")

            elif pos.type == 1:  # SELL
                current   = tick.ask
                profit_p  = (entry - current) / pip
                if profit_p >= TRAILING_START:
                    new_sl = round(current + TRAILING_STEP * pip, sym.digits)
                    if new_sl < pos.sl or pos.sl == 0:
                        self._modify_sl_tp(pos.ticket, new_sl, pos.tp)
                        logger.debug(f"🔄 TRAIL SELL | Ticket: {pos.ticket} | "
                                     f"SL: {pos.sl} → {new_sl}")

    def _modify_sl_tp(self, ticket: int, sl: float, tp: float):
        if not HAS_MT5:
            logger.debug(f"[MOCK SLTP] Modify Ticket: {ticket} | SL: {sl} | TP: {tp}")
            return

        request = {
            "action":   mt5.TRADE_ACTION_SLTP,
            "position": ticket,
            "sl":       sl,
            "tp":       tp,
        }
        result = mt5.order_send(request)
        if result and result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.warning(f"Gagal modify SL/TP [{result.retcode}]: {result.comment}")

    def close_all_positions(self, symbol: str, reason: str = "EA-Close"):
        """Tutup semua posisi (dipakai saat sesi tutup atau darurat)."""
        if not HAS_MT5:
            logger.warning(f"⚠️ [MOCK CLOSE ALL] Tutup semua posisi | Simbol: {symbol} | Alasan: {reason}")
            return

        positions = mt5.positions_get(symbol=symbol)
        if not positions:
            return

        for pos in positions:
            if pos.magic != MAGIC_NUMBER:
                continue
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                continue
            close_type  = mt5.ORDER_TYPE_SELL if pos.type == 0 \
                          else mt5.ORDER_TYPE_BUY
            close_price = tick.bid if pos.type == 0 else tick.ask
            request = {
                "action":       mt5.TRADE_ACTION_DEAL,
                "symbol":       symbol,
                "volume":       pos.volume,
                "type":         close_type,
                "position":     pos.ticket,
                "price":        close_price,
                "deviation":    10,
                "magic":        MAGIC_NUMBER,
                "comment":      reason,
                "type_time":    mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            result = mt5.order_send(request)
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                logger.info(f"✅ Posisi {pos.ticket} ditutup | "
                            f"Profit: ${pos.profit:.2f} | Alasan: {reason}")
