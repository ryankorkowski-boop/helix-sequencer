from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class BridgeResult:
    provider: str
    configured: bool
    message: str


def is_configured() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY", "").strip())


def request_guidance(task: str, context: str = "") -> BridgeResult:
    _ = (task, context)
    if not is_configured():
        return BridgeResult(
            provider="chatgpt",
            configured=False,
            message="ChatGPT bridge is disabled. Set OPENAI_API_KEY before wiring live calls.",
        )
    return BridgeResult(
        provider="chatgpt",
        configured=True,
        message="ChatGPT bridge is intentionally stubbed in this safe restructure. Prefer rule-based logic first.",
    )
