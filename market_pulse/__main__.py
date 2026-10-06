import asyncio
from .config import Settings
from .feed import demo_feed, alpaca_feed
from .signals import SignalEngine
from .server import State, start_server, run
from threading import Thread

async def main():
    settings = Settings()
    state = State()
    Thread(target=start_server, args=(settings.host, settings.port, state), daemon=True).start()
    engine = SignalEngine()
    if settings.live_feed_enabled:
        feed = alpaca_feed(settings.api_key, settings.api_secret, settings.symbols)
        mode = "LIVE IEX"
    else:
        feed = demo_feed(settings.symbols)
        mode = "DEMO"
    print(f"Market Pulse {mode}: http://{settings.host}:{settings.port}")
    await run(feed, engine, state)

if __name__ == "__main__":
    asyncio.run(main())
