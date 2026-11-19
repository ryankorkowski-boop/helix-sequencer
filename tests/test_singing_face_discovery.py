from core.singing_face_discovery import detect_singing_faces, singing_face_summary


def test_detect_faces_without_name_guessing(tmp_path):
    layout = tmp_path / "xlights_rgbeffects.xml"
    layout.write_text(
        '<xrgb><models><model name="Ordinary Tree"><faceInfo Name="Singing" Type="NodeRange" '
        'Mouth-AI="1-5" Mouth-MBP="6-8"/></model>'
        '<model name="Snowman"/></models></xrgb>', encoding="utf-8"
    )
    faces = detect_singing_faces(layout)
    assert len(faces) == 1
    assert faces[0].model == "Ordinary Tree"
    assert faces[0].mappings["Mouth-AI"] == "1-5"
    assert singing_face_summary(layout)["singing_model_count"] == 1


def test_adjacent_xmodel_and_empty_definitions(tmp_path):
    layout = tmp_path / "xlights_rgbeffects.xml"
    layout.write_text('<xrgb><models><model name="No Face"><faceInfo Name="Empty"/></model><model name="Pixel Singer"/></models></xrgb>')
    (tmp_path / "singer.xmodel").write_text(
        '<custommodel name="Pixel Singer"><faceInfo Name="Default" Type="NodeRange" Mouth-O="1,2"/></custommodel>'
    )
    assert [face.model for face in detect_singing_faces(layout)] == ["Pixel Singer"]
    assert detect_singing_faces(layout, include_external=False) == []

def test_unrelated_xmodel_is_not_detected(tmp_path):
    layout = tmp_path / "xlights_rgbeffects.xml"
    layout.write_text('<xrgb><models><model name="House"/></models></xrgb>')
    (tmp_path / "other.xmodel").write_text(
        '<custommodel name="Other Singer"><faceInfo Name="Face" Mouth-AI="1"/></custommodel>'
    )
    assert detect_singing_faces(layout) == []
