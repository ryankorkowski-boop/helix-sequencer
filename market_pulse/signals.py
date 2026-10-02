from dataclasses import dataclass
from collections import deque
from statistics import mean, pstdev
import math

@dataclass(frozen=True)
class Signal:
    symbol: str
    kind: str
    score: float
    message: str
    price: float
    volume: float

class SignalEngine:
    def __init__(self, window: int = 60):
        self.prices: dict[str, deque[float]] = {}
        self.volumes: dict[str, deque[float]] = {}
        self.window = window

    def update(self, symbol: str, price: float, volume: float) -> list[Signal]:
        ps = self.prices.setdefault(symbol, deque(maxlen=self.window))
        vs = self.volumes.setdefault(symbol, deque(maxlen=self.window))
        signals: list[Signal] = []
        if len(ps) >= 10:
            baseline = mean(ps)
            sigma = pstdev(ps) or 1e-9
            z = (price - baseline) / sigma
            if abs(z) >= 2.5:
                signals.append(Signal(symbol, "price_anomaly", min(abs(z) / 5, 1), f"Price z-score {z:+.2f}", price, volume))
            if price > ps[-1] and price > mean(list(ps)[-5:]):
                signals.append(Signal(symbol, "momentum", min(abs(price / baseline - 1) * 20, 1), "Short-window upside momentum", price, volume))
        if len(vs) >= 10:
            vb = mean(vs)
            if vb > 0 and volume >= vb * 3:
                signals.append(Signal(symbol, "volume_anomaly", min(volume / vb / 5, 1), f"Volume {volume / vb:.1f}x rolling baseline", price, volume))
        ps.append(price)
        vs.append(volume)
        return signals

def signal_to_dict(s: Signal) -> dict:
    return {
        "symbol": s.symbol, "kind": s.kind, "score": round(s.score, 4),
        "message": s.message, "price": s.price, "volume": s.volume
    }
