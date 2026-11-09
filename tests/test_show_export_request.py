from pathlib import Path
from types import SimpleNamespace
import pytest
from core.show_export_request import ShowExportRequest, validate_exporters, export_selected


def request(**overrides):
    return ShowExportRequest(**({"layout_variant": "band"} | overrides))


def test_three_output_choices():
    assert request(output_format="xsq").requested_formats == ("xsq",)
    assert request(output_format="lms").requested_formats == ("lms",)
    assert request(output_format="both").requested_formats == ("xsq", "lms")


@pytest.mark.parametrize("kwargs", [
    {"output_format": "fseq"}, {"layout_variant": "unknown"},
    {"hardware_mode": "guess"}, {"layout_variant": "custom"},
    {"layout_variant": "custom", "layout_path": "my_layout.txt"},
])
def test_invalid_requests_rejected(kwargs):
    with pytest.raises(ValueError):
        request(**kwargs)


def test_lms_request_cannot_silently_fall_back_to_xsq():
    with pytest.raises(NotImplementedError, match="lms"):
        validate_exporters(request(output_format="both"), {"xsq"})


def test_both_formats_share_analysis_and_produce_real_files(tmp_path):
    analysis = object()
    calls = []
    def make(fmt):
        def export(a, path, req):
            assert a is analysis
            calls.append(fmt)
            path.write_text(fmt)
        return export
    result = export_selected(request(output_format="both"),
                             {"xsq": make("xsq"), "lms": make("lms")},
                             analysis, tmp_path)
    assert calls == ["xsq", "lms"]
    assert set(result) == {"xsq", "lms"}
    assert all(path.stat().st_size for path in result.values())


def test_empty_export_is_an_error(tmp_path):
    def export(a, path, req):
        path.touch()
    with pytest.raises(RuntimeError, match="produced no sequence"):
        export_selected(request(), {"xsq": export}, object(), tmp_path)


def test_export_refuses_to_overwrite_previous_sequence(tmp_path):
    existing = tmp_path / "Performance.xsq"
    existing.write_text("approved version")
    with pytest.raises(FileExistsError):
        export_selected(request(), {"xsq": lambda a,p,r: p.write_text("replacement")},
                        object(), tmp_path)
    assert existing.read_text() == "approved version"


def test_both_formats_roll_back_if_lms_export_raises(tmp_path):
    def xsq(a, path, req):
        path.write_text("valid xsq")
    def lms(a, path, req):
        path.write_text("partial lms")
        raise RuntimeError("LMS conversion failed")
    with pytest.raises(RuntimeError, match="LMS conversion failed"):
        export_selected(request(output_format="both"),
                        {"xsq": xsq, "lms": lms}, object(), tmp_path)
    assert not (tmp_path / "Performance.xsq").exists()
    assert not (tmp_path / "Performance.lms").exists()


def test_both_formats_roll_back_if_second_export_empty(tmp_path):
    def xsq(a, path, req):
        path.write_text("valid xsq")
    def empty(a, path, req):
        path.touch()
    with pytest.raises(RuntimeError, match="LMS exporter produced no sequence"):
        export_selected(request(output_format="both"),
                        {"xsq": xsq, "lms": empty}, object(), tmp_path)
    assert not (tmp_path / "Performance.xsq").exists()
    assert not (tmp_path / "Performance.lms").exists()
