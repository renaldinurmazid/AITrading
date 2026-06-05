import requests
import logging
from datetime import datetime
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)

class TelegramNotifier:

    BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

    def send(self, text: str) -> bool:
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID or \
           TELEGRAM_BOT_TOKEN in ["", "your_bot_token", "your_bot_token_here"] or \
           TELEGRAM_CHAT_ID in ["", "your_chat_id", "your_chat_id_here"]:
            logger.debug("Telegram credentials are not set. Skipping notification.")
            return False
        try:
            resp = requests.post(
                f"{self.BASE_URL}/sendMessage",
                json={"chat_id": TELEGRAM_CHAT_ID,
                      "text": text, "parse_mode": "HTML"},
                timeout=8
            )
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"Telegram error: {e}")
            return False

    def alert_trade_open(self, signal: str, symbol: str, price: float,
                         sl: float, tp: float, lot: float,
                         ticket: int, spread: float, session: str):
        e = "🟢" if signal == "BUY" else "🔴"
        sl_p = abs(round((price - sl) / 0.0001)) if price else 0
        tp_p = abs(round((tp - price) / 0.0001)) if price else 0
        rr   = round(tp_p / sl_p, 1) if sl_p else 0
        now  = datetime.utcnow().strftime("%H:%M:%S UTC")

        msg = (
            f"{e} <b>SCALP {signal} — {symbol}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⏰ Waktu   : <code>{now}</code>\n"
            f"📍 Sesi    : <code>{session}</code>\n"
            f"💵 Entry   : <code>{price}</code>\n"
            f"🛡️ SL      : <code>{sl}</code> ({sl_p}p)\n"
            f"🎯 TP      : <code>{tp}</code> ({tp_p}p)\n"
            f"⚖️ R:R     : <code>1:{rr}</code>\n"
            f"📦 Lot     : <code>{lot}</code>\n"
            f"📊 Spread  : <code>{spread:.1f} pips</code>\n"
            f"🎫 Ticket  : <code>{ticket}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚡ <i>EA Scalping Python</i>"
        )
        self.send(msg)

    def alert_trade_close(self, ticket: int, symbol: str,
                          profit: float, pips: float, reason: str):
        e = "✅" if profit >= 0 else "❌"
        msg = (
            f"{e} <b>SCALP CLOSE — {symbol}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎫 Ticket  : <code>{ticket}</code>\n"
            f"📐 Pips    : <code>{pips:+.1f}</code>\n"
            f"💰 Profit  : <code>${profit:+.2f}</code>\n"
            f"📋 Alasan  : <code>{reason}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━"
        )
        self.send(msg)

    def alert_session_start(self, session: str, symbol: str,
                             spread: float, trend: str):
        msg = (
            f"🚀 <b>SESI TRADING DIMULAI</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🌍 Sesi    : <b>{session}</b>\n"
            f"📌 Simbol  : <b>{symbol}</b>\n"
            f"📊 Spread  : <code>{spread:.1f} pips</code>\n"
            f"📈 Trend   : <code>{trend}</code>\n"
            f"⚡ EA Scalping siap berburu pip!"
        )
        self.send(msg)

    def alert_daily_summary(self, balance: float, profit: float,
                             trades: int, wins: int):
        win_rate = round(wins / trades * 100, 1) if trades else 0
        e = "📈" if profit >= 0 else "📉"
        msg = (
            f"{e} <b>RINGKASAN HARIAN</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💼 Balance   : <code>${balance:.2f}</code>\n"
            f"💰 Profit    : <code>${profit:+.2f}</code>\n"
            f"📋 Trades    : <code>{trades}</code>\n"
            f"🏆 Win Rate  : <code>{win_rate}%</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━"
        )
        self.send(msg)
