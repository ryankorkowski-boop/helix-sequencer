from pathlib import Path

from core.physical_targets import PhysicalTargets, physical_placement_block


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
    assert targets.resolve("Duplicate") is None


def test_shared_layer_blocks_only_an_occupied_peer(tmp_path):
    layout = tmp_path / "xlights_rgbeffects.xml"
    layout.write_text("""<xrgb><models>
      <model name="Nova">
        <subModel name="Left" line0="1-4"/>
        <subModel name="Right" line0="5-8"/>
      </model>
      </models><modelGroups>
        <modelGroup name="Voice" models="Nova/Left"/>
        <modelGroup name="Missing" models="Unknown"/>
      </modelGroups></xrgb>""")
    targets = PhysicalTargets(layout)
    occupied = {"Voice"}
    assert physical_placement_block(None, "Nova/Left", layer_occupied=lambda peer: peer in occupied) is None
    assert physical_placement_block(
        targets, "Missing", layer_occupied=lambda peer: False
    ) == "unresolved physical target"
    assert physical_placement_block(
        targets, "Nova/Left", layer_occupied=lambda peer: peer in occupied
    ) == "shared physical target already occupied on this layer"
    assert physical_placement_block(
        targets, "Nova/Right", layer_occupied=lambda peer: peer in occupied
    ) is None


def test_live_placer_calls_the_physical_and_role_gates():
    text = (Path(__file__).resolve().parents[1] / "core" / "effect_engine.py").read_text(encoding="utf-8")
    assert "physical_placement_block(" in text
    assert "PhysicalTargets(active_layout_file)" in text
    assert "balance.allows_piano_overlay" in text
    assert "balance.allows_vocal" in text
    assert "_section_budget_ok" in text
    assert "_section_budget_take" in text

