from core.ac_drummer_wiring_patch import ac_drummer_patch, write_ac_drummer_patch


def test_patch_has_ten_distinct_outputs():
    rows = ac_drummer_patch(33)
    assert len(rows) == 10
    assert [r["ac_channel"] for r in rows] == list(range(33, 43))
    assert [r["controller_output"] for r in rows] == list(range(1, 11))
    assert rows[0]["base_dim"] is True
    assert rows[4]["circuit"] == "SNARE_LEFT"
    assert rows[5]["circuit"] == "SNARE_RIGHT"


def test_patch_csv(tmp_path):
    path = write_ac_drummer_patch(tmp_path / "drummer.csv")
    text = path.read_text(encoding="utf-8")
    assert "CYMBAL_LEFT" in text
    assert "CYMBAL_RIGHT" in text
    assert "SNARE_LEFT" in text
    assert "SNARE_RIGHT" in text
