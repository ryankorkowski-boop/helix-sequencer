from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from tools import check_xlights_rest_sequence as rest_check


def _write_xsq(path: Path) -> Path:
    path.write_text("<xsequence></xsequence>\n", encoding="utf-8")
    return path


def test_sequence_check_records_successful_xlights_response(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    xsq = _write_xsq(tmp_path / "helix_flow_demo.xsq")
    requests: list[tuple[str, str, dict[str, Any] | None]] = []

    def fake_request_json(
        method: str,
        url: str,
        payload: dict[str, Any] | None = None,
        timeout: float = 3.0,
    ) -> dict[str, Any]:
        requests.append((method, url, payload))
        if url.endswith("/getVersion"):
            return {"res": 200, "version": "2024.9"}
        return {"res": 200, "msg": "Sequence checked.", "output": "CheckSeq.txt"}

    monkeypatch.setattr(rest_check, "_request_json", fake_request_json)

    result = rest_check.check_xlights_rest_sequence(xsq, ports=(49913,))

    assert result.status == "checked"
    assert result.endpoint == "http://127.0.0.1:49913"
    assert result.xlights_version == "2024.9"
    assert result.check_response == {"res": 200, "msg": "Sequence checked.", "output": "CheckSeq.txt"}
    assert result.rest_probes[0].reachable is True
    assert requests[1] == (
        "POST",
        "http://127.0.0.1:49913/xlDoAutomation",
        {"cmd": "checkSequence", "seq": str(xsq.resolve())},
    )


def test_sequence_check_records_blocked_when_rest_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    xsq = _write_xsq(tmp_path / "helix_flow_demo.xsq")

    def fake_request_json(
        method: str,
        url: str,
        payload: dict[str, Any] | None = None,
        timeout: float = 3.0,
    ) -> dict[str, Any]:
        raise OSError("connection refused")

    monkeypatch.setattr(rest_check, "_request_json", fake_request_json)

    result = rest_check.check_xlights_rest_sequence(xsq, ports=(49913, 49914))

    assert result.status == "blocked"
    assert result.endpoint is None
    assert [probe.reachable for probe in result.rest_probes] == [False, False]
    assert "connection refused" in "\n".join(result.errors)


def test_sequence_check_records_failed_when_check_sequence_rejects_xsq(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    xsq = _write_xsq(tmp_path / "helix_flow_demo.xsq")

    def fake_request_json(
        method: str,
        url: str,
        payload: dict[str, Any] | None = None,
        timeout: float = 3.0,
    ) -> dict[str, Any]:
        if url.endswith("/getVersion"):
            return {"res": 200, "version": "2024.9"}
        return {"res": 500, "msg": "Sequence contains invalid effects."}

    monkeypatch.setattr(rest_check, "_request_json", fake_request_json)

    result = rest_check.check_xlights_rest_sequence(xsq, ports=(49913,))

    assert result.status == "failed"
    assert result.endpoint == "http://127.0.0.1:49913"
    assert result.check_response == {"res": 500, "msg": "Sequence contains invalid effects."}
    assert "non-success" in result.errors[-1]


def test_write_sequence_check_outputs_json_and_markdown(tmp_path: Path) -> None:
    xsq = _write_xsq(tmp_path / "helix_flow_demo.xsq")
    result = rest_check.XlightsRestSequenceCheck(
        schema="helix.xlights_rest_sequence_check.v1",
        created_at="2026-06-28T00:00:00+00:00",
        xsq_path=str(xsq),
        status="checked",
        endpoint="http://127.0.0.1:49913",
        xlights_version="2024.9",
        check_response={"res": 200, "msg": "Sequence checked."},
        errors=(),
        rest_probes=(
            rest_check.XlightsRestEndpointProbe(
                host="127.0.0.1",
                port=49913,
                reachable=True,
                detail="xLights version 2024.9",
            ),
        ),
        visual_review_status="not_reviewed",
        controller_channel_safety="not_tested",
    )

    paths = rest_check.write_sequence_check(result, tmp_path / "report")

    payload = json.loads(paths["json"].read_text(encoding="utf-8"))
    assert payload["status"] == "checked"
    markdown = paths["markdown"].read_text(encoding="utf-8")
    assert "Controller/channel safety: `not_tested`" in markdown
    assert "does not complete manual visual review" in markdown


def test_missing_xsq_is_blocked_without_rest_probe(tmp_path: Path) -> None:
    result = rest_check.check_xlights_rest_sequence(tmp_path / "missing.xsq")

    assert result.status == "blocked"
    assert result.rest_probes == ()
    assert "does not exist" in result.errors[0]
