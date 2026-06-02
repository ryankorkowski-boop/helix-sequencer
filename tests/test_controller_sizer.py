from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

from core.controller_sizer import analyze_layout_channel_usage, patch_layout_controller_capacity


def _write_layout(path: Path, models_xml: str, controller_channels: int = 10) -> Path:
    path.write_text(
        f"""<?xml version="1.0" encoding="UTF-8"?>
<xrgb>
  <controllers>
    <controller name="Main" Channels="{controller_channels}" />
  </controllers>
  <models>
    {models_xml}
  </models>
</xrgb>
""",
        encoding="utf-8",
    )
    return path


def test_rgb_model_uses_three_channels_per_pixel(tmp_path: Path) -> None:
    layout = _write_layout(
        tmp_path / "layout.xml",
        '<model name="Mega Tree" DisplayAs="Tree 360" StartChannel="1" NumStrings="10" NodesPerString="10" StringType="RGB Nodes" />',
    )

    report = analyze_layout_channel_usage(layout, padding_channels=50)

    assert report.required_channels == 300
    assert report.recommended_channels == 350
    assert report.models_with_channels == 1
    assert report.usages[0].channel_count == 300
    assert report.usages[0].rgb is True


def test_single_color_channel_block_uses_one_channel_per_pixel(tmp_path: Path) -> None:
    layout = _write_layout(
        tmp_path / "layout.xml",
        '<model name="AC Block" DisplayAs="Channel Block" StartChannel="1" NumChannels="16" StringType="Single Color" />',
    )

    report = analyze_layout_channel_usage(layout, padding_channels=50)

    assert report.required_channels == 16
    assert report.recommended_channels == 66
    assert report.usages[0].channel_count == 16
    assert report.usages[0].rgb is False


def test_multiple_models_use_highest_end_channel(tmp_path: Path) -> None:
    layout = _write_layout(
        tmp_path / "layout.xml",
        """
        <model name="A" DisplayAs="Tree 360" StartChannel="1" NumStrings="10" NodesPerString="10" StringType="RGB Nodes" />
        <model name="B" DisplayAs="Tree 360" StartChannel="500" NumStrings="5" NodesPerString="10" StringType="RGB Nodes" />
        """,
    )

    report = analyze_layout_channel_usage(layout, padding_channels=0)

    assert report.required_channels == 649
    assert report.recommended_channels == 649


def test_missing_start_channel_warns_and_does_not_crash(tmp_path: Path) -> None:
    layout = _write_layout(
        tmp_path / "layout.xml",
        '<model name="No Start" DisplayAs="Tree 360" NumStrings="10" NodesPerString="10" StringType="RGB Nodes" />',
    )

    report = analyze_layout_channel_usage(layout)

    assert report.required_channels == 0
    assert report.models_with_channels == 0
    assert any("No Start" in warning for warning in report.warnings)


def test_submodels_do_not_inflate_controller_requirement(tmp_path: Path) -> None:
    layout = _write_layout(
        tmp_path / "layout.xml",
        """
        <model name="Face" DisplayAs="Tree 360" StartChannel="1" NumStrings="1" NodesPerString="10" StringType="RGB Nodes">
          <subModel name="Mouth" line0="1-10" />
        </model>
        """,
    )

    report = analyze_layout_channel_usage(layout, padding_channels=0)

    assert report.model_count == 1
    assert report.models_with_channels == 1
    assert report.required_channels == 30


def test_patch_increases_low_controller_count(tmp_path: Path) -> None:
    layout = _write_layout(
        tmp_path / "layout.xml",
        '<model name="Mega Tree" DisplayAs="Tree 360" StartChannel="1" NumStrings="10" NodesPerString="10" StringType="RGB Nodes" />',
        controller_channels=10,
    )
    output = tmp_path / "patched.xml"

    report = patch_layout_controller_capacity(layout, output_path=output, padding_channels=50)

    assert report.xml_patched is True
    assert report.required_channels == 300
    assert report.recommended_channels == 350
    tree = ET.parse(output)
    controller = tree.getroot().find(".//controller")
    assert controller is not None
    assert controller.get("Channels") == "350"
    assert Path(str(output) + ".controller_sizing_report.json").exists()


def test_patch_never_decreases_high_controller_count(tmp_path: Path) -> None:
    layout = _write_layout(
        tmp_path / "layout.xml",
        '<model name="Mega Tree" DisplayAs="Tree 360" StartChannel="1" NumStrings="10" NodesPerString="10" StringType="RGB Nodes" />',
        controller_channels=999,
    )
    output = tmp_path / "patched.xml"

    report = patch_layout_controller_capacity(layout, output_path=output, padding_channels=50)

    assert report.xml_patched is False
    tree = ET.parse(output)
    controller = tree.getroot().find(".//controller")
    assert controller is not None
    assert controller.get("Channels") == "999"


def test_dry_run_does_not_write_output(tmp_path: Path) -> None:
    layout = _write_layout(
        tmp_path / "layout.xml",
        '<model name="Mega Tree" DisplayAs="Tree 360" StartChannel="1" NumStrings="10" NodesPerString="10" StringType="RGB Nodes" />',
        controller_channels=10,
    )
    output = tmp_path / "patched.xml"

    report = patch_layout_controller_capacity(layout, output_path=output, padding_channels=50, dry_run=True)

    assert report.required_channels == 300
    assert report.recommended_channels == 350
    assert report.xml_patched is False
    assert not output.exists()
