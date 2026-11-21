"""Regression coverage for strict canonical layout-bench XSQ selection."""
from pathlib import Path

import pytest

from tools.layout_bench.render_comparisons import find_xsq


def _folder(tmp_path: Path) -> Path:
    folder = tmp_path / "ac16_lor"
    folder.mkdir()
    return folder


def test_exact_song_stem_not_prefix(tmp_path):
    folder = _folder(tmp_path)
    (folder / "Bells of Mathmas Remix,auto.xsq").write_text("other")
    expected = folder / "Bells of Mathmas,auto.xsq"
    expected.write_text("correct")
    assert find_xsq(tmp_path, "ac16_lor", "Bells of Mathmas") == expected


def test_glob_metacharacters_are_literal(tmp_path):
    folder = _folder(tmp_path)
    (folder / "Song A,auto.xsq").write_text("wrong")
    expected = folder / "Song [A],auto.xsq"
    expected.write_text("correct")
    assert find_xsq(tmp_path, "ac16_lor", "Song [A]") == expected


def test_ambiguous_canonical_sequences_fail_closed(tmp_path):
    folder = _folder(tmp_path)
    (folder / "Track,auto.xsq").write_text("one")
    (folder / "Track,alternate.xsq").write_text("two")
    with pytest.raises(ValueError, match="Ambiguous canonical XSQ"):
        find_xsq(tmp_path, "ac16_lor", "Track")


def test_orchestrated_sidecar_is_not_canonical(tmp_path):
    folder = _folder(tmp_path)
    (folder / "Track,orchestrated.xsq").write_text("sidecar")
    expected = folder / "Track,auto.xsq"
    expected.write_text("canonical")
    assert find_xsq(tmp_path, "ac16_lor", "Track") == expected


def test_missing_sequence_fails(tmp_path):
    _folder(tmp_path)
    with pytest.raises(FileNotFoundError, match="No canonical XSQ"):
        find_xsq(tmp_path, "ac16_lor", "Missing")


def test_stitch_rejects_incomplete_panel_count(tmp_path):
    from tools.layout_bench.render_comparisons import stitch_panels

    with pytest.raises(ValueError, match="9, 12 or 16"):
        stitch_panels([], tmp_path / "song.mp3", tmp_path / "out.mp4", "Title", "Description")


def test_stitch_rejects_missing_panel_before_encoding(tmp_path):
    from tools.layout_bench.render_comparisons import stitch_panels

    soundtrack = tmp_path / "song.mp3"
    soundtrack.write_bytes(b"placeholder")
    with pytest.raises(FileNotFoundError, match="Missing comparison panel"):
        stitch_panels([tmp_path / f"panel_{i}.mp4" for i in range(9)], soundtrack, tmp_path / "out.mp4", "Title", "Description")


def test_stitch_rejects_missing_soundtrack_before_encoding(tmp_path):
    from tools.layout_bench.render_comparisons import stitch_panels

    panels = [tmp_path / f"panel_{i}.mp4" for i in range(9)]
    for panel in panels:
        panel.write_bytes(b"placeholder")
    with pytest.raises(FileNotFoundError, match="Missing comparison soundtrack"):
        stitch_panels(panels, tmp_path / "missing.mp3", tmp_path / "out.mp4", "Title", "Description")


def test_failed_comparison_encode_preserves_previous_mp4(tmp_path, monkeypatch):
    import subprocess
    from tools.layout_bench import render_comparisons as comparisons

    panels = [tmp_path / f"panel_{i}.mp4" for i in range(9)]
    for panel in panels:
        panel.write_bytes(b"panel")
    soundtrack = tmp_path / "song.mp3"
    soundtrack.write_bytes(b"audio")
    destination = tmp_path / "approved.mp4"
    destination.write_bytes(b"previous valid video")

    def fail_encode(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], 1, stderr=b"simulated failure")

    monkeypatch.setattr(comparisons, "_ffmpeg", lambda: "ffmpeg")
    monkeypatch.setattr(comparisons.subprocess, "run", fail_encode)
    with pytest.raises(RuntimeError, match="Comparison encode"):
        comparisons.stitch_panels(panels, soundtrack, destination, "Title", "Description")

    assert destination.read_bytes() == b"previous valid video"
    assert not list(tmp_path.glob("*.banner.png"))
    assert not list(tmp_path.glob("tmp*/comparison.mp4"))


def test_legacy_variant_plan_can_select_one_song_without_entire_catalog(tmp_path):
    from tools.layout_bench.render_comparisons import variant_plan

    songs = {"north_pole_overdrive": {
        "path": tmp_path / "north_pole_overdrive.mp3",
        "stem": "north_pole_overdrive",
        "label": "North Pole Overdrive",
    }}
    plans = variant_plan(songs, {"V01-NPO-ALL16"})
    assert len(plans) == 1
    assert plans[0]["id"] == "V01-NPO-ALL16"
    assert len(plans[0]["layout_ids"]) == 16


def test_legacy_variant_specs_have_unique_ids_and_expected_panel_counts():
    from tools.layout_bench.render_comparisons import variant_specs

    specs = variant_specs()
    assert len({spec[0] for spec in specs}) == len(specs)
    assert all(len(spec[4]) in (12, 16) for spec in specs)


def test_successful_comparison_encode_atomically_replaces_previous_mp4(tmp_path, monkeypatch):
    import subprocess
    from tools.layout_bench import render_comparisons as comparisons

    panels = [tmp_path / f"panel_{i}.mp4" for i in range(9)]
    for panel in panels:
        panel.write_bytes(b"panel")
    soundtrack = tmp_path / "song.mp3"
    soundtrack.write_bytes(b"audio")
    destination = tmp_path / "review.mp4"
    destination.write_bytes(b"previous review")

    def successful_encode(cmd, **kwargs):
        assert cmd[cmd.index("-framerate") + 1] == "30"
        assert cmd[cmd.index("-movflags") + 1] == "+faststart"
        staged = Path(cmd[-1])
        assert staged != destination
        assert staged.parent != destination.parent
        assert Path(cmd[cmd.index("-loop") + 3]).is_file()
        staged.write_bytes(b"new verified render")
        return subprocess.CompletedProcess(cmd, 0, stderr=b"")

    monkeypatch.setattr(comparisons, "_ffmpeg", lambda: "ffmpeg")
    monkeypatch.setattr(comparisons.subprocess, "run", successful_encode)
    comparisons.stitch_panels(panels, soundtrack, destination, "Title", "Description")
    assert destination.read_bytes() == b"new verified render"
    assert not list(tmp_path.glob("*.banner.png"))


def test_zero_byte_comparison_encode_preserves_previous_mp4(tmp_path, monkeypatch):
    import subprocess
    from tools.layout_bench import render_comparisons as comparisons

    panels = [tmp_path / f"panel_{i}.mp4" for i in range(12)]
    for panel in panels:
        panel.write_bytes(b"panel")
    soundtrack = tmp_path / "song.mp3"
    soundtrack.write_bytes(b"audio")
    destination = tmp_path / "review.mp4"
    destination.write_bytes(b"previous review")

    def empty_encode(cmd, **kwargs):
        Path(cmd[-1]).write_bytes(b"")
        return subprocess.CompletedProcess(cmd, 0, stderr=b"")

    monkeypatch.setattr(comparisons, "_ffmpeg", lambda: "ffmpeg")
    monkeypatch.setattr(comparisons.subprocess, "run", empty_encode)
    with pytest.raises(RuntimeError, match="Comparison encode"):
        comparisons.stitch_panels(panels, soundtrack, destination, "Title", "Description")
    assert destination.read_bytes() == b"previous review"


def test_stitch_rejects_duplicate_panel_paths(tmp_path):
    from tools.layout_bench.render_comparisons import stitch_panels

    panel = tmp_path / "panel.mp4"
    panel.write_bytes(b"video")
    with pytest.raises(ValueError, match="duplicate panel"):
        stitch_panels([panel] * 9, tmp_path / "song.mp3", tmp_path / "out.mp4", "Title", "Description")


def test_stitch_rejects_empty_panel(tmp_path):
    from tools.layout_bench.render_comparisons import stitch_panels

    panels = [tmp_path / f"panel_{i}.mp4" for i in range(9)]
    for panel in panels:
        panel.write_bytes(b"video")
    panels[3].write_bytes(b"")
    with pytest.raises(ValueError, match="Empty comparison panel"):
        stitch_panels(panels, tmp_path / "song.mp3", tmp_path / "out.mp4", "Title", "Description")


def test_stitch_rejects_empty_soundtrack(tmp_path):
    from tools.layout_bench.render_comparisons import stitch_panels

    panels = [tmp_path / f"panel_{i}.mp4" for i in range(9)]
    for panel in panels:
        panel.write_bytes(b"video")
    soundtrack = tmp_path / "song.mp3"
    soundtrack.write_bytes(b"")
    with pytest.raises(ValueError, match="Empty comparison soundtrack"):
        stitch_panels(panels, soundtrack, tmp_path / "out.mp4", "Title", "Description")


def test_orchestrated_word_in_song_title_does_not_exclude_canonical_xsq(tmp_path):
    folder = _folder(tmp_path)
    expected = folder / "Orchestrated Christmas,auto.xsq"
    expected.write_text("canonical")
    (folder / "Orchestrated Christmas,orchestrated.xsq").write_text("sidecar")
    assert find_xsq(tmp_path, "ac16_lor", "Orchestrated Christmas") == expected


def test_orchestrated_sidecar_filter_is_case_insensitive(tmp_path):
    folder = _folder(tmp_path)
    expected = folder / "Track,auto.xsq"
    expected.write_text("canonical")
    (folder / "Track,ORCHESTRATED.xsq").write_text("sidecar")
    assert find_xsq(tmp_path, "ac16_lor", "Track") == expected


def test_native_panel_encode_rejects_zero_frames(tmp_path, monkeypatch):
    import numpy as np
    from types import SimpleNamespace
    from tools.layout_bench import render_comparisons as comparisons

    fseq = SimpleNamespace(
        fps=lambda: 30, step_ms=33, sparse_start=0, rows=lambda: iter(())
    )
    class FakePipe:
        def write(self, data):
            pass
        def close(self):
            pass
    class FakeProcess:
        stdin = FakePipe()
        stderr = SimpleNamespace(read=lambda: b"")
        def wait(self):
            return 0
    monkeypatch.setattr(comparisons, "load_fseq", lambda path: fseq)
    monkeypatch.setattr(comparisons, "model_channel_report", lambda *args: [])
    monkeypatch.setattr(comparisons, "build_node_drawlist", lambda *args: {})
    monkeypatch.setattr(comparisons, "_ffmpeg", lambda: "ffmpeg")
    monkeypatch.setattr(comparisons.subprocess, "Popen", lambda *args, **kwargs: FakeProcess())
    with pytest.raises(RuntimeError, match="no video frames"):
        comparisons._encode_panel(
            {"fseq": tmp_path / "empty.fseq", "layout": tmp_path / "layout.xml",
             "title": "Test panel", "channels": 3},
            tmp_path / "empty.mp4",
        )


def test_native_panel_encoder_reaps_process_on_frame_iterator_exception(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from tools.layout_bench import render_comparisons as comparisons

    def broken_rows():
        raise ValueError("malformed FSEQ frame")
        yield b""

    fseq = SimpleNamespace(
        fps=lambda: 30, step_ms=33, sparse_start=0, rows=broken_rows
    )
    events = []
    class FakePipe:
        def close(self):
            events.append("stdin_closed")
    class FakeProcess:
        stdin = FakePipe()
        stderr = SimpleNamespace(read=lambda: b"ffmpeg log")
        def wait(self):
            events.append("reaped")
            return 0

    monkeypatch.setattr(comparisons, "load_fseq", lambda path: fseq)
    monkeypatch.setattr(comparisons, "model_channel_report", lambda *args: [])
    monkeypatch.setattr(comparisons, "build_node_drawlist", lambda *args: {})
    monkeypatch.setattr(comparisons, "_ffmpeg", lambda: "ffmpeg")
    monkeypatch.setattr(comparisons.subprocess, "Popen", lambda *args, **kwargs: FakeProcess())
    with pytest.raises(RuntimeError, match="panel encode failed") as exc:
        comparisons._encode_panel(
            {"fseq": tmp_path / "bad.fseq", "layout": tmp_path / "layout.xml",
             "title": "Test panel", "channels": 3},
            tmp_path / "panel.mp4",
        )
    assert isinstance(exc.value.__cause__, ValueError)
    assert events == ["stdin_closed", "reaped"]


def test_comparison_layout_collector_rejects_repeated_layout_ids(tmp_path):
    from tools.layout_bench.render_comparisons import collect_required_layouts

    song = {"stem": "song", "path": tmp_path / "song.mp3"}
    with pytest.raises(ValueError, match="Repeated layout IDs"):
        collect_required_layouts([{"id": "duplicate", "song": song, "layout_ids": ["a"] * 9}])


def test_comparison_layout_collector_rejects_unsupported_panel_count(tmp_path):
    from tools.layout_bench.render_comparisons import collect_required_layouts

    song = {"stem": "song", "path": tmp_path / "song.mp3"}
    with pytest.raises(ValueError, match="Invalid comparison panel count"):
        collect_required_layouts([{"id": "short", "song": song, "layout_ids": ["a", "b"]}])


def test_comparison_layout_collector_deduplicates_shared_native_inputs(tmp_path):
    from tools.layout_bench.render_comparisons import collect_required_layouts

    song = {"stem": "song", "path": tmp_path / "song.mp3"}
    layouts = [f"layout_{i}" for i in range(9)]
    plans = [
        {"id": "one", "song": song, "layout_ids": layouts},
        {"id": "two", "song": song, "layout_ids": list(reversed(layouts))},
    ]
    required = collect_required_layouts(plans)
    assert [layout for layout, _media in required] == layouts
    assert all(media == song["path"] for _layout, media in required)


def test_comparison_collector_rejects_same_stem_different_audio_sources(tmp_path):
    from tools.layout_bench.render_comparisons import collect_required_layouts

    layouts = [f"layout_{i}" for i in range(9)]
    plans = [
        {"id": "one", "song": {"stem": "shared", "path": tmp_path / "a" / "shared.mp3"},
         "layout_ids": layouts},
        {"id": "two", "song": {"stem": "shared", "path": tmp_path / "b" / "shared.mp3"},
         "layout_ids": layouts},
    ]
    with pytest.raises(ValueError, match="Conflicting source audio"):
        collect_required_layouts(plans)
