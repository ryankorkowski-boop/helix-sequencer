import asyncio, json, random, time
from typing import AsyncIterator

async def demo_feed(symbols: tuple[str, ...]) -> AsyncIterator[dict]:
    prices = {s: 100.0 + i * 17 for i, s in enumerate(symbols)}
    while True:
        for symbol in symbols:
            move = random.gauss(0, 0.12)
            prices[symbol] = max(1.0, prices[symbol] + move)
            volume = max(1, random.gauss(5000, 1200))
            if random.random() < 0.02:
                volume *= random.randint(4, 10)
            yield {"T": "t", "S": symbol, "p": prices[symbol], "s": 1, "v": volume, "ts": time.time()}
        await asyncio.sleep(0.25)

async def alpaca_feed(api_key: str, api_secret: str, symbols: tuple[str, ...]) -> AsyncIterator[dict]:
    import websockets
    url = "wss://stream.data.alpaca.markets/v2/iex"
    async with websockets.connect(url, ping_interval=20, ping_timeout=20) as ws:
        await ws.send(json.dumps({"action": "auth", "key": api_key, "secret": api_secret}))
        await ws.send(json.dumps({"action": "subscribe", "trades": list(symbols)}))
        async for raw in ws:
            for item in json.loads(raw):
                if item.get("T") == "t":
                    yield {"T": "t", "S": item["S"], "p": float(item["p"]), "s": item.get("s", 0), "v": float(item.get("s", 0)), "ts": time.time()}
