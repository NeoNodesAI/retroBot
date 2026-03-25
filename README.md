# retroBot

Real-time crypto intelligence agent built with LangGraph.  
Developed by **NeoNodes**.

---

## Setup

```bash
# Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your API keys

# Start server
python -m src.api
```

Server runs at `http://localhost:8000`

---

## Features

- Real-time crypto prices from Binance, Coinbase, Kraken
- LangGraph-powered conversational agent
- LangGraph Cloud-compatible API (streaming + sync)
- On-chain tooling via Web3
- Warden Protocol integration

---

## API

```bash
# Health check
curl http://localhost:8000/health

# Ask a question
curl -X POST http://localhost:8000/runs/wait \
  -H "Content-Type: application/json" \
  -d '{"assistant_id":"retrobot-warden-001","input":{"messages":[{"role":"user","content":"BTC price"}]}}'
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
