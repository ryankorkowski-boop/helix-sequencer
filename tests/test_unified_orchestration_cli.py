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
    default, _, default_band = run("default", [])
    original, _, unsnapped_band = run("no_grid", ["--no-snap", *args])
    assert original == default
    assert unsnapped_band == default_band
    snapped, report, band = run("explicit_grid", args)
    assert report["beat_grid"]["scope"] == "generated_effect_starts"
    assert report["beat_grid"]["admitted_attempts"]["shifted"] > 0
    assert original != snapped and any((start - 17) % 125 == 0 for start in snapped)
    assert band == unsnapped_band
    assert report["orchestration"]["export_validation"]["passed"]


def test_serialized_performer_anchors_and_shared_manual_nodes(tmp_path, monkeypatch):
    from core import effect_engine
    from core.sequence_builder import run_profile

    audio = tmp_path / "test.wav"
    subprocess.run(
        [sys.executable, "-c",
         "import runpy, sys; from pathlib import Path; "
         "runpy.run_path(sys.argv[1])['generate_wav'](Path(sys.argv[2]), duration_seconds=3.0)",
         str(FIXTURE / "generate_synthetic_audio.py"), str(audio)],
        check=True,
    )
    layout = tmp_path / "layout.xml"
    layout.write_text("""<xrgb><models>
      <model name="Nova" DisplayAs="Custom" StringType="RGB Nodes" parm1="8">
        <faceInfo Name="Main" Type="NodeRange"/>
      </model>
      <model name="Kit" DisplayAs="Single Line" parm1="1" parm2="8">
        <Aliases><alias name="OldName:Snowman Drummer"/></Aliases>
        <subModel name="Pedal" line0="1-4">
          <aliases><alias name="OldName:HX_SNOWMAN_DRUMMER_KICK"/></aliases>
        </subModel>
      </model>
      <model name="Probe" DisplayAs="Single Line" parm1="1" parm2="8">
        <subModel name="Left" line0="1-4"/><subModel name="Right" line0="5-8"/>
      </model>
    </models><modelGroups>
      <modelGroup name="Inner Manual" models="Probe/Left"/>
      <modelGroup name="Outer Manual" models="Inner Manual">
        <Aliases><alias name="OldName:Manual Alias"/></Aliases>
      </modelGroup>
    </modelGroups></xrgb>""")
    fixture = ET.parse(FIXTURE / "minimal_template.xsq")
    root = fixture.getroot()
    root.tag = "xsequence"
    rows = ET.SubElement(root, "ElementEffects")
    manual = ET.SubElement(rows, "Element", name="Manual Alias", type="model")
    layer = ET.SubElement(manual, "EffectLayer", name="Hand authored")
    ET.SubElement(layer, "Effect", name="On", startTime="61", endTime="321", palette="0")
    template = tmp_path / "template.xsq"
    fixture.write(template, encoding="utf-8", xml_declaration=True)

    monkeypatch.setattr(effect_engine.snowman_band_engine, "build_snowman_band_plan", lambda **_: {
        "cues": {"drummer": [{
            "kind": "kick", "start_ms": 139, "end_ms": 250,
            "composite_submodels": ["HX_SNOWMAN_DRUMMER_KICK"],
        }]},
        "xlights_translation": {"sequence_effect_instructions": [{
            "target_model": "Nova", "effect": "Faces", "start_ms": 113, "end_ms": 238,
            "phoneme": "MBP", "face_definition": "Main", "label": "renamed vocal lead",
        }]},
    })

    def propose(**kwargs):
        for name in ("Probe/Left", "Probe/Right"):
            kwargs["add_model"](name, 155, 227, "pixel_test")
        return 2

    monkeypatch.setattr(effect_engine, "place_pixel_reactive_score", propose)
    monkeypatch.chdir(ROOT)
    profile_defaults = {
        name: getattr(effect_engine.base, name) for name in ("DENSITY", "SPEED", "RANDOMNESS")
    }

    def run(label, *, drummer=True):
        for name, value in profile_defaults.items():
            monkeypatch.setattr(effect_engine.base, name, value)
        output = tmp_path / label
        run_profile("master", [
            "--template", str(template), "--layout-file", str(layout), "--audio", str(audio),
            "--output-dir", str(output), "--variants", "1", "--single", "--no-prompt", "--no-save-settings",
            "--no-workspace-history", "--no-learning-memory", "--no-matrix-intelligence", "--no-effects-orchestrator",
            "--layering-mode", "smart_layer", "--polish",
            "--snap-grid", "16", "--snap-bpm", "120", "--snap-offset-ms", "17", "--snap-mode", "strict",
            *(["--orchestrate-band-performers"] if drummer else []),
        ])
        xsq_path = next(output.glob("*,*.xsq"))
        return xsq_path, json.loads(next(output.glob("*,*.report.json")).read_text())

    xsq_path, report = run("out")
    xsq = ET.parse(xsq_path)
    models = {row.get("name"): row for row in xsq.findall("./ElementEffects/Element")}

    def generated(name):
        return [
            effect for layer in models[name].findall("EffectLayer")
            if layer.get("name", "").startswith("AUTO_DreamSequenceWeaver_")
            for effect in layer.findall("Effect")
        ]

    assert any(effect.get("startTime") == "113" and effect.get("name") == "Faces"
               and "Faces_Phoneme=MBP" in effect.get("settings", "") for effect in generated("Nova"))
    assert any(effect.get("startTime") == "139" for effect in generated("Kit/Pedal"))
    assert any(effect.get("startTime") == "142" for effect in generated("Probe/Right"))
    assert all(int(effect.get("endTime")) <= 61 or int(effect.get("startTime")) >= 321
               for effect in generated("Probe/Left"))
    authored = models["Outer Manual"].find("./EffectLayer[@name='Hand authored']/Effect")
    assert (authored.get("startTime"), authored.get("endTime")) == ("61", "321")
    assert report["orchestration"]["contributions"]["drummer"]["retained"] == 1
    assert report["orchestration"]["export_validation"]["passed"]


    # Reverse the exact same proposals just before the governor ranks them.
    from core.orchestration_balance import PlacementSession

    drain = PlacementSession.place_accents

    def reverse(self):
        self._accents.reverse()
        drain(self)

    monkeypatch.setattr(PlacementSession, "place_accents", reverse)
    reversed_xsq, reversed_report = run("reversed")
    assert reversed_xsq.read_bytes() == xsq_path.read_bytes()
    assert reversed_report["orchestration"]["contributions"] == report["orchestration"]["contributions"]
    _, default_report = run("kit-disabled", drummer=False)
    assert "drummer" not in default_report["orchestration"]["contributions"]
