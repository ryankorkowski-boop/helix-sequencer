import json
import subprocess
import sys


def test_style_engine_preview_outputs_decision_json() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "tools.style_engine_preview"],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)

    assert isinstance(payload, list)
    assert payload
    assert {"start", "duration", "intent", "effect", "targets", "palette", "intensity"}.issubset(payload[0])
    assert any(item["style"] == "SpatialHelix" for item in payload)
    assert any(item["targets"] for item in payload)
