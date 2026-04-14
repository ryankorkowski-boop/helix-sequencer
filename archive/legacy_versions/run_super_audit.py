#!/usr/bin/env python3
from __future__ import annotations

import json
import py_compile
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

from v1 import _layout_entries_and_lookup, load_xsq
from xlights_model_parser import parse_layout


ROOT = Path(__file__).resolve().parent
ALLMODELS = ROOT / "allmodels"
LAYOUT_PATH = ALLMODELS / "xlights_rgbeffects.xml"
TEMPLATE_PATH = ALLMODELS / "template2.xsq"
AUDIT_DATE = date.today().isoformat()

CHECK_FILES = [
    ROOT / "variant_engine.py",
    ROOT / "xlights_model_parser.py",
    ROOT / "sequencer_launcher.py",
    ROOT / "build_allmodels_pack.py",
    ROOT / "generate_allmodels_variants.py",
    ROOT / "run_super_audit.py",
    ROOT / "v20.1.py",
    ROOT / "v20.2.py",
    ROOT / "v20.3.py",
    ROOT / "v21.1.py",
    ROOT / "v21.2.py",
    ROOT / "v21.3.py",
    ROOT / "v21.4.py",
    ROOT / "v21.5.py",
    ROOT / "v21.6.py",
    ROOT / "v22.1.py",
    ROOT / "v22.2.py",
    ROOT / "v22.3.py",
    ROOT / "v23.1.py",
    ROOT / "v23.2.py",
    ROOT / "v23.3.py",
    ROOT / "v23.4.py",
    ROOT / "v23.5.py",
    ROOT / "v23.6.py",
]


def _grade_rank(grade: str) -> int:
    order = {
        "A+": 12,
        "A": 11,
        "A-": 10,
        "B+": 9,
        "B": 8,
        "B-": 7,
        "C+": 6,
        "C": 5,
        "C-": 4,
        "D+": 3,
        "D": 2,
        "D-": 1,
        "F": 0,
    }
    return order.get((grade or "").strip().upper(), -1)


def _compile_checks() -> list[dict]:
    results: list[dict] = []
    for path in CHECK_FILES:
        item = {"file": str(path), "ok": False}
        try:
            py_compile.compile(str(path), doraise=True)
            item["ok"] = True
        except Exception as exc:  # pragma: no cover - defensive audit code
            item["error"] = repr(exc)
        results.append(item)
    return results


def _folder_sort_key(path: Path) -> tuple[int, ...]:
    nums = [int(part) for part in re.findall(r"\d+", path.name)]
    return tuple(nums + [0] * (4 - len(nums)))


def _latest_file(paths: list[Path]) -> Path | None:
    if not paths:
        return None
    return max(paths, key=lambda p: (p.stat().st_mtime, p.name.lower()))


def _discover_targets() -> list[tuple[str, Path, Path | None, Path | None, Path | None]]:
    root = ALLMODELS / "final"
    if not root.exists():
        return []
    folders = [
        path
        for path in root.iterdir()
        if path.is_dir() and re.match(r"^v(?:20|21|22|23)\.\d+$", path.name, re.IGNORECASE)
    ]
    folders.sort(key=_folder_sort_key)
    out: list[tuple[str, Path, Path | None, Path | None, Path | None]] = []
    for folder in folders:
        main_candidates = [
            path
            for path in folder.glob("*.xsq")
            if not path.name.endswith(".all_models_all_effects.xsq")
        ]
        main_path = _latest_file(main_candidates)
        report_path = None
        showcase_path = None
        if main_path is not None:
            expected_report = folder / f"{main_path.stem}.report.json"
            report_path = expected_report if expected_report.exists() else _latest_file(list(folder.glob("*.report.json")))
            expected_showcase = folder / f"{main_path.stem}.all_models_all_effects.xsq"
            showcase_path = expected_showcase if expected_showcase.exists() else _latest_file(list(folder.glob("*.all_models_all_effects.xsq")))
            if showcase_path is None:
                # Current builds save the all-models result directly as the primary XSQ.
                showcase_path = main_path
        out.append((folder.name, folder, main_path, report_path, showcase_path))
    return out


def _scan_target(
    layout_names: set[str],
    label: str,
    folder: Path,
    xsq_path: Path | None,
    report_path: Path | None,
    showcase_path: Path | None,
) -> dict:
    item = {
        "version": label,
        "folder": str(folder),
        "present": False,
    }
    if xsq_path is None or report_path is None or not xsq_path.exists() or not report_path.exists():
        missing: list[str] = []
        if xsq_path is None or not xsq_path.exists():
            missing.append(str(xsq_path or (folder / "<latest main xsq missing>")))
        if report_path is None or not report_path.exists():
            missing.append(str(report_path or (folder / "<latest report missing>")))
        item["missing_files"] = missing
        return item

    report = json.loads(report_path.read_text(encoding="utf-8"))
    xsq = load_xsq(xsq_path)
    xsq_names = set(xsq.elements.keys())
    placements = report.get("placements", {}) or {}
    effects_total = int(report.get("effects_total", 0) or 0)
    dominant_family, dominant_count = ("", 0)
    if placements:
        dominant_family, dominant_count = max(placements.items(), key=lambda kv: int(kv[1]))
    item.update(
        {
            "present": True,
            "title": report.get("title", ""),
            "main": str(xsq_path),
            "report": str(report_path),
            "showcase": str(showcase_path) if showcase_path and showcase_path.exists() else "",
            "effects_total": effects_total,
            "quality_score": float((report.get("quality", {}) or {}).get("score", 0.0) or 0.0),
            "quality_grade": (report.get("quality", {}) or {}).get("grade", ""),
            "keyboard_ratio": float((report.get("quality", {}) or {}).get("keyboard_ratio", 0.0) or 0.0),
            "validation_ratio": float((report.get("quality", {}) or {}).get("validation_ratio", 0.0) or 0.0),
            "coverage_ratio": float((report.get("quality", {}) or {}).get("coverage_ratio", 0.0) or 0.0),
            "detail_ratio": float((report.get("quality", {}) or {}).get("detail_ratio", 0.0) or 0.0),
            "layout_rows_missing_in_xsq": len(layout_names - xsq_names),
            "extra_xsq_rows_not_in_layout": len(xsq_names - layout_names),
            "dominant_family": dominant_family,
            "dominant_family_ratio": round((int(dominant_count) / max(1, effects_total)), 3),
            "top_families": sorted(placements.items(), key=lambda kv: int(kv[1]), reverse=True)[:8],
        }
    )
    if showcase_path and showcase_path.exists():
        showcase_xsq = load_xsq(showcase_path)
        showcase_names = set(showcase_xsq.elements.keys())
        item["showcase_present"] = True
        item["showcase_layout_rows_missing_in_xsq"] = len(layout_names - showcase_names)
        item["showcase_extra_xsq_rows_not_in_layout"] = len(showcase_names - layout_names)
    else:
        item["showcase_present"] = False
    return item


def _launcher_contains(text: str, version: str) -> bool:
    return f'VariantOption("{version}"' in text


def _exe_smoke_test() -> dict:
    candidates = [
        ROOT / "HelixSequenceWeaverBeta.exe",
        ROOT / "dist_v23" / "HelixSequenceWeaverBeta.exe",
        ROOT / "dist" / "HelixSequenceWeaverBeta.exe",
    ]
    existing = [path for path in candidates if path.exists()]
    exe_path = max(existing, key=lambda p: (p.stat().st_mtime, p.name.lower())) if existing else candidates[0]
    output_dir = ALLMODELS / "final" / "_exe_smoke_current"
    result = {
        "exe": str(exe_path),
        "output_dir": str(output_dir),
        "ok": False,
    }
    if not exe_path.exists():
        result["error"] = "dist exe missing"
        return result
    output_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        str(exe_path),
        "--run-variant",
        "v24.3",
        "--template",
        str(TEMPLATE_PATH),
        "--audio",
        str(ALLMODELS / "13.wav"),
        "--layout-file",
        str(LAYOUT_PATH),
        "--output-dir",
        str(output_dir),
        "--no-prompt",
        "--no-save-settings",
        "--no-workspace-history",
        "--layering-mode",
        "smart_layer",
        "--strict-xlights-effects",
        "--spatial-awareness",
        "0.52",
        "--chase-style",
        "wave",
        "--keyboard-mix",
        "0.12",
    ]
    try:
        completed = subprocess.run(
            cmd,
            cwd=ROOT,
            check=True,
            timeout=900,
            capture_output=True,
            text=True,
        )
        xsq_path = output_dir / "13,v23.6.xsq"
        report_path = output_dir / "13,v23.6.report.json"
        result["ok"] = xsq_path.exists() and report_path.exists()
        result["stdout_tail"] = "\n".join((completed.stdout or "").splitlines()[-20:])
        result["stderr_tail"] = "\n".join((completed.stderr or "").splitlines()[-20:])
        result["xsq"] = str(xsq_path)
        result["report"] = str(report_path)
    except Exception as exc:  # pragma: no cover - audit only
        result["error"] = repr(exc)
    return result


def _official_display_types() -> list[str]:
    defaults = [
        "Arches",
        "Candy Canes",
        "Channel Block",
        "Circle",
        "Cube",
        "Custom",
        "DmxMovingHead",
        "DmxMovingHeadAdv",
        "DmxFloodArea",
        "DmxFloodlight",
        "DmxGeneral",
        "DmxServo",
        "DmxServo3d",
        "DmxSkull",
        "Icicles",
        "Image",
        "Matrix",
        "ModelGroup",
        "MultiPoint",
        "Single Line",
        "Poly Line",
        "Sphere",
        "Spinner",
        "Star",
        "Tree",
        "Window Frame",
        "Wreath",
        "Gridlines",
        "Terrain",
        "Mesh",
        "Ruler",
    ]
    keys_path = ROOT / "xlights_src" / "xLights" / "XmlSerializer" / "XmlNodeKeys.h"
    if not keys_path.exists():
        return defaults
    wanted = {
        "ArchesType",
        "CandyCaneType",
        "ChannelBlockType",
        "CircleType",
        "CubeType",
        "CustomType",
        "DmxMovingHeadType",
        "DmxMovingHeadAdvType",
        "DmxFloodAreaType",
        "DmxFloodlightType",
        "DmxGeneralType",
        "DmxServoType",
        "DmxServo3dType",
        "DmxSkullType",
        "IciclesType",
        "ImageType",
        "MatrixType",
        "ModelGroupType",
        "MultiPointType",
        "SingleLineType",
        "PolyLineType",
        "SphereType",
        "SpinnerType",
        "StarType",
        "TreeType",
        "WindowType",
        "WreathType",
        "GridlinesType",
        "TerrainType",
        "MeshType",
        "RulerType",
    }
    pattern = re.compile(r'constexpr\s+auto\s+([A-Za-z0-9_]+)\s*=\s*"([^"]+)";')
    values: list[str] = []
    for line in keys_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        match = pattern.search(line)
        if not match:
            continue
        key = match.group(1).strip()
        value = match.group(2).strip()
        if key in wanted and value:
            values.append(value)
    if not values:
        return defaults
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def _edge_case_attrs(display_as: str, index: int) -> dict[str, str]:
    attrs = {
        "DisplayAs": display_as,
        "StartChannel": str(1 + (index * 64)),
        "WorldPosX": str((index % 10) * 36),
        "WorldPosY": str((index // 10) * 30),
        "WorldPosZ": "0",
        "X2": "24",
        "Y2": "0",
        "Z2": "0",
        "parm1": "4",
        "parm2": "12",
        "StringType": "RGB Nodes",
    }
    disp = (display_as or "").lower()
    if "single line" in disp or "poly line" in disp:
        attrs["StringType"] = "Single Color White"
        attrs["parm1"] = "1"
        attrs["parm2"] = "100"
    elif "candy cane" in disp:
        attrs["parm1"] = "6"
        attrs["parm2"] = "30"
    elif "icicle" in disp:
        attrs["parm1"] = "12"
        attrs["parm2"] = "20"
    elif "matrix" in disp or "image" in disp:
        attrs["parm1"] = "16"
        attrs["parm2"] = "32"
    elif "tree" in disp:
        attrs["parm1"] = "16"
        attrs["parm2"] = "50"
    elif "spinner" in disp:
        attrs["parm1"] = "8"
        attrs["parm2"] = "18"
    elif "sphere" in disp:
        attrs["parm1"] = "8"
        attrs["parm2"] = "16"
    elif "flood" in disp or "dmxgeneral" in disp:
        attrs["StringType"] = "Single Color White"
        attrs["NumChannels"] = "8"
        attrs["parm1"] = "8"
        attrs["parm2"] = "1"
    elif "dmx" in disp:
        attrs["StringType"] = "Single Color White"
        attrs["parm1"] = "6"
        attrs["parm2"] = "1"
    elif "modelgroup" in disp or "objectgroup" in disp or "submodel" in disp:
        attrs["StringType"] = "Single Color White"
        attrs["parm1"] = "1"
        attrs["parm2"] = "1"
    return attrs


def _run_edge_case_model_audit() -> dict:
    result = {
        "ok": False,
        "official_display_types_count": 0,
        "tested_display_types_count": 0,
        "failures": [],
    }
    try:
        from variant_engine import family_from_parsed_model
    except Exception as exc:  # pragma: no cover - environment-dependent
        result["error"] = f"variant_engine import failed: {exc!r}"
        return result

    official = _official_display_types()
    result["official_display_types_count"] = len(official)
    tested = official + [
        "Vert Matrix",
        "Horiz Matrix",
        "Tree 360",
        "Tree Flat",
        "Tree Ribbon",
        "Tree Angled",
        "DmxServo3Axis",
        "Terrian",
        "ObjectGroup",
        "SubModel",
        "MysteryLaserBar",
    ]
    result["tested_display_types_count"] = len(tested)
    view_like = {"Gridlines", "Terrain", "Terrian", "Mesh", "Ruler", "ModelGroup", "ObjectGroup", "SubModel"}

    root = ET.Element("xrgb")
    groups_el = ET.SubElement(root, "modelGroups")
    ET.SubElement(groups_el, "modelGroup", {"name": "ALL_AUDIT_MODELS", "models": ""})
    models_el = ET.SubElement(root, "models")
    for idx, display_as in enumerate(tested):
        safe = re.sub(r"[^A-Za-z0-9]+", "_", display_as).strip("_") or f"model_{idx:03d}"
        attrs = _edge_case_attrs(display_as, idx)
        attrs["name"] = f"AUDIT_{idx:03d}_{safe}"
        ET.SubElement(models_el, "model", attrs)

    with tempfile.TemporaryDirectory(prefix="dream_weaver_edge_audit_") as tmpdir:
        layout_path = Path(tmpdir) / "edge_case_models.xml"
        ET.ElementTree(root).write(layout_path, encoding="utf-8", xml_declaration=True)
        parsed = parse_layout(layout_path)

        by_display: dict[str, dict] = {}
        failures: list[dict] = []
        for model in parsed.models.values():
            if model.is_submodel:
                continue
            display = model.display_as or ""
            family = family_from_parsed_model(model)
            item = {
                "name": model.name,
                "display_as": display,
                "semantic_type": model.type,
                "family": family,
                "rgb_capable": bool(model.is_rgb_capable()),
                "total_pixels": int(model.total_pixels),
            }
            by_display[display] = item
            if display in view_like:
                if family:
                    failures.append({"display_as": display, "reason": "view/object/group should not map to effect family", "family": family})
            else:
                if not family:
                    failures.append({"display_as": display, "reason": "model display type did not map to any effect family", "semantic_type": model.type})

    result["sample_map"] = {key: by_display[key] for key in sorted(by_display.keys())}
    result["failures"] = failures
    result["ok"] = len(failures) == 0
    return result


def run() -> int:
    layout = parse_layout(LAYOUT_PATH)
    layout_rows = _layout_entries_and_lookup(LAYOUT_PATH)[0]
    layout_names = set(layout_rows)
    launcher_text = (ROOT / "sequencer_launcher.py").read_text(encoding="utf-8")

    compile_checks = _compile_checks()
    targets = [_scan_target(layout_names, *target) for target in _discover_targets()]
    present_targets = [item for item in targets if item.get("present")]
    best_overall = max(
        present_targets,
        key=lambda item: (
            float(item.get("quality_score", 0.0)),
            _grade_rank(str(item.get("quality_grade", ""))),
            -float(item.get("keyboard_ratio", 1.0)),
            -float(item.get("validation_ratio", 1.0)),
        ),
        default=None,
    )
    best_latest = max(
        [item for item in present_targets if str(item.get("version", "")).startswith("v23.")],
        key=lambda item: (
            float(item.get("quality_score", 0.0)),
            _grade_rank(str(item.get("quality_grade", ""))),
            -float(item.get("keyboard_ratio", 1.0)),
            -float(item.get("validation_ratio", 1.0)),
        ),
        default=None,
    )

    payload = {
        "audit_date": AUDIT_DATE,
        "layout": str(LAYOUT_PATH),
        "template": str(TEMPLATE_PATH),
        "root_models": len([model for model in layout.models.values() if not model.is_submodel]),
        "submodels": len([model for model in layout.models.values() if model.is_submodel]),
        "groups": len(layout.groups),
        "layout_sequence_rows": len(layout_rows),
        "compile_checks": compile_checks,
        "launcher_has_v22_1": _launcher_contains(launcher_text, "v22.1"),
        "launcher_has_v22_2": _launcher_contains(launcher_text, "v22.2"),
        "launcher_has_v22_3": _launcher_contains(launcher_text, "v22.3"),
        "launcher_has_v23_1": _launcher_contains(launcher_text, "v23.1"),
        "launcher_has_v23_2": _launcher_contains(launcher_text, "v23.2"),
        "launcher_has_v23_3": _launcher_contains(launcher_text, "v23.3"),
        "launcher_has_v23_4": _launcher_contains(launcher_text, "v23.4"),
        "launcher_has_v23_5": _launcher_contains(launcher_text, "v23.5"),
        "launcher_has_v23_6": _launcher_contains(launcher_text, "v23.6"),
        "edge_case_model_audit": _run_edge_case_model_audit(),
        "targets": targets,
        "best_overall": best_overall,
        "best_latest": best_latest,
        "exe_smoke": _exe_smoke_test(),
    }

    json_path = ALLMODELS / f"SUPER_AUDIT_{AUDIT_DATE}.json"
    txt_path = ALLMODELS / f"SUPER_AUDIT_{AUDIT_DATE}.txt"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines: list[str] = []
    lines.append("Dream Sequence Weaver Super Audit")
    lines.append("")
    lines.append(f"date={AUDIT_DATE}")
    lines.append(f"layout={LAYOUT_PATH}")
    lines.append(f"template={TEMPLATE_PATH}")
    lines.append(f"root_models={payload['root_models']}")
    lines.append(f"submodels={payload['submodels']}")
    lines.append(f"groups={payload['groups']}")
    lines.append(f"layout_sequence_rows={payload['layout_sequence_rows']}")
    lines.append("")
    lines.append("compile_checks=" + ", ".join(f"{Path(item['file']).name}:{'ok' if item['ok'] else 'fail'}" for item in compile_checks))
    lines.append(
        "launcher_v22="
        + ",".join(
            [
                f"v22.1:{int(bool(payload['launcher_has_v22_1']))}",
                f"v22.2:{int(bool(payload['launcher_has_v22_2']))}",
                f"v22.3:{int(bool(payload['launcher_has_v22_3']))}",
            ]
        )
    )
    lines.append(
        "launcher_v23="
        + ",".join(
            [
                f"v23.1:{int(bool(payload['launcher_has_v23_1']))}",
                f"v23.2:{int(bool(payload['launcher_has_v23_2']))}",
                f"v23.3:{int(bool(payload['launcher_has_v23_3']))}",
                f"v23.4:{int(bool(payload['launcher_has_v23_4']))}",
                f"v23.5:{int(bool(payload['launcher_has_v23_5']))}",
                f"v23.6:{int(bool(payload['launcher_has_v23_6']))}",
            ]
        )
    )
    lines.append("exe_smoke_ok=" + str(int(bool((payload.get("exe_smoke") or {}).get("ok")))))
    edge_case = payload.get("edge_case_model_audit") or {}
    lines.append("edge_case_model_audit_ok=" + str(int(bool(edge_case.get("ok")))))
    lines.append(
        "edge_case_model_audit_summary="
        f"official={edge_case.get('official_display_types_count', 0)} "
        f"tested={edge_case.get('tested_display_types_count', 0)} "
        f"failures={len(edge_case.get('failures', []))}"
    )
    if best_latest:
        lines.append(
            "best_latest="
            f"{best_latest['version']} {best_latest['quality_score']} {best_latest['quality_grade']} "
            f"keyboard={best_latest['keyboard_ratio']} validation={best_latest['validation_ratio']}"
        )
    if best_overall:
        lines.append(
            "best_overall="
            f"{best_overall['version']} {best_overall['quality_score']} {best_overall['quality_grade']} "
            f"keyboard={best_overall['keyboard_ratio']} validation={best_overall['validation_ratio']}"
        )
    lines.append("")
    for item in targets:
        lines.append(f"[{item['version']}]")
        if not item.get("present"):
            lines.append("present=0")
            lines.append("missing_files=" + ", ".join(item.get("missing_files", [])))
            lines.append("")
            continue
        lines.append("present=1")
        lines.append(f"title={item['title']}")
        lines.append(f"main={item['main']}")
        lines.append(f"showcase={item.get('showcase', '')}")
        lines.append(f"effects_total={item['effects_total']}")
        lines.append(f"quality={item['quality_score']} ({item['quality_grade']})")
        lines.append(f"keyboard_ratio={item['keyboard_ratio']}")
        lines.append(f"validation_ratio={item['validation_ratio']}")
        lines.append(f"coverage_ratio={item['coverage_ratio']}")
        lines.append(f"detail_ratio={item['detail_ratio']}")
        lines.append(f"layout_rows_missing_in_xsq={item['layout_rows_missing_in_xsq']}")
        lines.append(f"extra_xsq_rows_not_in_layout={item['extra_xsq_rows_not_in_layout']}")
        lines.append(f"showcase_present={int(bool(item.get('showcase_present')))}")
        if item.get("showcase_present"):
            lines.append(f"showcase_layout_rows_missing_in_xsq={item['showcase_layout_rows_missing_in_xsq']}")
            lines.append(f"showcase_extra_xsq_rows_not_in_layout={item['showcase_extra_xsq_rows_not_in_layout']}")
        lines.append(f"dominant_family={item['dominant_family']}")
        lines.append(f"dominant_family_ratio={item['dominant_family_ratio']}")
        lines.append("top_families=" + ", ".join(f"{name}:{count}" for name, count in item.get("top_families", [])))
        lines.append("")
    txt_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(txt_path)
    print(json_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
