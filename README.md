# 🤖 AI Trading System

**Automated Trading System powered by Gemini AI + MetaTrader 5**

AI Trading System yang menganalisis pasar secara otomatis menggunakan Google Gemini AI, menghitung indikator teknikal, dan mengeksekusi trade pada MetaTrader 5.

## 📊 Trading Pairs

| Pair | Description |
|------|-------------|
| EUR/USD | Euro vs US Dollar |
| GBP/JPY | British Pound vs Japanese Yen |
| XAU/USD | Gold vs US Dollar |

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    AI Trading System                      │
├──────────────────────────────────────────────────────────┤
│                                                          │
│   ┌─────────────┐    ┌──────────────┐    ┌───────────┐  │
│   │  MT5 Data    │───▶│  Technical   │───▶│  Gemini   │  │
│   │  Connector   │    │  Analysis    │    │  AI       │  │
│   └─────────────┘    └──────────────┘    └─────┬─────┘  │
│         ▲                                       │        │
│         │              ┌──────────────┐         │        │
│         │              │    Risk      │◀────────┘        │
│         │              │  Manager     │                  │
│         │              └──────┬───────┘                  │
│         │                     │                          │
│         └─────────────────────┘                          │
│                  Execute Trade                           │
├──────────────────────────────────────────────────────────┤
│   Web Dashboard  │  MCP Server  │  CLI Interface         │
└──────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### 1. Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure `.env`
```env
GEMINI_API_KEY=your_gemini_api_key

# MetaTrader 5 (isi jika menggunakan MT5 di Windows)
MT5_LOGIN=your_login
MT5_PASSWORD=your_password
MT5_SERVER=your_broker_server

# Trading Settings
TRADING_MODE=demo
MAX_RISK_PERCENT=2.0
DEFAULT_LOT_SIZE=0.01
```

### 3. Run

```bash
# Single analysis (rekomendasi untuk test)
python main.py analyze

# Analyze specific pair
python main.py analyze --symbol EURUSD

# Start auto-trading bot
python main.py run

# Web Dashboard
python main.py dashboard

# MCP Server (untuk AI agent integration)
python main.py mcp
```

## 🖥️ Modes

| Mode | Command | Description |
|------|---------|-------------|
| **Analyze** | `python main.py analyze` | Run single analysis cycle |
| **Run** | `python main.py run` | Continuous auto-trading |
| **Dashboard** | `python main.py dashboard` | Web UI at localhost:5000 |
| **Status** | `python main.py status` | Show current status |
| **MCP** | `python main.py mcp` | Start MCP server |

## 🧠 AI Analysis Pipeline

1. **Data Collection** — Fetch OHLCV candles from MT5
2. **Technical Analysis** — Calculate 15+ indicators:
   - EMA (9, 21, 50, 200)
   - RSI, MACD, Stochastic
   - Bollinger Bands, ATR, ADX
   - Support/Resistance levels
3. **AI Interpretation** — Gemini AI analyzes all data
4. **Risk Validation** — Position sizing, daily limits
5. **Execution** — Open/close positions on MT5

## 🔌 MCP Integration

Add to your MCP client config (`mcp_config.json`):
```json
{
    "mcpServers": {
        "ai-trading": {
            "command": "python",
            "args": ["mcp_server.py"],
            "cwd": "/path/to/AITrading"
        }
    }
}
```

### Available MCP Tools:
- `analyze_market` — Analyze specific pair
- `analyze_all_pairs` — Analyze all pairs
- `execute_trade` — Execute BUY/SELL
- `close_position` — Close position
- `get_open_positions` — List positions
- `get_account_info` — Account details
- `get_market_price` — Current price
- `get_trading_status` — Full status
- `get_trade_history` — Trade history

## ⚠️ Important Notes

- **Simulation Mode**: Jika MetaTrader 5 tidak terinstall (Mac/Linux), sistem berjalan dalam mode simulasi dengan data sintetis
- **MT5 hanya tersedia di Windows**: Untuk live trading, jalankan di Windows dengan MT5 terminal terinstall
- **Selalu test di DEMO account terlebih dahulu!**
- Sistem ini untuk edukasi dan riset, bukan financial advice

## 📁 Project Structure

```
AITrading/
├── main.py              # Entry point & CLI
├── mcp_server.py        # MCP server
├── requirements.txt     # Dependencies
├── .env                 # Configuration
├── mcp_config.json      # MCP client config
├── config/
│   └── settings.py      # Centralized settings
├── core/
│   ├── mt5_connector.py # MetaTrader 5 integration
│   ├── technical_analysis.py  # Technical indicators
│   ├── ai_analyzer.py   # Gemini AI analysis
│   ├── risk_manager.py  # Risk management
│   └── trading_engine.py # Main orchestrator
├── dashboard/
│   ├── app.py           # Flask web dashboard
│   └── templates/
│       └── index.html   # Dashboard UI
└── logs/                # Trading logs
```
