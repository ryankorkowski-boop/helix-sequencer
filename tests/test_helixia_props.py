from __future__ import annotations

import json
import unittest

from models.helixia_props import (
    CACTUS_TUBEMAN_MODELS,
    SNOWMAN_BAND_MEMBERS,
    HelixiaPropDefinition,
    build_cactus_tubeman_dj_structure,
    build_snowman_band_export_catalog,
    build_snowman_band_group_definitions,
    build_snowman_band_structures,
    build_snowman_drummer_structure,
)


class HelixiaPropsTests(unittest.TestCase):
    def _assert_member_structure(self, prop: HelixiaPropDefinition) -> None:
        model_names = {model.name for model in prop.models}
        submodel_names = {submodel.name for submodel in prop.submodels}
        group_map = {group.name: set(group.members) for group in prop.groups}

        self.assertIn(f"{prop.name}_BODY", model_names)
        self.assertIn(f"{prop.name}_INSTRUMENT", model_names)
        self.assertTrue({f"{prop.name}_ARMS", f"{prop.name}_HEAD", f"{prop.name}_TORSO"}.issubset(submodel_names))
        self.assertEqual(group_map[prop.name], {f"{prop.name}_BODY", f"{prop.name}_INSTRUMENT"})
        self.assertIn(prop.name, group_map["HX_SNOWMAN_BAND"])
        self.assertIn("HX_SNOWMAN_BAND", group_map["HELIXIA_STAGE"])
        self.assertTrue(all(model.exportable for model in prop.models))

    def test_snowman_drummer_models_submodels_and_groups(self) -> None:
        prop = build_snowman_drummer_structure()
        submodel_names = {submodel.name for submodel in prop.submodels}

        self.assertEqual(prop.name, "HX_SNOWMAN_DRUMMER")
        self._assert_member_structure(prop)
        self.assertTrue(
            {
                "HX_SNOWMAN_DRUMMER_KICK",
                "HX_SNOWMAN_DRUMMER_SNARE",
                "HX_SNOWMAN_DRUMMER_TOM",
                "HX_SNOWMAN_DRUMMER_CYMBALS",
                "HX_SNOWMAN_DRUMMER_HI_HAT",
                "HX_SNOWMAN_DRUMMER_STICKS",
            }.issubset(submodel_names)
        )

    def test_all_snowman_band_members_have_structural_models(self) -> None:
        props = build_snowman_band_structures()
        prop_map = {prop.name: prop for prop in props}

        self.assertEqual(set(prop_map), set(SNOWMAN_BAND_MEMBERS))
        for prop in props:
            self._assert_member_structure(prop)

    def test_snowman_band_aggregate_groups_include_all_members(self) -> None:
        group_map = {group.name: set(group.members) for group in build_snowman_band_group_definitions()}

        self.assertEqual(group_map["HX_SNOWMAN_BAND"], set(SNOWMAN_BAND_MEMBERS))
        self.assertEqual(group_map["HELIXIA_STAGE"], {"HX_SNOWMAN_BAND"})
        for member in SNOWMAN_BAND_MEMBERS:
            self.assertEqual(group_map[member], {f"{member}_BODY", f"{member}_INSTRUMENT"})

    def test_member_specific_instrument_submodels_are_present(self) -> None:
        prop_map = {prop.name: prop for prop in build_snowman_band_structures()}
        expected = {
            "HX_SNOWMAN_BASSIST": {"BASS_BODY", "BASS_NECK", "BASS_STRINGS", "PLUCK_ZONE"},
            "HX_SNOWMAN_GUITARIST": {"GUITAR_BODY", "GUITAR_NECK", "GUITAR_STRINGS", "STRUM_ZONE"},
            "HX_SNOWMAN_DRUMMER": {"KICK", "SNARE", "TOM", "CYMBALS", "HI_HAT", "STICKS"},
            "HX_SNOWMAN_SINGER": {"MICROPHONE", "MIC_STAND"},
            "HX_SNOWMAN_SINGER_FEMALE": {"MICROPHONE", "MIC_STAND"},
        }

        for member, suffixes in expected.items():
            submodel_names = {submodel.name for submodel in prop_map[member].submodels}
            self.assertTrue({f"{member}_{suffix}" for suffix in suffixes}.issubset(submodel_names))

    def test_snowman_band_export_catalog_is_json_ready_structure_only(self) -> None:
        catalog = build_snowman_band_export_catalog()
        encoded = json.dumps(catalog, sort_keys=True)
        decoded = json.loads(encoded)
        group_map = {group["name"]: set(group["members"]) for group in decoded["groups"]}

        self.assertEqual(decoded["schema"], "helixia.props.catalog.v1")
        self.assertEqual(decoded["catalog_id"], "HX_SNOWMAN_BAND")
        self.assertEqual(decoded["scope"], "structure_only")
        self.assertEqual(len(decoded["props"]), len(SNOWMAN_BAND_MEMBERS))
        self.assertEqual(group_map["HX_SNOWMAN_BAND"], set(SNOWMAN_BAND_MEMBERS))
        self.assertFalse(decoded["implementation_boundary"]["layout_generation"])
        self.assertFalse(decoded["implementation_boundary"]["layout_xml_modification"])
        self.assertFalse(decoded["implementation_boundary"]["sequencing"])
        self.assertFalse(decoded["implementation_boundary"]["timing"])
        self.assertFalse(decoded["implementation_boundary"]["audio"])
        self.assertFalse(decoded["implementation_boundary"]["animation"])

    def test_cactus_tubeman_dj_models_submodels_and_groups(self) -> None:
        prop = build_cactus_tubeman_dj_structure()
        model_names = {model.name for model in prop.models}
        submodel_names = {submodel.name for submodel in prop.submodels}
        group_map = {group.name: set(group.members) for group in prop.groups}

        self.assertEqual(prop.name, "HX_CACTUS_TUBEMAN_GROUP")
        self.assertEqual(model_names, set(CACTUS_TUBEMAN_MODELS))
        self.assertTrue(
            {
                "HX_CACTUS_BODY_CORE",
                "HX_CACTUS_LEFT_ARM",
                "HX_CACTUS_RIGHT_ARM",
                "HX_CACTUS_FACE_EYES",
                "HX_CACTUS_FACE_MOUTH",
                "HX_TUBEMAN_BODY_CORE",
                "HX_TUBEMAN_HEAD",
                "HX_TUBEMAN_LEFT_ARM",
                "HX_TUBEMAN_RIGHT_ARM",
                "HX_DJ_BOOTH_FRONT",
                "HX_DJ_BOOTH_DECKS",
                "HX_DJ_BOOTH_SPEAKERS",
            }.issubset(submodel_names)
        )
        self.assertEqual(group_map["HX_CACTUS_TUBEMAN_GROUP"], set(CACTUS_TUBEMAN_MODELS))
        self.assertEqual(group_map["HELIXIA_STAGE"], {"HX_CACTUS_TUBEMAN_GROUP"})
        self.assertTrue(all(model.exportable for model in prop.models))


if __name__ == "__main__":
    unittest.main()
