# Market Pulse MVP

A separate, paper-first live market intelligence prototype. It is intentionally isolated from Helix Sequencer logic.

## Goals
- Consume Alpaca WebSocket market data when credentials are supplied.
- Run deterministic anomaly/momentum/volume signals locally.
- Persist a compact event log.
- Expose a local dashboard/API.
- Start in PAPER/OBSERVE mode; no live orders are implemented.

## Data limitations
Alpaca's free Basic market-data plan provides real-time US equities data from IEX only, with a 30-symbol WebSocket subscription limit. It is not a consolidated all-exchange feed.

## Quick start
```bash
python -m venv .venv
# activate the venv
pip install -e .
copy .env.example .env
python -m market_pulse
```

Open http://127.0.0.1:8765.

Set ALPACA_API_KEY and ALPACA_API_SECRET for live IEX data. Without keys, the service starts in demo mode so the pipeline can be exercised safely.

This project does not claim profitable trading signals and does not execute trades.
