# retroBot

Real-time crypto intelligence agent built with LangGraph.  
Developed by **NeoNodes**.

---

## What it does

retroBot is a conversational AI agent that answers crypto questions in natural language — prices, technical analysis, market signals, and on-chain activity, all in one place.

Ask things like:
- *"What's the BTC price?"*
- *"Give me a technical analysis of ETH"*
- *"Is SOL overbought right now?"*
- *"Compare BTC price across exchanges"*

---

## Features

**Market Data**
- Live prices from Binance, Coinbase, and Kraken with cross-exchange comparison
- Historical OHLCV data fetched on demand

**Technical Analysis**
- RSI, MACD, EMA, Bollinger Bands, Momentum
- Moving averages (SMA/EMA) across multiple timeframes
- Support & resistance level detection
- Volatility scoring

**On-Chain**
- Inference recording via Warden Protocol (Base network)
- Web3 wallet integration for on-chain attestations

**API & Infrastructure**
- LangGraph Cloud-compatible REST API (streaming + sync)
- Conversational memory via thread management
- Retro-themed `/retro` command system for status, stats, and diagnostics

---

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Add your API keys to .env

python -m src.api
```

Server runs at `http://localhost:8000`

---

## API

```bash
# Health check
curl http://localhost:8000/health

# Ask a question
curl -X POST http://localhost:8000/runs/wait \
  -H "Content-Type: application/json" \
  -d '{"assistant_id":"retrobot-warden-001","input":{"messages":[{"role":"user","content":"BTC price"}]}}'

# Streaming response
curl -X POST http://localhost:8000/runs/stream \
  -H "Content-Type: application/json" \
  -d '{"assistant_id":"retrobot-warden-001","input":{"messages":[{"role":"user","content":"ETH technical analysis"}]}}'
```

Key endpoints: `/runs/wait`, `/runs/stream`, `/threads`, `/health`, `/info`

---

## Configuration

Copy `.env.example` to `.env` and fill in:

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Anthropic API key (required) |
| `AGENT_PRIVATE_KEY` | Wallet private key (optional, for on-chain features) |
| `BASE_RPC_URL` | Base network RPC URL |

---

## License

MIT
