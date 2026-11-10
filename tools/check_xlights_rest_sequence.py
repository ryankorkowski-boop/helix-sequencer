from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence


DEFAULT_OUTPUT_DIR = Path("test_runs/xlights_rest_sequence_check")
DEFAULT_REST_HOST = "127.0.0.1"
DEFAULT_REST_PORTS = (49913, 49914)
CHECKED_STATUS = "checked"
FAILED_STATUS = "failed"
BLOCKED_STATUS = "blocked"


@dataclass(frozen=True)
class XlightsRestEndpointProbe:
    host: str
    port: int
    reachable: bool
    detail: str


@dataclass(frozen=True)
class XlightsRestSequenceCheck:
    schema: str
    created_at: str
    xsq_path: str
    status: str
    endpoint: str | None
    xlights_version: str | None
    check_response: dict[str, Any] | None
    errors: tuple[str, ...]
    rest_probes: tuple[XlightsRestEndpointProbe, ...]
    visual_review_status: str
    controller_channel_safety: str


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _base_url(host: str, port: int) -> str:
    return f"http://{host}:{int(port)}"


def _request_json(method: str, url: str, payload: dict[str, Any] | None = None, timeout: float = 3.0) -> dict[str, Any]:
    body = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url=url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read().decode("utf-8")
    if not raw.strip():
        return {}
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object from {url}")
    return value


def _response_ok(response: dict[str, Any]) -> bool:
    result = response.get("res")
    if result is None:
        return response.get("status") in {"ok", "OK", "success", "SUCCESS"}
    return result in {0, 200, "0", "200", "ok", "OK", "success", "SUCCESS"}


def _version_from_response(response: dict[str, Any]) -> str | None:
    for key in ("version", "Version", "xlights_version", "xLightsVersion"):
        value = response.get(key)
        if value is not None:
            return str(value)
    return None


def _check_sequence_payload(xsq_path: Path) -> dict[str, str]:
    return {"cmd": "checkSequence", "seq": str(xsq_path)}


def check_xlights_rest_sequence(
    xsq_path: Path,
    *,
    host: str = DEFAULT_REST_HOST,
    ports: Sequence[int] = DEFAULT_REST_PORTS,
    timeout: float = 3.0,
) -> XlightsRestSequenceCheck:
    resolved_xsq = xsq_path.resolve()
    probes: list[XlightsRestEndpointProbe] = []
    errors: list[str] = []

    if not resolved_xsq.exists():
        errors.append(f"XSQ file does not exist: {resolved_xsq}")
        return XlightsRestSequenceCheck(
            schema="helix.xlights_rest_sequence_check.v1",
            created_at=_utc_now(),
            xsq_path=str(resolved_xsq),
            status=BLOCKED_STATUS,
            endpoint=None,
            xlights_version=None,
            check_response=None,
            errors=tuple(errors),
            rest_probes=tuple(probes),
            visual_review_status="not_reviewed",
            controller_channel_safety="not_tested",
        )

    for port in ports:
        endpoint = _base_url(host, int(port))
        try:
            version_response = _request_json("GET", f"{endpoint}/getVersion", timeout=timeout)
        except (OSError, urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
            detail = str(exc) or exc.__class__.__name__
            probes.append(
                XlightsRestEndpointProbe(host=host, port=int(port), reachable=False, detail=detail)
            )
            errors.append(f"{endpoint}/getVersion unavailable: {detail}")
            continue

        version = _version_from_response(version_response)
        probes.append(
            XlightsRestEndpointProbe(
                host=host,
                port=int(port),
                reachable=True,
                detail=f"xLights version {version or 'not reported'}",
            )
        )
        try:
            check_response = _request_json(
                "POST",
                f"{endpoint}/xlDoAutomation",
                payload=_check_sequence_payload(resolved_xsq),
                timeout=timeout,
            )
        except (OSError, urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
            detail = str(exc) or exc.__class__.__name__
            errors.append(f"{endpoint}/xlDoAutomation checkSequence failed: {detail}")
            return XlightsRestSequenceCheck(
                schema="helix.xlights_rest_sequence_check.v1",
                created_at=_utc_now(),
                xsq_path=str(resolved_xsq),
                status=FAILED_STATUS,
                endpoint=endpoint,
                xlights_version=version,
                check_response=None,
                errors=tuple(errors),
                rest_probes=tuple(probes),
                visual_review_status="not_reviewed",
                controller_channel_safety="not_tested",
            )

        status = CHECKED_STATUS if _response_ok(check_response) else FAILED_STATUS
        if status == FAILED_STATUS:
            errors.append(f"{endpoint}/xlDoAutomation checkSequence returned a non-success result")
        return XlightsRestSequenceCheck(
            schema="helix.xlights_rest_sequence_check.v1",
            created_at=_utc_now(),
            xsq_path=str(resolved_xsq),
            status=status,
            endpoint=endpoint,
            xlights_version=version,
            check_response=check_response,
            errors=tuple(errors),
            rest_probes=tuple(probes),
            visual_review_status="not_reviewed",
            controller_channel_safety="not_tested",
        )

    return XlightsRestSequenceCheck(
        schema="helix.xlights_rest_sequence_check.v1",
        created_at=_utc_now(),
        xsq_path=str(resolved_xsq),
        status=BLOCKED_STATUS,
        endpoint=None,
        xlights_version=None,
        check_response=None,
        errors=tuple(errors),
        rest_probes=tuple(probes),
        visual_review_status="not_reviewed",
        controller_channel_safety="not_tested",
    )


def sequence_check_to_dict(result: XlightsRestSequenceCheck) -> dict[str, Any]:
    payload = asdict(result)
    payload["rest_probes"] = [asdict(probe) for probe in result.rest_probes]
    payload["errors"] = list(result.errors)
    return payload


def sequence_check_markdown(result: XlightsRestSequenceCheck) -> str:
    probes = "\n".join(
        f"- {probe.host}:{probe.port} - {'reachable' if probe.reachable else 'unavailable'} ({probe.detail})"
        for probe in result.rest_probes
    ) or "- Not probed"
    errors = "\n".join(f"- {error}" for error in result.errors) or "- None"
    response = (
        json.dumps(result.check_response, indent=2, sort_keys=True)
        if result.check_response is not None
        else "not recorded"
    )
    return (
        "# xLights REST Sequence Check\n\n"
        f"- Created: `{result.created_at}`\n"
        f"- XSQ: `{result.xsq_path}`\n"
        f"- Status: `{result.status}`\n"
        f"- Endpoint: `{result.endpoint or 'not connected'}`\n"
        f"- xLights version: `{result.xlights_version or 'not reported'}`\n"
        f"- Visual review: `{result.visual_review_status}`\n"
        f"- Controller/channel safety: `{result.controller_channel_safety}`\n\n"
        "## REST Probes\n\n"
        f"{probes}\n\n"
        "## checkSequence Response\n\n"
        "```json\n"
        f"{response}\n"
        "```\n\n"
        "## Errors\n\n"
        f"{errors}\n\n"
        "This report only records xLights REST `checkSequence` evidence. It does not complete manual visual review or controller/channel safety validation.\n"
    )


def write_sequence_check(result: XlightsRestSequenceCheck, output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "xlights_rest_sequence_check.json"
    md_path = output_dir / "xlights_rest_sequence_check.md"
    json_path.write_text(
        json.dumps(sequence_check_to_dict(result), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    md_path.write_text(sequence_check_markdown(result), encoding="utf-8")
    return {"json": json_path, "markdown": md_path}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run xLights REST checkSequence and record evidence.")
    parser.add_argument("--xsq", type=Path, required=True, help="Generated XSQ file to check.")
    parser.add_argument("--host", default=DEFAULT_REST_HOST)
    parser.add_argument("--ports", type=int, nargs="+", default=list(DEFAULT_REST_PORTS))
    parser.add_argument("--timeout", type=float, default=3.0)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = check_xlights_rest_sequence(
        args.xsq,
        host=args.host,
        ports=args.ports,
        timeout=args.timeout,
    )
    paths = write_sequence_check(result, args.output_dir)
    for kind, path in paths.items():
        print(f"{kind}: {path}")
    print(f"status: {result.status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
