from core.canonical_timeline_orchestrator import MusicalContext
from core.composition_governor import CompositionGovernor
from core.orchestration_balance import PlacementProposal
from core.physical_targets import PhysicalTargets
from xlights.layout_sync import layout_entries_and_lookup, map_layout_name


def test_aliases_nested_groups_and_physical_submodel_ownership(tmp_path):
    layout = tmp_path / "xlights_rgbeffects.xml"
    layout.write_text("""<xrgb><models>
      <model name="Nova"><Aliases><alias name="OldName:Lead Singer"/></Aliases>
        <faceInfo Name="Main" Type="NodeRange"/>
        <subModel name="Left" line0="1-4"><aliases><alias name="Mouth L"/></aliases></subModel>
        <subModel name="Right" line0="8-5,0"/>
        <subModel name="Crop" type="subbuffer" subBuffer="0x0x50x50"/>
      </model>
      <model name="Keys"><Aliases><alias name="OldName:Piano"/><alias name="Duplicate"/></Aliases></model>
      <model name="Arch"><Aliases><alias name="Duplicate"/></Aliases></model>
      </models><modelGroups>
        <modelGroup name="VoiceMix" models="Lead Singer/Mouth L"/>
        <modelGroup name="Nested" models="VoiceMix,Arch">
          <Aliases><alias name="OldName:Outer"/></Aliases>
        </modelGroup>
        <modelGroup name="Missing" models="Unknown,Arch"/>
        <modelGroup name="CycleA" models="CycleB"/>
        <modelGroup name="CycleB" models="CycleA,Arch"/>
      </modelGroups></xrgb>""")
    targets = PhysicalTargets(layout)
    assert targets.resolve("Lead Singer/Mouth L") == "Nova/Left"
    assert targets.resolve("Outer") == "Nested"
    assert targets.members["Nested"] == {"Nova/Left", "Arch"}
    assert {"Nested", "Nova", "Nova/Crop", "VoiceMix"} <= targets.shared_rows("Nova/Left")
    assert "Nova/Right" not in targets.shared_rows("Nova/Left")
    assert "Nova/Right" in targets.shared_rows("Nova/Crop")
    assert targets.invalid == {"Missing", "CycleA", "CycleB"}
    _, lookup = layout_entries_and_lookup(layout)
    assert map_layout_name("Lead Singer/Mouth L", lookup) == "Nova/Left"
    assert map_layout_name("Outer", lookup) == "Nested"
    assert map_layout_name("Duplicate", lookup) is None
    assert targets.resolve("Duplicate") is None

    session = CompositionGovernor().begin_placement(
        MusicalContext(1000, ()), targets.members, physical=targets,
    )
    assert session.has_singer and session.has_piano

    def proposal(model, lane):
        return session.resolve_proposal(PlacementProposal(model, "renamed", 10, 120, "On", lane=lane))

    assert session.ownership_rejection(proposal("Lead Singer/Mouth L", "vocal")) is None
    assert session.ownership_rejection(proposal("Keys", "piano_overlay")) is None
    assert session.ownership_rejection(proposal("Nested", "overlay")) == "accent kept off dedicated performer"
    assert session.ownership_rejection(proposal("Missing", "primary")) == "unresolved physical target"
    assert session.ownership_rejection(proposal("CycleB", "primary")) == "unresolved physical target"


def test_explicit_performer_fields_preserve_legacy_labels():
    legacy = PlacementProposal("Kit/Kick", "band_drummer_hit", 132, 292, "On")
    explicit = PlacementProposal(
        "Kit/Kick", "renamed", 132, 292, "On", engine="drummer", lane="percussion", timing_anchor=True,
    )
    assert explicit.timing_anchor == legacy.timing_anchor is True
    assert explicit.engine == legacy.engine == "drummer"
    assert explicit.lane == "percussion"


def test_native_submodel_layers_round_trip_without_retiming(tmp_path):
    import xml.etree.ElementTree as ET

    from tools.preview_renderer import parse_sequence
    from xlights.layout_sync import pack_native_submodels, unpack_native_submodels

    root = ET.fromstring("""<xsequence><ElementEffects><Element name="Prop" type="model">
      <SubModelEffectLayer name="Left" layer="2" layerName="Authored">
        <Effect name="On" startTime="13" endTime="87" ref="4"/>
      </SubModelEffectLayer>
    </Element></ElementEffects></xsequence>""")
    unpack_native_submodels(root)
    layers = root.findall("./ElementEffects/Element[@name='Prop/Left']/EffectLayer")
    assert len(layers) == 3 and layers[2].get("name") == "Authored"
    pack_native_submodels(root, {"Prop": "Prop", "Prop/Left": "Prop"}, "AUTO_")
    layer = root.find("./ElementEffects/Element[@name='Prop']/SubModelEffectLayer")
    assert (layer.get("name"), layer.get("layer"), layer.get("layerName")) == ("Left", "2", "Authored")
    assert layer.find("Effect").attrib == {"name": "On", "startTime": "13", "endTime": "87", "ref": "4"}
    path = tmp_path / "native.xsq"
    ET.ElementTree(root).write(path)
    event, = parse_sequence(path).model_effects["Prop/Left"]
    assert (event.name, event.start_ms, event.end_ms) == ("On", 13, 87)
