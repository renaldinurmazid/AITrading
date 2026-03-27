"""
AI Analyzer Module
Uses Google Gemini AI to analyze market conditions and make trading decisions.
"""
import json
import logging
from datetime import datetime
from typing import Optional

from google import genai
from google.genai import types

from config.settings import GEMINI_API_KEY, AI_MODEL

logger = logging.getLogger("AITrading.AI")


class AIAnalyzer:
    """
    Uses Gemini AI to interpret technical analysis data and market conditions
    to generate trading recommendations with reasoning.
    """

    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.model = AI_MODEL
        self.trade_history = []
        logger.info(f"🧠 AI Analyzer initialized with model: {self.model}")

    def analyze_market(
        self,
        symbol: str,
        ta_result: dict,
        support_resistance: dict,
        tick_data: Optional[dict] = None,
        account_info: Optional[dict] = None,
        open_positions: Optional[list] = None,
    ) -> dict:
        """
        Send market data to Gemini AI for comprehensive analysis.

        Returns a structured trading decision with:
        - action: BUY / SELL / HOLD / CLOSE
        - confidence: 0-100
        - reasoning: detailed explanation
        - entry_price, sl, tp (if action is BUY/SELL)
        - risk_reward_ratio
        """
        prompt = self._build_analysis_prompt(
            symbol, ta_result, support_resistance,
            tick_data, account_info, open_positions,
        )

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    top_p=0.8,
                    max_output_tokens=2048,
                    response_mime_type="application/json",
                ),
            )

            result = self._parse_ai_response(response.text, symbol)

            # Log the analysis
            logger.info(
                f"🧠 AI Analysis for {symbol}: "
                f"{result.get('action', 'UNKNOWN')} "
                f"(confidence: {result.get('confidence', 0)}%)"
            )

            return result

        except Exception as e:
            logger.error(f"❌ AI analysis error for {symbol}: {e}")
            return {
                "symbol": symbol,
                "action": "HOLD",
                "confidence": 0,
                "reasoning": f"AI analysis failed: {str(e)}",
                "timestamp": datetime.now().isoformat(),
            }

    def _build_analysis_prompt(
        self,
        symbol: str,
        ta_result: dict,
        support_resistance: dict,
        tick_data: Optional[dict],
        account_info: Optional[dict],
        open_positions: Optional[list],
    ) -> str:
        """Build the comprehensive analysis prompt for Gemini."""

        # Format indicators nicely
        indicators = ta_result.get("indicators", {})
        signals = ta_result.get("signals", [])
        trend = ta_result.get("trend", "UNKNOWN")
        strength = ta_result.get("strength", 0)
        ta_recommendation = ta_result.get("recommendation", "HOLD")

        prompt = f"""You are an expert forex and commodities trader AI with 20+ years of experience.
Analyze the following market data for {symbol} and provide a trading decision.

═══════════════════════════════════════════════════
MARKET DATA FOR: {symbol}
Timestamp: {datetime.now().isoformat()}
═══════════════════════════════════════════════════

📊 CURRENT PRICE DATA:
- Current Price: {indicators.get('current_price', 'N/A')}
"""
        if tick_data:
            prompt += f"""- Bid: {tick_data.get('bid', 'N/A')}
- Ask: {tick_data.get('ask', 'N/A')}
- Spread: {tick_data.get('spread', 'N/A')}
"""

        prompt += f"""
📈 TREND ANALYSIS:
- Overall Trend: {trend}
- Signal Strength: {strength}%
- TA Recommendation: {ta_recommendation}

📊 MOVING AVERAGES:
- EMA 9:   {indicators.get('ema_9', 'N/A')}
- EMA 21:  {indicators.get('ema_21', 'N/A')}
- EMA 50:  {indicators.get('ema_50', 'N/A')}
- EMA 200: {indicators.get('ema_200', 'N/A')}
- Price vs EMA200: {indicators.get('price_vs_ema200', 'N/A')}

📉 MOMENTUM INDICATORS:
- RSI (14): {indicators.get('rsi', 'N/A')} ({indicators.get('rsi_signal', 'N/A')})
- MACD Line: {indicators.get('macd_line', 'N/A')}
- MACD Signal: {indicators.get('macd_signal_line', 'N/A')}
- MACD Histogram: {indicators.get('macd_histogram', 'N/A')}
- Stochastic K: {indicators.get('stoch_k', 'N/A')}
- Stochastic D: {indicators.get('stoch_d', 'N/A')}

📊 VOLATILITY:
- BB Upper: {indicators.get('bb_upper', 'N/A')}
- BB Middle: {indicators.get('bb_middle', 'N/A')}
- BB Lower: {indicators.get('bb_lower', 'N/A')}
- ATR (14): {indicators.get('atr', 'N/A')}

📊 TREND STRENGTH:
- ADX: {indicators.get('adx', 'N/A')}
- DI+: {indicators.get('di_plus', 'N/A')}
- DI-: {indicators.get('di_minus', 'N/A')}

🔑 SUPPORT & RESISTANCE:
- Pivot: {support_resistance.get('pivot', 'N/A')}
- Support: {support_resistance.get('support', 'N/A')}
- Resistance: {support_resistance.get('resistance', 'N/A')}

⚡ ACTIVE SIGNALS:
"""
        for sig in signals:
            prompt += f"- {sig['name']}: {sig['direction']} (weight: {sig['weight']})\n"

        if open_positions:
            prompt += "\n📋 CURRENT OPEN POSITIONS:\n"
            for pos in open_positions:
                if pos.get("symbol") == symbol:
                    prompt += (
                        f"- {pos['type']} {pos['volume']} lots @ {pos['open_price']} "
                        f"| P/L: {pos.get('profit', 0)}\n"
                    )
            if not any(p.get("symbol") == symbol for p in open_positions):
                prompt += "- No open positions for this symbol\n"

        if account_info:
            prompt += f"""
💰 ACCOUNT:
- Balance: {account_info.get('balance', 'N/A')}
- Equity: {account_info.get('equity', 'N/A')}
- Free Margin: {account_info.get('free_margin', 'N/A')}
"""

        prompt += """
═══════════════════════════════════════════════════
INSTRUCTIONS:
═══════════════════════════════════════════════════

Based on the above data, provide your trading decision in the following JSON format:

{
    "action": "BUY" | "SELL" | "HOLD" | "CLOSE",
    "confidence": <0-100>,
    "entry_price": <float or null>,
    "stop_loss": <float or null>,
    "take_profit": <float or null>,
    "lot_size": <float, recommended 0.01-0.1>,
    "risk_reward_ratio": <float or null>,
    "reasoning": "<detailed explanation of your analysis>",
    "key_factors": ["<factor1>", "<factor2>", "<factor3>"],
    "risk_level": "LOW" | "MEDIUM" | "HIGH",
    "market_conditions": "<brief description of current market state>",
    "timeframe_bias": {
        "short_term": "BULLISH" | "BEARISH" | "NEUTRAL",
        "medium_term": "BULLISH" | "BEARISH" | "NEUTRAL",
        "long_term": "BULLISH" | "BEARISH" | "NEUTRAL"
    }
}

RULES:
1. Only recommend BUY/SELL when confidence > 60%
2. Always set stop_loss and take_profit for BUY/SELL
3. Aim for risk:reward ratio of at least 1:1.5
4. Consider all indicators - don't rely on just one
5. If signals are conflicting, recommend HOLD
6. Be conservative with lot sizing
7. If there's already an open position for this symbol, consider HOLD unless strong reversal signal
8. Factor in ATR for appropriate SL/TP distances
"""

        return prompt

    def _parse_ai_response(self, response_text: str, symbol: str) -> dict:
        """Parse and validate the AI response."""
        try:
            result = json.loads(response_text)

            # Ensure required fields
            result.setdefault("symbol", symbol)
            result.setdefault("action", "HOLD")
            result.setdefault("confidence", 0)
            result.setdefault("reasoning", "No reasoning provided")
            result.setdefault("timestamp", datetime.now().isoformat())

            # Validate action
            valid_actions = {"BUY", "SELL", "HOLD", "CLOSE"}
            if result["action"] not in valid_actions:
                result["action"] = "HOLD"

            # Validate confidence
            result["confidence"] = max(0, min(100, int(result["confidence"])))

            # Safety: don't trade if confidence too low
            if result["confidence"] < 60 and result["action"] in ("BUY", "SELL"):
                result["action"] = "HOLD"
                result["reasoning"] += (
                    " [SAFETY: Confidence too low for trade execution]"
                )

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response: {e}")
            logger.debug(f"Raw response: {response_text[:500]}")
            return {
                "symbol": symbol,
                "action": "HOLD",
                "confidence": 0,
                "reasoning": f"Failed to parse AI response: {str(e)}",
                "timestamp": datetime.now().isoformat(),
            }

    def get_market_summary(self, analyses: list) -> str:
        """Generate a human-readable market summary from multiple analyses."""
        if not analyses:
            return "No analyses available."

        prompt = f"""Based on the following AI trading analyses, create a brief market summary report:

{json.dumps(analyses, indent=2, default=str)}

Provide a concise, professional market summary covering:
1. Overall market sentiment
2. Key opportunities
3. Risk warnings
4. Top recommendation

Keep it under 300 words. Use professional trading language."""

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.5,
                    max_output_tokens=1024,
                ),
            )
            return response.text
        except Exception as e:
            return f"Failed to generate summary: {e}"
