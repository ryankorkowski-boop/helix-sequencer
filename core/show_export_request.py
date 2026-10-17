"""Validated GUI/export request contract; no fake LMS or implicit hardware probing."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

OUTPUT_FORMATS = ("xsq", "lms", "both")
LAYOUT_VARIANTS = ("custom", "small", "traditional", "mega_tree", "band", "advanced_3d", "ac16")
HARDWARE_MODES = ("auto", "ac16", "pixel", "mixed")


@dataclass(frozen=True)
class ShowExportRequest:
    output_format: str = "xsq"
    layout_variant: str = "custom"
    hardware_mode: str = "auto"
    layout_path: str | None = None

    def __post_init__(self):
        if self.output_format not in OUTPUT_FORMATS:
            raise ValueError(f"Unsupported output format: {self.output_format!r}")
        if self.layout_variant not in LAYOUT_VARIANTS:
            raise ValueError(f"Unsupported layout variant: {self.layout_variant!r}")
        if self.hardware_mode not in HARDWARE_MODES:
            raise ValueError(f"Unsupported hardware mode: {self.hardware_mode!r}")
        if self.layout_variant == "custom" and not self.layout_path:
            raise ValueError("Custom layout requires an imported xLights layout file")
        if self.layout_path and Path(self.layout_path).suffix.lower() != ".xml":
            raise ValueError("Imported xLights layout must be an XML file")

    @property
    def requested_formats(self) -> tuple[str, ...]:
        return ("xsq", "lms") if self.output_format == "both" else (self.output_format,)


def validate_exporters(request: ShowExportRequest, available: set[str] | frozenset[str]) -> None:
    """Fail before starting a potentially long song analysis if an exporter is absent."""
    missing = set(request.requested_formats) - set(available)
    if missing:
        raise NotImplementedError(
            "Requested sequence exporter(s) not available: " + ", ".join(sorted(missing))
        )


def export_selected(request: ShowExportRequest, exporters: dict, analysis, destination: Path):
    """Reuse the exact same analysis for selected formats; never silently skip one."""
    validate_exporters(request, set(exporters))
    destination = Path(destination)
    results = {}
    for fmt in request.requested_formats:
        path = destination / f"Performance.{fmt}"
        result = exporters[fmt](analysis, path, request)
        if not path.is_file() or path.stat().st_size == 0:
            raise RuntimeError(f"{fmt.upper()} exporter did not create a nonempty sequence: {path}")
        results[fmt] = path
    return results
