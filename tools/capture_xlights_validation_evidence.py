from __future__ import annotations

import argparse
import json
import socket
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence


STATUS_VALUES = {
    "xsq_import_status": {"imported", "failed", "blocked", "not_tested"},
    "preview_render_status": {"rendered", "failed", "blocked", "not_tested"},
    "visual_review_status": {"passed", "failed", "blocked", "not_reviewed"},
    "controller_status": {"passed", "failed", "blocked", "not_tested"},
}
DEFAULT_OUTPUT_DIR = Path("test_runs/xlights_validation_evidence")
DEFAULT_REST_PORTS = (49913, 49914)


@dataclass(frozen=True)
class RestProbe:
    host: str
    port: int
    reachable: bool
    detail: str


@dataclass(frozen=True)
class XlightsValidationEvidence:
    schema: str
    created_at: str
    artifact_run_url: str
    artifact_name: str
    artifact_digest: str | None
    xsq_filename: str
    mp4_filename: str
    xlights_version: str | None
    xsq_import_status: str
    preview_render_status: str
    visual_review_status: str
    controller_status: str
    reviewer: str | None
    notes: str
    rest_probes: tuple[RestProbe, ...]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _validate_status(field: str, value: str) -> None:
    allowed = STATUS_VALUES[field]
    if value not in allowed:
        choices = ", ".join(sorted(allowed))
        raise ValueError(f"{field} must be one of: {choices}")


def probe_xlights_rest(host: str = "127.0.0.1", ports: Sequence[int] = DEFAULT_REST_PORTS) -> tuple[RestProbe, ...]:
    probes: list[RestProbe] = []
    for port in ports:
        try:
            with socket.create_connection((host, int(port)), timeout=1.0):
                probes.append(RestProbe(host=host, port=int(port), reachable=True, detail="tcp connection opened"))
        except OSError as exc:
            probes.append(RestProbe(host=host, port=int(port), reachable=False, detail=str(exc)))
    return tuple(probes)


def build_evidence(
    *,
    artifact_run_url: str,
    artifact_name: str,
    artifact_digest: str | None,
    xsq_filename: str,
    mp4_filename: str,
    xlights_version: str | None,
    xsq_import_status: str,
    preview_render_status: str,
    visual_review_status: str,
    controller_status: str,
    reviewer: str | None,
    notes: str,
    rest_probes: Sequence[RestProbe] = (),
) -> XlightsValidationEvidence:
    for field, value in (
        ("xsq_import_status", xsq_import_status),
        ("preview_render_status", preview_render_status),
        ("visual_review_status", visual_review_status),
        ("controller_status", controller_status),
    ):
        _validate_status(field, value)
    return XlightsValidationEvidence(
        schema="helix.xlights_validation_evidence.v1",
        created_at=_utc_now(),
        artifact_run_url=artifact_run_url,
        artifact_name=artifact_name,
        artifact_digest=artifact_digest,
        xsq_filename=xsq_filename,
        mp4_filename=mp4_filename,
        xlights_version=xlights_version,
        xsq_import_status=xsq_import_status,
        preview_render_status=preview_render_status,
        visual_review_status=visual_review_status,
        controller_status=controller_status,
        reviewer=reviewer,
        notes=notes,
        rest_probes=tuple(rest_probes),
    )


def evidence_to_dict(evidence: XlightsValidationEvidence) -> dict[str, object]:
    payload = asdict(evidence)
    payload["rest_probes"] = [asdict(probe) for probe in evidence.rest_probes]
    return payload


def evidence_markdown(evidence: XlightsValidationEvidence) -> str:
    probes = "\n".join(
        f"- {probe.host}:{probe.port} - {'reachable' if probe.reachable else 'unavailable'} ({probe.detail})"
        for probe in evidence.rest_probes
    ) or "- Not probed"
    digest = evidence.artifact_digest or "not recorded"
    version = evidence.xlights_version or "not recorded"
    reviewer = evidence.reviewer or "not recorded"
    return (
        "# xLights Validation Evidence\n\n"
        f"- Created: `{evidence.created_at}`\n"
        f"- Artifact run: {evidence.artifact_run_url}\n"
        f"- Artifact bundle: `{evidence.artifact_name}`\n"
        f"- Artifact digest: `{digest}`\n"
        f"- XSQ: `{evidence.xsq_filename}`\n"
        f"- MP4: `{evidence.mp4_filename}`\n"
        f"- xLights version: `{version}`\n"
        f"- Reviewer: `{reviewer}`\n\n"
        "## Status\n\n"
        f"- XSQ import: `{evidence.xsq_import_status}`\n"
        f"- Preview render: `{evidence.preview_render_status}`\n"
        f"- Visual review: `{evidence.visual_review_status}`\n"
        f"- Controller/channel safety: `{evidence.controller_status}`\n\n"
        "## xLights REST Probe\n\n"
        f"{probes}\n\n"
        "## Notes\n\n"
        f"{evidence.notes.strip() or 'No notes recorded.'}\n"
    )


def write_evidence(evidence: XlightsValidationEvidence, output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "xlights_validation_evidence.json"
    md_path = output_dir / "xlights_validation_evidence.md"
    json_path.write_text(json.dumps(evidence_to_dict(evidence), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(evidence_markdown(evidence), encoding="utf-8")
    return {"json": json_path, "markdown": md_path}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Record xLights import/manual/controller validation evidence.")
    parser.add_argument("--artifact-run-url", required=True)
    parser.add_argument("--artifact-name", default="helix-flow-review-artifacts")
    parser.add_argument("--artifact-digest", default=None)
    parser.add_argument("--xsq-filename", default="helix_flow_demo.xsq")
    parser.add_argument("--mp4-filename", default="helix_flow_demo.mp4")
    parser.add_argument("--xlights-version", default=None)
    parser.add_argument("--xsq-import-status", choices=sorted(STATUS_VALUES["xsq_import_status"]), default="not_tested")
    parser.add_argument("--preview-render-status", choices=sorted(STATUS_VALUES["preview_render_status"]), default="not_tested")
    parser.add_argument("--visual-review-status", choices=sorted(STATUS_VALUES["visual_review_status"]), default="not_reviewed")
    parser.add_argument("--controller-status", choices=sorted(STATUS_VALUES["controller_status"]), default="not_tested")
    parser.add_argument("--reviewer", default=None)
    parser.add_argument("--notes", default="")
    parser.add_argument("--probe-rest", action="store_true", help="Probe local xLights/xFade REST automation ports.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    probes = probe_xlights_rest() if args.probe_rest else ()
    evidence = build_evidence(
        artifact_run_url=args.artifact_run_url,
        artifact_name=args.artifact_name,
        artifact_digest=args.artifact_digest,
        xsq_filename=args.xsq_filename,
        mp4_filename=args.mp4_filename,
        xlights_version=args.xlights_version,
        xsq_import_status=args.xsq_import_status,
        preview_render_status=args.preview_render_status,
        visual_review_status=args.visual_review_status,
        controller_status=args.controller_status,
        reviewer=args.reviewer,
        notes=args.notes,
        rest_probes=probes,
    )
    paths = write_evidence(evidence, args.output_dir)
    for kind, path in paths.items():
        print(f"{kind}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
