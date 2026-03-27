"""
Web Dashboard for AI Trading System
Provides real-time monitoring and control via a web interface.
"""
import json
import logging
from datetime import datetime

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO

from core.trading_engine import TradingEngine

logger = logging.getLogger("AITrading.Dashboard")


def create_app() -> Flask:
    """Create and configure the Flask dashboard app."""
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )
    app.config["SECRET_KEY"] = "ai-trading-secret-key"
    socketio = SocketIO(app, cors_allowed_origins="*")

    # Shared engine instance
    engine = TradingEngine()
    if not engine.mt5.connected:
        engine.mt5.connect()

    # ── Routes ───────────────────────────────────────────────

    @app.route("/")
    def index():
        """Main dashboard page."""
        return render_template("index.html")

    @app.route("/api/status")
    def api_status():
        """Get trading system status."""
        return jsonify(engine.get_status())

    @app.route("/api/analyze", methods=["POST"])
    def api_analyze():
        """Run analysis for a symbol or all pairs."""
        data = request.json or {}
        symbol = data.get("symbol")
        results = engine.run_single_analysis(symbol)
        return jsonify(results)

    @app.route("/api/analyze/<symbol>")
    def api_analyze_symbol(symbol):
        """Run analysis for a specific symbol."""
        results = engine.run_single_analysis(symbol.upper())
        return jsonify(results)

    @app.route("/api/positions")
    def api_positions():
        """Get open positions."""
        return jsonify(engine.mt5.get_positions())

    @app.route("/api/account")
    def api_account():
        """Get account info."""
        return jsonify(engine.mt5.get_account_info())

    @app.route("/api/trade", methods=["POST"])
    def api_trade():
        """Execute a manual trade."""
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400

        symbol = data.get("symbol")
        action = data.get("action")
        lot = data.get("lot_size", 0.01)

        if not symbol or not action:
            return jsonify({"error": "symbol and action required"}), 400

        pair_config = next(
            (p for p in engine.pairs if p["symbol"] == symbol), None
        )
        if not pair_config:
            return jsonify({"error": f"Unknown symbol: {symbol}"}), 400

        tick = engine.mt5.get_tick(symbol)
        if not tick:
            return jsonify({"error": "Cannot get market price"}), 500

        price = tick["ask"] if action == "BUY" else tick["bid"]
        pip_value = pair_config["pip_value"]

        if action == "BUY":
            sl = price - pair_config["sl_pips"] * pip_value
            tp = price + pair_config["tp_pips"] * pip_value
        else:
            sl = price + pair_config["sl_pips"] * pip_value
            tp = price - pair_config["tp_pips"] * pip_value

        result = engine.mt5.open_position(
            symbol=symbol,
            order_type=action,
            lot=lot,
            sl=sl,
            tp=tp,
            comment="Dashboard_Trade",
        )

        if result:
            return jsonify({"success": True, "trade": result})
        return jsonify({"error": "Trade execution failed"}), 500

    @app.route("/api/close/<int:ticket>", methods=["POST"])
    def api_close(ticket):
        """Close a position."""
        success = engine.mt5.close_position(ticket)
        return jsonify({"success": success, "ticket": ticket})

    @app.route("/api/history")
    def api_history():
        """Get trade history."""
        limit = request.args.get("limit", 50, type=int)
        return jsonify(engine.trade_history[-limit:])

    @app.route("/api/tick/<symbol>")
    def api_tick(symbol):
        """Get current tick data."""
        tick = engine.mt5.get_tick(symbol.upper())
        return jsonify(tick or {"error": "No tick data"})

    # ── SocketIO Events ──────────────────────────────────────

    @socketio.on("connect")
    def handle_connect():
        logger.info("Client connected to dashboard")

    @socketio.on("request_analysis")
    def handle_analysis_request(data):
        symbol = data.get("symbol")
        results = engine.run_single_analysis(symbol)
        socketio.emit("analysis_result", results)

    @socketio.on("request_status")
    def handle_status_request():
        status = engine.get_status()
        socketio.emit("status_update", status)

    return app
