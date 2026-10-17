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
    with pytest.raises(RuntimeError, match="nonempty"):
        export_selected(request(), {"xsq": export}, object(), tmp_path)
