"""
Risk Manager Module
Controls position sizing, risk limits, and trade validation.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional

from config.settings import MAX_RISK_PERCENT, MAX_POSITIONS, DEFAULT_LOT_SIZE

logger = logging.getLogger("AITrading.Risk")


class RiskManager:
    """
    Manages trading risk through:
    - Position sizing based on account risk percentage
    - Maximum position limits
    - Daily loss limits
    - Trade validation before execution
    """

    def __init__(self):
        self.max_risk_percent = MAX_RISK_PERCENT
        self.max_positions = MAX_POSITIONS
        self.default_lot = DEFAULT_LOT_SIZE
        self.daily_trades = []
        self.max_daily_trades = 10
        self.max_daily_loss_percent = 5.0
        self.trade_log = []

    def validate_trade(
        self,
        ai_decision: dict,
        account_info: dict,
        open_positions: list,
        pair_config: dict,
    ) -> dict:
        """
        Validate a proposed trade against risk rules.

        Returns:
            {
                "approved": bool,
                "reason": str,
                "adjusted_lot": float,
                "adjusted_sl": float,
                "adjusted_tp": float,
            }
        """
        action = ai_decision.get("action", "HOLD")
        confidence = ai_decision.get("confidence", 0)
        symbol = ai_decision.get("symbol", "")

        # ── Check 1: Action must be BUY or SELL ──────────────
        if action not in ("BUY", "SELL"):
            return {
                "approved": False,
                "reason": f"No trade needed: action is {action}",
            }

        # ── Check 2: Minimum confidence ──────────────────────
        if confidence < 60:
            return {
                "approved": False,
                "reason": f"Confidence too low: {confidence}% (min: 60%)",
            }

        # ── Check 3: Max open positions ──────────────────────
        if len(open_positions) >= self.max_positions:
            return {
                "approved": False,
                "reason": f"Max positions reached: {len(open_positions)}/{self.max_positions}",
            }

        # ── Check 4: No duplicate positions ──────────────────
        existing = [p for p in open_positions if p.get("symbol") == symbol]
        if existing:
            return {
                "approved": False,
                "reason": f"Already have open position for {symbol}",
            }

        # ── Check 5: Daily trade limit ───────────────────────
        today = datetime.now().date()
        today_trades = [
            t for t in self.daily_trades
            if datetime.fromisoformat(t["time"]).date() == today
        ]
        if len(today_trades) >= self.max_daily_trades:
            return {
                "approved": False,
                "reason": f"Daily trade limit reached: {len(today_trades)}/{self.max_daily_trades}",
            }

        # ── Check 6: Daily loss limit ────────────────────────
        balance = account_info.get("balance", 0)
        equity = account_info.get("equity", 0)
        if balance > 0:
            daily_loss_pct = ((balance - equity) / balance) * 100
            if daily_loss_pct >= self.max_daily_loss_percent:
                return {
                    "approved": False,
                    "reason": f"Daily loss limit reached: {daily_loss_pct:.1f}% (max: {self.max_daily_loss_percent}%)",
                }

        # ── Check 7: Sufficient free margin ──────────────────
        free_margin = account_info.get("free_margin", 0)
        if free_margin < balance * 0.1:  # Need at least 10% free margin
            return {
                "approved": False,
                "reason": f"Insufficient free margin: {free_margin}",
            }

        # ── Calculate position size ──────────────────────────
        adjusted_lot = self._calculate_lot_size(
            ai_decision, account_info, pair_config
        )

        # ── Validate SL/TP from AI ───────────────────────────
        sl = ai_decision.get("stop_loss", 0)
        tp = ai_decision.get("take_profit", 0)
        entry = ai_decision.get("entry_price", 0)

        if not sl or not tp or not entry:
            # Use pair config defaults
            pip_value = pair_config.get("pip_value", 0.0001)
            if action == "BUY":
                sl = entry - pair_config.get("sl_pips", 30) * pip_value
                tp = entry + pair_config.get("tp_pips", 50) * pip_value
            else:
                sl = entry + pair_config.get("sl_pips", 30) * pip_value
                tp = entry - pair_config.get("tp_pips", 50) * pip_value

        # ── All checks passed ────────────────────────────────
        result = {
            "approved": True,
            "reason": "All risk checks passed",
            "adjusted_lot": adjusted_lot,
            "adjusted_sl": round(sl, 5),
            "adjusted_tp": round(tp, 5),
        }

        # Log the trade
        self.daily_trades.append({
            "symbol": symbol,
            "action": action,
            "lot": adjusted_lot,
            "time": datetime.now().isoformat(),
        })

        logger.info(
            f"✅ Trade approved: {action} {adjusted_lot} lots {symbol} | "
            f"SL: {sl} | TP: {tp}"
        )

        return result

    def _calculate_lot_size(
        self,
        ai_decision: dict,
        account_info: dict,
        pair_config: dict,
    ) -> float:
        """
        Calculate appropriate lot size based on risk parameters.
        Uses fixed fractional position sizing.
        """
        balance = account_info.get("balance", 10000)
        risk_amount = balance * (self.max_risk_percent / 100)

        # Get SL distance in pips
        entry = ai_decision.get("entry_price", 0)
        sl = ai_decision.get("stop_loss", 0)
        pip_value = pair_config.get("pip_value", 0.0001)

        if entry and sl and pip_value:
            sl_pips = abs(entry - sl) / pip_value
            if sl_pips > 0:
                # Simplified lot calculation
                # risk_amount = lot * sl_pips * pip_value_per_lot
                lot = risk_amount / (sl_pips * 10)  # Approximate
                lot = max(0.01, min(lot, 0.5))  # Clamp
                lot = round(lot, 2)
                return lot

        # Use AI suggested lot or default
        ai_lot = ai_decision.get("lot_size", self.default_lot)
        if ai_lot:
            return max(0.01, min(float(ai_lot), 0.5))

        return self.default_lot

    def should_close_position(
        self,
        position: dict,
        ai_decision: dict,
    ) -> bool:
        """Check if an existing position should be closed."""
        action = ai_decision.get("action", "")
        confidence = ai_decision.get("confidence", 0)

        # AI explicitly says CLOSE
        if action == "CLOSE" and confidence >= 70:
            return True

        # AI says opposite direction with high confidence
        pos_type = position.get("type", "")
        if pos_type == "BUY" and action == "SELL" and confidence >= 75:
            return True
        if pos_type == "SELL" and action == "BUY" and confidence >= 75:
            return True

        # Position has significant profit (> 50 pips worth)
        profit = position.get("profit", 0)
        if profit > 50:  # $50 profit
            return True

        return False

    def get_risk_report(self, account_info: dict, positions: list) -> dict:
        """Generate a risk report."""
        balance = account_info.get("balance", 0)
        equity = account_info.get("equity", 0)
        total_profit = sum(p.get("profit", 0) for p in positions)

        return {
            "balance": balance,
            "equity": equity,
            "margin_used": account_info.get("margin", 0),
            "free_margin": account_info.get("free_margin", 0),
            "open_positions": len(positions),
            "max_positions": self.max_positions,
            "total_unrealized_pnl": total_profit,
            "daily_trades_count": len([
                t for t in self.daily_trades
                if datetime.fromisoformat(t["time"]).date() == datetime.now().date()
            ]),
            "max_daily_trades": self.max_daily_trades,
            "risk_per_trade": f"{self.max_risk_percent}%",
            "drawdown_pct": round(
                ((balance - equity) / balance * 100) if balance > 0 else 0, 2
            ),
        }
