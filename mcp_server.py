"""
MCP (Model Context Protocol) Server for AI Trading
Provides tools for AI agents to interact with the trading system.
"""
import asyncio
import json
import logging
from datetime import datetime

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
)

from core.trading_engine import TradingEngine

logger = logging.getLogger("AITrading.MCP")

# Initialize globals
app = Server("ai-trading-mcp")
engine = TradingEngine()


# ── Tool Definitions ─────────────────────────────────────────

@app.list_tools()
async def list_tools():
    """List all available MCP tools."""
    return [
        Tool(
            name="analyze_market",
            description=(
                "Analyze a specific trading pair using technical indicators and AI. "
                "Returns detailed analysis with recommendation."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Trading symbol: EURUSD, GBPJPY, or XAUUSD",
                        "enum": ["EURUSD", "GBPJPY", "XAUUSD"],
                    }
                },
                "required": ["symbol"],
            },
        ),
        Tool(
            name="analyze_all_pairs",
            description=(
                "Analyze all configured trading pairs (EURUSD, GBPJPY, XAUUSD). "
                "Returns analysis for each pair."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="execute_trade",
            description=(
                "Execute a trade (BUY or SELL) on a specific symbol. "
                "The trade goes through risk management validation first."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Trading symbol",
                        "enum": ["EURUSD", "GBPJPY", "XAUUSD"],
                    },
                    "action": {
                        "type": "string",
                        "description": "Trade direction",
                        "enum": ["BUY", "SELL"],
                    },
                    "lot_size": {
                        "type": "number",
                        "description": "Position size (default: 0.01)",
                        "default": 0.01,
                    },
                },
                "required": ["symbol", "action"],
            },
        ),
        Tool(
            name="close_position",
            description="Close an open position by ticket number.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticket": {
                        "type": "integer",
                        "description": "Position ticket number to close",
                    }
                },
                "required": ["ticket"],
            },
        ),
        Tool(
            name="get_open_positions",
            description="Get all currently open trading positions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Optional: filter by symbol",
                    }
                },
            },
        ),
        Tool(
            name="get_account_info",
            description="Get current account balance, equity, and margin information.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="get_market_price",
            description="Get current bid/ask price for a symbol.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Trading symbol",
                        "enum": ["EURUSD", "GBPJPY", "XAUUSD"],
                    }
                },
                "required": ["symbol"],
            },
        ),
        Tool(
            name="get_trading_status",
            description="Get overall trading system status including all analyses and risk report.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="get_trade_history",
            description="Get recent trade history.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of recent trades to return (default: 10)",
                        "default": 10,
                    }
                },
            },
        ),
    ]


# ── Tool Handlers ────────────────────────────────────────────

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle MCP tool calls."""
    try:
        if name == "analyze_market":
            result = engine.run_single_analysis(arguments["symbol"])
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2, default=str),
            )]

        elif name == "analyze_all_pairs":
            result = engine.run_single_analysis()
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2, default=str),
            )]

        elif name == "execute_trade":
            symbol = arguments["symbol"]
            action = arguments["action"]
            lot = arguments.get("lot_size", 0.01)

            # Get current data for trade validation
            if not engine.mt5.connected:
                engine.mt5.connect()

            tick = engine.mt5.get_tick(symbol)
            if not tick:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": f"Cannot get price for {symbol}"}),
                )]

            price = tick["ask"] if action == "BUY" else tick["bid"]

            # Find pair config
            pair_config = next(
                (p for p in engine.pairs if p["symbol"] == symbol), None
            )
            if not pair_config:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": f"Unknown symbol: {symbol}"}),
                )]

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
                comment="MCP_Trade",
            )

            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2, default=str),
            )]

        elif name == "close_position":
            success = engine.mt5.close_position(arguments["ticket"])
            return [TextContent(
                type="text",
                text=json.dumps({"success": success, "ticket": arguments["ticket"]}),
            )]

        elif name == "get_open_positions":
            symbol = arguments.get("symbol")
            positions = engine.mt5.get_positions(symbol)
            return [TextContent(
                type="text",
                text=json.dumps(positions, indent=2, default=str),
            )]

        elif name == "get_account_info":
            info = engine.mt5.get_account_info()
            return [TextContent(
                type="text",
                text=json.dumps(info, indent=2, default=str),
            )]

        elif name == "get_market_price":
            tick = engine.mt5.get_tick(arguments["symbol"])
            return [TextContent(
                type="text",
                text=json.dumps(tick, indent=2, default=str),
            )]

        elif name == "get_trading_status":
            status = engine.get_status()
            return [TextContent(
                type="text",
                text=json.dumps(status, indent=2, default=str),
            )]

        elif name == "get_trade_history":
            limit = arguments.get("limit", 10)
            history = engine.trade_history[-limit:]
            return [TextContent(
                type="text",
                text=json.dumps(history, indent=2, default=str),
            )]

        else:
            return [TextContent(
                type="text",
                text=json.dumps({"error": f"Unknown tool: {name}"}),
            )]

    except Exception as e:
        logger.error(f"MCP tool error ({name}): {e}")
        return [TextContent(
            type="text",
            text=json.dumps({"error": str(e)}),
        )]


# ── Main Entry ───────────────────────────────────────────────

async def main():
    """Run the MCP server."""
    logger.info("🚀 Starting AI Trading MCP Server...")
    engine.mt5.connect()

    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    asyncio.run(main())
