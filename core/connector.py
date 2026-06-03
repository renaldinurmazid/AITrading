import logging
from config import MT5_CONFIG, SYMBOL, HAS_MT5

logger = logging.getLogger(__name__)

if HAS_MT5:
    import MetaTrader5 as mt5
else:
    # Safe mock for non-Windows environments (like macOS) to allow compilation/backtesting
    class MockMT5:
        def initialize(self):
            logger.warning("MT5 initialize: Mocked. MetaTrader5 is Windows-only.")
            return False
        def login(self, login, password, server):
            return False
        def shutdown(self):
            pass
        def last_error(self):
            return (0, "Mock MT5 on non-Windows environment")
        def account_info(self):
            return None
        def symbol_info(self, symbol):
            return None
        def symbol_select(self, symbol, visible):
            return False
    mt5 = MockMT5()

class MT5Connector:
    """Mengelola koneksi ke MetaTrader 5."""

    def __init__(self):
        self.connected = False

    def connect(self) -> bool:
        """Inisiasi koneksi ke MT5."""
        if not HAS_MT5:
            logger.error("Gagal terhubung ke MT5: Library MetaTrader5 hanya didukung di Windows.")
            return False

        if not mt5.initialize():
            logger.error(f"MT5 initialize gagal: {mt5.last_error()}")
            return False

        authorized = mt5.login(
            login=MT5_CONFIG["login"],
            password=MT5_CONFIG["password"],
            server=MT5_CONFIG["server"],
        )
        if not authorized:
            logger.error(f"Login MT5 gagal: {mt5.last_error()}")
            mt5.shutdown()
            return False

        account = mt5.account_info()
        if account:
            logger.info(f"✅ Terhubung ke MT5 | Akun: {account.login} | "
                        f"Server: {account.server} | Balance: ${account.balance:.2f}")
        else:
            logger.info("✅ Terhubung ke MT5 (Info akun tidak tersedia)")
        self.connected = True
        return True

    def disconnect(self):
        """Putus koneksi dari MT5."""
        if HAS_MT5:
            mt5.shutdown()
        self.connected = False
        logger.info("🔌 Koneksi MT5 diputus.")

    def get_account_info(self) -> dict:
        """Ambil informasi akun trading."""
        if not HAS_MT5:
            return {}
        info = mt5.account_info()
        if info is None:
            return {}
        return {
            "balance":   info.balance,
            "equity":    info.equity,
            "margin":    info.margin,
            "free_margin": info.margin_free,
            "profit":    info.profit,
            "leverage":  info.leverage,
        }

    def get_symbol_info(self, symbol: str = SYMBOL) -> dict:
        """Ambil informasi simbol."""
        if not HAS_MT5:
            return {}
        sym = mt5.symbol_info(symbol)
        if sym is None:
            logger.error(f"Simbol {symbol} tidak ditemukan!")
            return {}
        if not sym.visible:
            mt5.symbol_select(symbol, True)
        return {
            "bid":        sym.bid,
            "ask":        sym.ask,
            "spread":     sym.spread,
            "point":      sym.point,
            "digits":     sym.digits,
            "volume_min": sym.volume_min,
            "volume_step": sym.volume_step,
        }
