import requests
import logging
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, format_currency


logger = logging.getLogger(__name__)

class TelegramNotifier:
    """Kirim notifikasi trading ke Telegram."""

    BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

    def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID or TELEGRAM_BOT_TOKEN == "your_bot_token_here" or TELEGRAM_CHAT_ID == "your_chat_id_here":
            logger.debug("Telegram credentials are not set or are default. Skipping notification.")
            return False
        try:
            resp = requests.post(
                f"{self.BASE_URL}/sendMessage",
                json={"chat_id": TELEGRAM_CHAT_ID,
                      "text": text,
                      "parse_mode": parse_mode},
                timeout=10
            )
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"Telegram error: {e}")
            return False

    def notify_trade_open(self, signal: str, symbol: str,
                          price: float, sl: float, tp: float,
                          lot: float, ticket: int):
        emoji = "🟢" if signal == "BUY" else "🔴"
        msg = (
            f"{emoji} <b>TRADE OPEN — {signal}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📌 Simbol  : <b>{symbol}</b>\n"
            f"💵 Harga   : <code>{price}</code>\n"
            f"🛡️ SL      : <code>{sl}</code>\n"
            f"🎯 TP      : <code>{tp}</code>\n"
            f"📦 Lot     : <code>{lot}</code>\n"
            f"🎫 Ticket  : <code>{ticket}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⚡ EA Python Auto-Trader"
        )
        self.send_message(msg)

    def notify_trade_close(self, symbol: str, ticket: int,
                           profit: float, pips: float):
        emoji = "✅" if profit >= 0 else "❌"
        msg = (
            f"{emoji} <b>TRADE CLOSED</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📌 Simbol  : <b>{symbol}</b>\n"
            f"🎫 Ticket  : <code>{ticket}</code>\n"
            f"💰 Profit  : <code>{format_currency(profit)}</code>\n"
            f"📐 Pips    : <code>{pips:.1f}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )

        self.send_message(msg)

    def notify_daily_report(self, balance: float, equity: float,
                            daily_profit: float, total_trades: int,
                            win_rate: float):
        emoji = "📈" if daily_profit >= 0 else "📉"
        msg = (
            f"{emoji} <b>LAPORAN HARIAN</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"💼 Balance   : <code>{format_currency(balance)}</code>\n"
            f"📊 Equity    : <code>{format_currency(equity)}</code>\n"
            f"💰 Profit    : <code>{format_currency(daily_profit)}</code>\n"
            f"📋 Trades    : <code>{total_trades}</code>\n"
            f"🎯 Win Rate  : <code>{win_rate:.1f}%</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )

        self.send_message(msg)
