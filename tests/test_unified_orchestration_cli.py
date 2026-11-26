from pathlib import Path
import json
import subprocess
import sys
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "beta_demo"


def test_cli_live_orchestration_is_deterministic_and_can_be_disabled(tmp_path):
    audio = tmp_path / "test.wav"
    subprocess.run(
        [sys.executable, str(FIXTURE / "generate_synthetic_audio.py"), str(audio)],
        check=True,
    )
    fixture = ET.parse(FIXTURE / "minimal_template.xsq")
    fixture.getroot().tag = "xsequence"
    template = tmp_path / "template.xsq"
    fixture.write(template, encoding="utf-8", xml_declaration=True)
    saved = []
    for label, extra in (
        ("first", ()),
        ("repeat", ()),
        ("disabled", ("--no-unified-orchestration",)),
    ):
        output = tmp_path / label
        command = [
            sys.executable, str(ROOT / "main.py"), "--", "--template", str(template),
            "--layout-file", str(FIXTURE / "minimal_layout.xml"), "--output-dir", str(output),
            "--audio", str(audio), "--variants", "1", "--single", "--no-prompt", "--no-save-settings",
            "--no-workspace-history", "--no-learning-memory", "--no-matrix-intelligence",
            "--no-effects-orchestrator", *extra,
        ]
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=True, timeout=240)
        xsq = next(output.glob("*,*.xsq"), None)
        assert xsq is not None, result.stdout + result.stderr
        report = json.loads(next(output.glob("*,*.report.json")).read_text(encoding="utf-8"))
        manifest = next(output.glob("beta/*/run_manifest.json"))
        artifacts = json.loads(manifest.read_text(encoding="utf-8"))["artifacts"]
        assert any(item["kind"] == "xsq" and Path(item["path"]) == xsq for item in artifacts)
        if label == "disabled":
            assert "orchestration" not in report
        else:
            orchestration = report["orchestration"]
            assert orchestration["export_validation"]["passed"], orchestration["export_validation"]
            assert orchestration["export_validation"]["effects_checked"] == report["effects_total"] > 0
            assert orchestration["fallbacks"]["yard_keyboard"]
            assert any(pass_["name"] == "intent_render_validation" for pass_ in orchestration["planning_passes"])
            saved.append(xsq.read_bytes())
    assert saved[0] == saved[1]


def test_explicit_grid_changes_serialized_xsq_not_analysis_sidecars(tmp_path):
    audio = tmp_path / "test.wav"
    subprocess.run(
        [sys.executable, "-c",
         "import runpy, sys; from pathlib import Path; "
         "runpy.run_path(sys.argv[1])['generate_wav'](Path(sys.argv[2]), duration_seconds=3.0)",
         str(FIXTURE / "generate_synthetic_audio.py"), str(audio)],
        check=True,
    )
    fixture = ET.parse(FIXTURE / "minimal_template.xsq")
    fixture.getroot().tag = "xsequence"
    template = tmp_path / "template.xsq"
    fixture.write(template, encoding="utf-8", xml_declaration=True)

    def run(label, extra):
        output = tmp_path / label
        subprocess.run(
            [sys.executable, str(ROOT / "main.py"), "--", "--template", str(template),
             "--layout-file", str(FIXTURE / "minimal_layout.xml"), "--output-dir", str(output),
             "--audio", str(audio), "--variants", "1", "--single", "--no-prompt", "--no-save-settings",
             "--no-workspace-history", "--no-learning-memory", "--no-matrix-intelligence",
             "--no-effects-orchestrator", *extra],
            cwd=ROOT, capture_output=True, text=True, check=True, timeout=240,
        )
        xsq = next(output.glob("*,*.xsq"))
        report = json.loads(next(output.glob("*,*.report.json")).read_text(encoding="utf-8"))
        band = json.loads(next(output.glob("*,*.snowman_band.json")).read_text(encoding="utf-8"))
        starts = [
            int(effect.attrib["startTime"])
            for layer in ET.parse(xsq).findall("./ElementEffects/Element/EffectLayer")
            if layer.get("name", "").startswith("AUTO_DreamSequenceWeaver_")
            for effect in layer.findall("Effect")
        ]
        return starts, report, band

    args = ["--snap-grid", "16", "--snap-bpm", "120", "--snap-offset-ms", "17", "--snap-mode", "strict"]
    original, _, _ = run("no_grid", ["--no-snap", *args])
    snapped, report, band = run("explicit_grid", args)
    assert report["beat_grid"]["scope"] == "generated_effect_starts"
    assert report["beat_grid"]["admitted_attempts"]["shifted"] > 0
    assert original != snapped and any((start - 17) % 125 == 0 for start in snapped)
    assert not band.get("beat_grid", {}).get("snapped")
    assert report["orchestration"]["export_validation"]["passed"]
