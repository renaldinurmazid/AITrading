"""
MT5 Connector - MetaTrader 5 Integration Module
Handles connection, market data retrieval, and trade execution.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd

logger = logging.getLogger("AITrading.MT5")

# Try to import MetaTrader5 - it only works on Windows
try:
    import MetaTrader5 as mt5

    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    logger.warning(
        "MetaTrader5 package not available. "
        "Running in simulation mode. "
        "Install on Windows: pip install MetaTrader5"
    )


class MT5Connector:
    """
    Manages the connection to MetaTrader 5 terminal.
    Provides methods for market data, order placement, and position management.
    """

    def __init__(self, login: int, password: str, server: str, path: str = ""):
        self.login = login
        self.password = password
        self.server = server
        self.path = path
        self.connected = False
        self._simulation_mode = not MT5_AVAILABLE

        if self._simulation_mode:
            logger.info("🔄 MT5 Connector running in SIMULATION mode")

    # ── Connection ───────────────────────────────────────────

    def connect(self) -> bool:
        """Initialize and login to MT5 terminal."""
        if self._simulation_mode:
            logger.info("✅ [SIM] Connected to MT5 (simulation)")
            self.connected = True
            return True

        try:
            init_params = {}
            if self.path:
                init_params["path"] = self.path
            init_params["login"] = self.login
            init_params["password"] = self.password
            init_params["server"] = self.server

            if not mt5.initialize(**init_params):
                error = mt5.last_error()
                logger.error(f"❌ MT5 init failed: {error}")
                return False

            account_info = mt5.account_info()
            if account_info is None:
                logger.error("❌ Failed to get account info")
                return False

            self.connected = True
            logger.info(
                f"✅ Connected to MT5 | Account: {account_info.login} | "
                f"Balance: {account_info.balance} {account_info.currency} | "
                f"Server: {account_info.server}"
            )
            return True

        except Exception as e:
            logger.error(f"❌ MT5 connection error: {e}")
            return False

    def disconnect(self):
        """Shutdown MT5 connection."""
        if not self._simulation_mode and MT5_AVAILABLE:
            mt5.shutdown()
        self.connected = False
        logger.info("🔌 MT5 disconnected")

    # ── Market Data ──────────────────────────────────────────

    def get_rates(
        self, symbol: str, timeframe: str = "H1", count: int = 500
    ) -> Optional[pd.DataFrame]:
        """
        Get OHLCV candlestick data from MT5.
        Returns DataFrame with: time, open, high, low, close, volume
        """
        if self._simulation_mode:
            return self._generate_simulated_rates(symbol, timeframe, count)

        tf_map = {
            "M1": mt5.TIMEFRAME_M1,
            "M5": mt5.TIMEFRAME_M5,
            "M15": mt5.TIMEFRAME_M15,
            "M30": mt5.TIMEFRAME_M30,
            "H1": mt5.TIMEFRAME_H1,
            "H4": mt5.TIMEFRAME_H4,
            "D1": mt5.TIMEFRAME_D1,
            "W1": mt5.TIMEFRAME_W1,
        }

        mt5_tf = tf_map.get(timeframe, mt5.TIMEFRAME_H1)
        rates = mt5.copy_rates_from_pos(symbol, mt5_tf, 0, count)

        if rates is None or len(rates) == 0:
            logger.error(f"❌ No rates data for {symbol} {timeframe}")
            return None

        df = pd.DataFrame(rates)
        df["time"] = pd.to_datetime(df["time"], unit="s")
        df.set_index("time", inplace=True)
        df.rename(
            columns={
                "tick_volume": "volume",
            },
            inplace=True,
        )
        return df[["open", "high", "low", "close", "volume"]]

    def get_tick(self, symbol: str) -> Optional[dict]:
        """Get current tick (bid/ask) for a symbol."""
        if self._simulation_mode:
            return self._generate_simulated_tick(symbol)

        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return None

        return {
            "symbol": symbol,
            "bid": tick.bid,
            "ask": tick.ask,
            "spread": round(tick.ask - tick.bid, 5),
            "time": datetime.fromtimestamp(tick.time),
        }

    def get_symbol_info(self, symbol: str) -> Optional[dict]:
        """Get symbol specification."""
        if self._simulation_mode:
            return self._get_simulated_symbol_info(symbol)

        info = mt5.symbol_info(symbol)
        if info is None:
            return None

        return {
            "symbol": info.name,
            "digits": info.digits,
            "point": info.point,
            "spread": info.spread,
            "trade_mode": info.trade_mode,
            "volume_min": info.volume_min,
            "volume_max": info.volume_max,
            "volume_step": info.volume_step,
        }

    # ── Order Execution ──────────────────────────────────────

    def open_position(
        self,
        symbol: str,
        order_type: str,
        lot: float,
        sl: float = 0.0,
        tp: float = 0.0,
        comment: str = "AI_Trade",
        magic: int = 123456,
    ) -> Optional[dict]:
        """
        Open a market order (BUY or SELL).

        Args:
            symbol:     Trading symbol (e.g. EURUSD)
            order_type: 'BUY' or 'SELL'
            lot:        Position size
            sl:         Stop Loss price
            tp:         Take Profit price
            comment:    Order comment
            magic:      Magic number for identification

        Returns:
            Order result dict or None on error
        """
        if self._simulation_mode:
            return self._simulate_open_position(
                symbol, order_type, lot, sl, tp, comment
            )

        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            logger.error(f"❌ Cannot get tick for {symbol}")
            return None

        if order_type.upper() == "BUY":
            trade_type = mt5.ORDER_TYPE_BUY
            price = tick.ask
        elif order_type.upper() == "SELL":
            trade_type = mt5.ORDER_TYPE_SELL
            price = tick.bid
        else:
            logger.error(f"❌ Invalid order type: {order_type}")
            return None

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot,
            "type": trade_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 20,
            "magic": magic,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)

        if result is None:
            logger.error(f"❌ Order send returned None for {symbol}")
            return None

        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(
                f"❌ Order failed: {result.retcode} - {result.comment}"
            )
            return None

        logger.info(
            f"✅ {order_type} {lot} lots {symbol} @ {price} | "
            f"SL: {sl} | TP: {tp} | Ticket: {result.order}"
        )

        return {
            "ticket": result.order,
            "symbol": symbol,
            "type": order_type.upper(),
            "volume": lot,
            "price": price,
            "sl": sl,
            "tp": tp,
            "comment": comment,
            "time": datetime.now().isoformat(),
        }

    def close_position(self, ticket: int) -> bool:
        """Close a specific position by ticket."""
        if self._simulation_mode:
            logger.info(f"✅ [SIM] Closed position #{ticket}")
            return True

        position = mt5.positions_get(ticket=ticket)
        if not position:
            logger.error(f"❌ Position #{ticket} not found")
            return False

        pos = position[0]
        close_type = (
            mt5.ORDER_TYPE_SELL
            if pos.type == mt5.ORDER_TYPE_BUY
            else mt5.ORDER_TYPE_BUY
        )
        tick = mt5.symbol_info_tick(pos.symbol)
        price = tick.bid if close_type == mt5.ORDER_TYPE_SELL else tick.ask

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": pos.symbol,
            "volume": pos.volume,
            "type": close_type,
            "position": ticket,
            "price": price,
            "deviation": 20,
            "magic": pos.magic,
            "comment": "AI_Close",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        result = mt5.order_send(request)
        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            logger.info(f"✅ Closed position #{ticket}")
            return True

        logger.error(f"❌ Failed to close #{ticket}: {result}")
        return False

    def get_positions(self, symbol: str = None) -> list:
        """Get open positions, optionally filtered by symbol."""
        if self._simulation_mode:
            return []

        if symbol:
            positions = mt5.positions_get(symbol=symbol)
        else:
            positions = mt5.positions_get()

        if positions is None:
            return []

        return [
            {
                "ticket": p.ticket,
                "symbol": p.symbol,
                "type": "BUY" if p.type == 0 else "SELL",
                "volume": p.volume,
                "open_price": p.price_open,
                "current_price": p.price_current,
                "sl": p.sl,
                "tp": p.tp,
                "profit": p.profit,
                "swap": p.swap,
                "time": datetime.fromtimestamp(p.time).isoformat(),
                "comment": p.comment,
            }
            for p in positions
        ]

    def get_account_info(self) -> dict:
        """Get account information."""
        if self._simulation_mode:
            return {
                "login": 0,
                "balance": 10000.0,
                "equity": 10000.0,
                "margin": 0.0,
                "free_margin": 10000.0,
                "margin_level": 0.0,
                "profit": 0.0,
                "currency": "USD",
                "server": "SIMULATION",
                "mode": "DEMO",
            }

        info = mt5.account_info()
        if info is None:
            return {}

        return {
            "login": info.login,
            "balance": info.balance,
            "equity": info.equity,
            "margin": info.margin,
            "free_margin": info.margin_free,
            "margin_level": info.margin_level if info.margin_level else 0.0,
            "profit": info.profit,
            "currency": info.currency,
            "server": info.server,
            "mode": "DEMO"
            if info.trade_mode == 0
            else "REAL",
        }

    # ── Simulation Helpers ───────────────────────────────────

    def _generate_simulated_rates(
        self, symbol: str, timeframe: str, count: int
    ) -> pd.DataFrame:
        """Generate realistic simulated OHLCV data."""
        import numpy as np

        base_prices = {
            "EURUSD": 1.0850,
            "GBPJPY": 193.50,
            "XAUUSD": 2650.00,
        }
        volatility = {
            "EURUSD": 0.0005,
            "GBPJPY": 0.05,
            "XAUUSD": 2.0,
        }

        base = base_prices.get(symbol, 1.0)
        vol = volatility.get(symbol, 0.001)

        tf_minutes = {
            "M1": 1, "M5": 5, "M15": 15, "M30": 30,
            "H1": 60, "H4": 240, "D1": 1440, "W1": 10080,
        }
        minutes = tf_minutes.get(timeframe, 60)

        np.random.seed(hash(symbol + timeframe) % (2**31))

        dates = pd.date_range(
            end=datetime.now(),
            periods=count,
            freq=f"{minutes}min",
        )

        # Generate random walk with mean reversion
        returns = np.random.normal(0, vol, count)
        prices = [base]
        for r in returns[1:]:
            mean_reversion = (base - prices[-1]) * 0.005
            new_price = prices[-1] * (1 + r) + mean_reversion
            prices.append(new_price)

        prices = np.array(prices)

        # Generate OHLC from close prices
        high_add = np.abs(np.random.normal(0, vol * 0.5, count))
        low_sub = np.abs(np.random.normal(0, vol * 0.5, count))

        df = pd.DataFrame(
            {
                "open": prices * (1 + np.random.normal(0, vol * 0.1, count)),
                "high": prices + high_add * base,
                "low": prices - low_sub * base,
                "close": prices,
                "volume": np.random.randint(100, 5000, count),
            },
            index=dates,
        )
        df.index.name = "time"
        return df

    def _generate_simulated_tick(self, symbol: str) -> dict:
        """Generate a simulated current tick."""
        import numpy as np

        base_prices = {
            "EURUSD": 1.0850,
            "GBPJPY": 193.50,
            "XAUUSD": 2650.00,
        }
        spreads = {
            "EURUSD": 0.00015,
            "GBPJPY": 0.03,
            "XAUUSD": 0.50,
        }

        base = base_prices.get(symbol, 1.0)
        spread = spreads.get(symbol, 0.001)

        # Add some randomness
        noise = np.random.normal(0, base * 0.001)
        bid = base + noise
        ask = bid + spread

        return {
            "symbol": symbol,
            "bid": round(bid, 5),
            "ask": round(ask, 5),
            "spread": round(spread, 5),
            "time": datetime.now(),
        }

    def _get_simulated_symbol_info(self, symbol: str) -> dict:
        """Return simulated symbol metadata."""
        info_map = {
            "EURUSD": {"digits": 5, "point": 0.00001, "spread": 15},
            "GBPJPY": {"digits": 3, "point": 0.001, "spread": 30},
            "XAUUSD": {"digits": 2, "point": 0.01, "spread": 50},
        }
        info = info_map.get(symbol, {"digits": 5, "point": 0.00001, "spread": 20})
        return {
            "symbol": symbol,
            "digits": info["digits"],
            "point": info["point"],
            "spread": info["spread"],
            "trade_mode": 0,
            "volume_min": 0.01,
            "volume_max": 100.0,
            "volume_step": 0.01,
        }

    def _simulate_open_position(
        self, symbol, order_type, lot, sl, tp, comment
    ):
        """Simulate opening a position."""
        import random

        tick = self._generate_simulated_tick(symbol)
        price = tick["ask"] if order_type.upper() == "BUY" else tick["bid"]
        ticket = random.randint(100000, 999999)

        logger.info(
            f"✅ [SIM] {order_type} {lot} lots {symbol} @ {price:.5f} | "
            f"SL: {sl} | TP: {tp} | Ticket: {ticket}"
        )

        return {
            "ticket": ticket,
            "symbol": symbol,
            "type": order_type.upper(),
            "volume": lot,
            "price": price,
            "sl": sl,
            "tp": tp,
            "comment": comment,
            "time": datetime.now().isoformat(),
            "simulated": True,
        }
