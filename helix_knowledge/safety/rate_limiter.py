from __future__ import annotations

import threading
import time
from urllib.parse import urlparse


class RateLimiter:
    def __init__(self, *, min_interval_seconds: float = 1.5) -> None:
        self.min_interval_seconds = max(0.0, float(min_interval_seconds))
        self._last_by_host: dict[str, float] = {}
        self._lock = threading.Lock()

    def wait(self, url: str) -> float:
        host = (urlparse(url).netloc or "").lower() or "local"
        with self._lock:
            now = time.monotonic()
            last = self._last_by_host.get(host)
            if last is None:
                self._last_by_host[host] = now
                return 0.0
            elapsed = now - last
            sleep_for = max(0.0, self.min_interval_seconds - elapsed)
            if sleep_for > 0:
                time.sleep(sleep_for)
            self._last_by_host[host] = time.monotonic()
            return sleep_for
