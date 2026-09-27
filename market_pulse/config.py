from dataclasses import dataclass
import os

@dataclass(frozen=True)
class Settings:
    api_key: str = os.getenv("ALPACA_API_KEY", "")
    api_secret: str = os.getenv("ALPACA_API_SECRET", "")
    symbols: tuple[str, ...] = tuple(
        s.strip().upper() for s in os.getenv("MARKET_PULSE_SYMBOLS", "SPY,QQQ,AAPL,MSFT,NVDA,TSLA").split(",") if s.strip()
    )
    host: str = os.getenv("MARKET_PULSE_HOST", "127.0.0.1")
    port: int = int(os.getenv("MARKET_PULSE_PORT", "8765"))
    demo: bool = os.getenv("MARKET_PULSE_DEMO", "").lower() in {"1", "true", "yes"}

    @property
    def live_feed_enabled(self) -> bool:
        return bool(self.api_key and self.api_secret) and not self.demo
