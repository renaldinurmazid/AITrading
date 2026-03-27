"""
AI Trading System - Main Entry Point
Run the trading bot in different modes.
"""
import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from config.settings import LOG_DIR, TRADING_MODE, TRADING_PAIRS

console = Console()


def setup_logging(verbose: bool = False):
    """Configure logging for the application."""
    log_level = logging.DEBUG if verbose else logging.INFO
    log_file = LOG_DIR / f"trading_{datetime.now().strftime('%Y%m%d')}.log"

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file),
        ],
    )


def print_banner():
    """Print the application banner."""
    banner = Text()
    banner.append("🤖 ", style="bold")
    banner.append("AI TRADING SYSTEM", style="bold cyan")
    banner.append(" 🤖\n", style="bold")
    banner.append(f"Powered by Gemini AI + MetaTrader 5\n", style="dim")
    banner.append(f"Mode: {TRADING_MODE.upper()}", style="bold yellow")

    console.print(Panel(banner, border_style="cyan", padding=(1, 2)))

    # Trading pairs table
    table = Table(title="📊 Trading Pairs", border_style="cyan")
    table.add_column("Symbol", style="bold white")
    table.add_column("Name", style="cyan")
    table.add_column("Lot Size", style="green")
    table.add_column("SL (pips)", style="red")
    table.add_column("TP (pips)", style="green")

    for pair in TRADING_PAIRS:
        table.add_row(
            pair["symbol"],
            pair["display_name"],
            str(pair["lot_size"]),
            str(pair["sl_pips"]),
            str(pair["tp_pips"]),
        )

    console.print(table)
    console.print()


def run_bot():
    """Run the trading bot in continuous mode."""
    from core.trading_engine import TradingEngine

    engine = TradingEngine()
    engine.start()


def run_single_analysis(symbol: str = None):
    """Run a single analysis cycle."""
    from core.trading_engine import TradingEngine

    engine = TradingEngine()
    results = engine.run_single_analysis(symbol)

    for result in results:
        sym = result.get("symbol", "Unknown")
        action = result.get("action", "HOLD")
        confidence = result.get("confidence", 0)
        reasoning = result.get("reasoning", "N/A")

        color = {"BUY": "green", "SELL": "red", "HOLD": "yellow"}.get(
            action, "white"
        )

        console.print(
            Panel(
                f"[bold {color}]{action}[/] | Confidence: {confidence}%\n\n"
                f"{reasoning[:300]}",
                title=f"📊 {sym}",
                border_style=color,
            )
        )

    engine.mt5.disconnect()


def run_status():
    """Show current trading status."""
    from core.trading_engine import TradingEngine

    engine = TradingEngine()
    status = engine.get_status()

    # Account info
    account = status.get("account", {})
    console.print(
        Panel(
            f"Balance: ${account.get('balance', 0):,.2f}\n"
            f"Equity: ${account.get('equity', 0):,.2f}\n"
            f"Free Margin: ${account.get('free_margin', 0):,.2f}\n"
            f"Mode: {account.get('mode', 'N/A')}",
            title="💰 Account",
            border_style="green",
        )
    )

    # Positions
    positions = status.get("open_positions", [])
    if positions:
        table = Table(title="📋 Open Positions", border_style="blue")
        table.add_column("Ticket")
        table.add_column("Symbol")
        table.add_column("Type")
        table.add_column("Volume")
        table.add_column("Profit", style="green")

        for pos in positions:
            table.add_row(
                str(pos.get("ticket")),
                pos.get("symbol"),
                pos.get("type"),
                str(pos.get("volume")),
                f"${pos.get('profit', 0):.2f}",
            )
        console.print(table)
    else:
        console.print("[dim]No open positions[/]")

    engine.mt5.disconnect()


def run_dashboard():
    """Run the web dashboard."""
    from dashboard.app import create_app

    app = create_app()
    console.print(
        "[bold green]🌐 Dashboard starting at http://localhost:5005[/]"
    )
    app.run(host="0.0.0.0", port=5005, debug=True)


def run_mcp_server():
    """Run the MCP server for AI agent integration."""
    import asyncio
    from mcp_server import main

    console.print("[bold green]🔌 Starting MCP Server...[/]")
    asyncio.run(main())


def main():
    parser = argparse.ArgumentParser(
        description="🤖 AI Trading System - Gemini AI + MetaTrader 5"
    )
    parser.add_argument(
        "command",
        choices=["run", "analyze", "status", "dashboard", "mcp"],
        help=(
            "Command to execute: "
            "run=start trading bot, "
            "analyze=single analysis, "
            "status=show status, "
            "dashboard=web UI, "
            "mcp=start MCP server"
        ),
    )
    parser.add_argument(
        "--symbol",
        type=str,
        help="Specific symbol to analyze (e.g., EURUSD)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()
    setup_logging(args.verbose)
    print_banner()

    if args.command == "run":
        run_bot()
    elif args.command == "analyze":
        run_single_analysis(args.symbol)
    elif args.command == "status":
        run_status()
    elif args.command == "dashboard":
        run_dashboard()
    elif args.command == "mcp":
        run_mcp_server()


if __name__ == "__main__":
    main()
