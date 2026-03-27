"""
Trading Engine - Main orchestrator
Coordinates AI analysis, technical analysis, risk management, and trade execution.
"""
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from config.settings import (
    TRADING_PAIRS,
    MT5_LOGIN,
    MT5_PASSWORD,
    MT5_SERVER,
    MT5_PATH,
    AI_ANALYSIS_INTERVAL,
    LOG_DIR,
    TRADING_MODE,
)
from core.mt5_connector import MT5Connector
from core.technical_analysis import TechnicalAnalyzer
from core.ai_analyzer import AIAnalyzer
from core.risk_manager import RiskManager

logger = logging.getLogger("AITrading.Engine")


class TradingEngine:
    """
    Main trading engine that orchestrates the full analysis-to-execution pipeline:
    1. Fetch market data from MT5
    2. Run technical analysis
    3. Send to Gemini AI for interpretation
    4. Validate through risk management
    5. Execute approved trades on MT5
    """

    def __init__(self):
        self.mt5 = MT5Connector(
            login=MT5_LOGIN,
            password=MT5_PASSWORD,
            server=MT5_SERVER,
            path=MT5_PATH,
        )
        self.ta = TechnicalAnalyzer()
        self.ai = AIAnalyzer()
        self.risk = RiskManager()

        self.pairs = TRADING_PAIRS
        self.analysis_interval = AI_ANALYSIS_INTERVAL
        self.running = False
        self.last_analyses = {}
        self.trade_history = []

        # Trade log file
        self.trade_log_path = LOG_DIR / "trades.json"
        self._load_trade_history()

        logger.info("🚀 Trading Engine initialized")
        logger.info(f"📊 Trading pairs: {[p['display_name'] for p in self.pairs]}")
        logger.info(f"⏱️  Analysis interval: {self.analysis_interval}s")
        logger.info(f"🔒 Trading mode: {TRADING_MODE}")

    def start(self):
        """Start the trading engine main loop."""
        logger.info("=" * 60)
        logger.info("🚀 STARTING AI TRADING ENGINE")
        logger.info("=" * 60)

        # Connect to MT5
        if not self.mt5.connect():
            logger.error("❌ Failed to connect to MT5. Exiting.")
            return

        self.running = True
        account = self.mt5.get_account_info()
        logger.info(
            f"💰 Account: {account.get('login')} | "
            f"Balance: {account.get('balance')} {account.get('currency')}"
        )

        try:
            while self.running:
                self._run_analysis_cycle()
                logger.info(
                    f"⏳ Next analysis in {self.analysis_interval} seconds..."
                )
                time.sleep(self.analysis_interval)
        except KeyboardInterrupt:
            logger.info("⛔ Shutdown requested by user")
        finally:
            self.stop()

    def stop(self):
        """Stop the trading engine."""
        self.running = False
        self.mt5.disconnect()
        self._save_trade_history()
        logger.info("🛑 Trading Engine stopped")

    def _run_analysis_cycle(self):
        """Run one full analysis cycle for all trading pairs."""
        logger.info("")
        logger.info("═" * 60)
        logger.info(f"🔄 Analysis cycle started at {datetime.now().isoformat()}")
        logger.info("═" * 60)

        account_info = self.mt5.get_account_info()
        open_positions = self.mt5.get_positions()
        analyses = []

        for pair_config in self.pairs:
            symbol = pair_config["symbol"]
            display = pair_config["display_name"]

            try:
                result = self._analyze_pair(
                    symbol, display, pair_config,
                    account_info, open_positions,
                )
                if result:
                    analyses.append(result)
            except Exception as e:
                logger.error(f"❌ Error analyzing {display}: {e}")

        # Generate market summary
        if analyses:
            try:
                summary = self.ai.get_market_summary(analyses)
                logger.info(f"\n📋 MARKET SUMMARY:\n{summary}")
            except Exception as e:
                logger.error(f"Failed to generate summary: {e}")

        logger.info("═" * 60)
        logger.info(f"✅ Analysis cycle completed")
        logger.info("═" * 60)

    def _analyze_pair(
        self,
        symbol: str,
        display_name: str,
        pair_config: dict,
        account_info: dict,
        open_positions: list,
    ) -> Optional[dict]:
        """Analyze a single trading pair and execute if approved."""
        logger.info(f"\n{'─' * 40}")
        logger.info(f"📊 Analyzing {display_name} ({symbol})")
        logger.info(f"{'─' * 40}")

        # Step 1: Get market data
        df = self.mt5.get_rates(symbol, timeframe="H1", count=500)
        if df is None:
            logger.warning(f"⚠️ No data for {symbol}")
            return None

        tick = self.mt5.get_tick(symbol)

        # Step 2: Technical Analysis
        ta_result = self.ta.analyze(df)
        sr_levels = self.ta.get_support_resistance(df)

        logger.info(
            f"📈 TA Result: Trend={ta_result['trend']} | "
            f"Strength={ta_result['strength']}% | "
            f"Recommendation={ta_result['recommendation']}"
        )

        # Step 3: AI Analysis
        ai_decision = self.ai.analyze_market(
            symbol=symbol,
            ta_result=ta_result,
            support_resistance=sr_levels,
            tick_data=tick,
            account_info=account_info,
            open_positions=open_positions,
        )

        self.last_analyses[symbol] = {
            "ta": ta_result,
            "ai": ai_decision,
            "support_resistance": sr_levels,
            "tick": tick,
            "timestamp": datetime.now().isoformat(),
        }

        logger.info(
            f"🧠 AI Decision: {ai_decision.get('action')} | "
            f"Confidence: {ai_decision.get('confidence')}% | "
            f"Risk: {ai_decision.get('risk_level', 'N/A')}"
        )
        logger.info(f"💡 Reasoning: {ai_decision.get('reasoning', 'N/A')[:200]}")

        # Step 4: Risk Validation & Execution
        action = ai_decision.get("action", "HOLD")

        if action in ("BUY", "SELL"):
            risk_check = self.risk.validate_trade(
                ai_decision, account_info, open_positions, pair_config,
            )

            if risk_check.get("approved"):
                trade_result = self._execute_trade(
                    symbol, ai_decision, risk_check, pair_config,
                )
                if trade_result:
                    ai_decision["trade_executed"] = True
                    ai_decision["trade_result"] = trade_result
            else:
                logger.info(
                    f"🚫 Trade rejected: {risk_check.get('reason')}"
                )

        elif action == "CLOSE":
            # Check if we have a position to close
            for pos in open_positions:
                if pos.get("symbol") == symbol:
                    if self.risk.should_close_position(pos, ai_decision):
                        self.mt5.close_position(pos["ticket"])
                        logger.info(
                            f"📤 Closed position #{pos['ticket']} for {symbol}"
                        )

        return ai_decision

    def _execute_trade(
        self,
        symbol: str,
        ai_decision: dict,
        risk_check: dict,
        pair_config: dict,
    ) -> Optional[dict]:
        """Execute an approved trade on MT5."""
        action = ai_decision["action"]
        lot = risk_check["adjusted_lot"]
        sl = risk_check["adjusted_sl"]
        tp = risk_check["adjusted_tp"]

        logger.info(
            f"🎯 EXECUTING: {action} {lot} lots {symbol} | "
            f"SL: {sl} | TP: {tp}"
        )

        result = self.mt5.open_position(
            symbol=symbol,
            order_type=action,
            lot=lot,
            sl=sl,
            tp=tp,
            comment=f"AI_{ai_decision.get('confidence', 0)}%",
        )

        if result:
            trade_record = {
                **result,
                "ai_confidence": ai_decision.get("confidence"),
                "ai_reasoning": ai_decision.get("reasoning", "")[:500],
                "risk_level": ai_decision.get("risk_level", "MEDIUM"),
                "timestamp": datetime.now().isoformat(),
            }
            self.trade_history.append(trade_record)
            self._save_trade_history()

            logger.info(f"✅ Trade executed successfully!")
            return result
        else:
            logger.error(f"❌ Trade execution failed for {symbol}")
            return None

    def run_single_analysis(self, symbol: str = None) -> list:
        """Run a single analysis cycle (for manual/API use)."""
        if not self.mt5.connected:
            self.mt5.connect()

        account_info = self.mt5.get_account_info()
        open_positions = self.mt5.get_positions()
        results = []

        pairs_to_analyze = self.pairs
        if symbol:
            pairs_to_analyze = [
                p for p in self.pairs if p["symbol"] == symbol
            ]

        for pair_config in pairs_to_analyze:
            try:
                result = self._analyze_pair(
                    pair_config["symbol"],
                    pair_config["display_name"],
                    pair_config,
                    account_info,
                    open_positions,
                )
                if result:
                    results.append(result)
            except Exception as e:
                logger.error(f"Error analyzing {pair_config['symbol']}: {e}")

        return results

    def get_status(self) -> dict:
        """Get current engine status."""
        account = self.mt5.get_account_info() if self.mt5.connected else {}
        positions = self.mt5.get_positions() if self.mt5.connected else []

        return {
            "running": self.running,
            "connected": self.mt5.connected,
            "trading_mode": TRADING_MODE,
            "account": account,
            "open_positions": positions,
            "last_analyses": {
                sym: {
                    "action": data["ai"].get("action"),
                    "confidence": data["ai"].get("confidence"),
                    "trend": data["ta"].get("trend"),
                    "strength": data["ta"].get("strength"),
                    "timestamp": data["timestamp"],
                }
                for sym, data in self.last_analyses.items()
            },
            "risk_report": self.risk.get_risk_report(account, positions),
            "total_trades": len(self.trade_history),
            "recent_trades": self.trade_history[-5:] if self.trade_history else [],
        }

    def _load_trade_history(self):
        """Load trade history from file."""
        if self.trade_log_path.exists():
            try:
                with open(self.trade_log_path, "r") as f:
                    self.trade_history = json.load(f)
            except Exception:
                self.trade_history = []

    def _save_trade_history(self):
        """Save trade history to file."""
        try:
            with open(self.trade_log_path, "w") as f:
                json.dump(self.trade_history, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save trade history: {e}")
