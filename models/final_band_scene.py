"""Final six-performer scenes; historical seven-member rigs stay available."""
from __future__ import annotations

import numpy as np
from models.distinct_band_stages import DistinctBandScene
from models.band_performance_scene import matrix, rgb


class FinalBandScene(DistinctBandScene):
    def __init__(self, stage="ember_amphitheatre", *, rock=False, legacy_mallet_player=False):
        super().__init__(stage, wire=False)
        self.rock = rock
        self.legacy_mallet_player = bool(legacy_mallet_player)
        # Preserve both historical models/addresses internally. Render only
        # one pitched performer in the default cast: the genuine piano rig.
        # Legacy shows may explicitly request the old mallet character.
        active = "xylophone" if self.legacy_mallet_player else "piano"
        inactive = "piano" if self.legacy_mallet_player else "xylophone"
        hidden_prefixes = (inactive + "_",)
        if inactive == "piano":
            hidden_prefixes += ("keyboard_",)
        for item in self.instances:
            if item.get("performer_role") == inactive or item["name"].startswith(hidden_prefixes):
                item["kind"] = "hidden"
        self.custom = [o for o in self.custom if not o["name"].startswith(hidden_prefixes)]
        if self.legacy_mallet_player:
            # The former six-person arrangement is still opt-in and keeps
            # its existing artistic position and note/bar geometry.
            offset = np.array((13.1, 0., 0.))
            for item in self.instances:
                if item.get("performer_role") == "xylophone" or item["name"].startswith("xylophone_"):
                    item["matrix"][:3, 3] += offset
            for pitch in self.bars:
                self.bars[pitch] += offset
            for rig in self.rigs:
                if rig["role"] == "xylophone":
                    for key in ("shoulder", "elbow", "hand"):
                        rig[key] += offset
        self.visible_roles = ("drummer", "bass", "guitar", active, "lead", "harmony")
        # Purple belongs to the second singer independently of stage palette.
        for item in self.instances:
            if item.get("performer_role") == "harmony" and "scarf" in item["name"]:
                item["color"] = rgb("#9472C9")
        if rock:
            self._rock_costumes()
        self._attach_solid_faces()
        # Groove uses cached rest matrices. Refresh them after styling so the
        # inherited motion cannot restore a snowman body on the next frame.
        self.groove = [(i, role, self.instances[i]["matrix"].copy()) for i, role, _ in self.groove]
        self.technical_proof.update(
            band_members=list(self.visible_roles), unified_pitched_performer=True,
            style="solid rock band" if rock else "sculpted snow band",
            wireframe_performers=False, preserved_guitar_rig=True,
            continuous_motion_output="video or pixel matrix",
            legacy_mallet_player=self.legacy_mallet_player,
            pitched_character=active)

    def _attach_solid_faces(self):
        """Wire masks protrude intentionally; solid faces need attached mouths."""
        from models.expressive_band_face import update_expressive_mouth
        for role in ('lead', 'harmony'):
            head = next(o for o in self.instances if o['name'] == role+'_head')
            center = head['matrix'][:3, 3]
            depth = float(np.linalg.norm(head['matrix'][:3, 2]))
            mouth = center + (0, -.12, depth*.98)
            ids = self.expressive_mouths[role]
            ids['center'] = mouth.copy()
            self.instances[ids['cavity']]['mouth_center'] = mouth.copy()
            nose = next(o for o in self.instances if o['name'] == role+'_carrot')
            nose['matrix'][:3, 3] = center + (.038, .015, depth+.035)
            update_expressive_mouth(self, role, 'REST', 0)

    def _rock_costumes(self):
        jackets = {"bass": "#354554", "guitar": "#6D3435", "lead": "#283745",
                   "harmony": "#57416F",
                   ("xylophone" if self.legacy_mallet_player else "piano"): "#3B554F"}
        for role, jacket in jackets.items():
            head = next(o for o in self.instances if o["name"] == role + "_head")
            origin = head["matrix"][:3, 3] - (0, 2.28, 0)
            for item in self.instances:
                if item.get("performer_role") != role:
                    continue
                name = item["name"]
                if name.endswith("_base"):
                    item["kind"] = "box"; item["matrix"] = matrix(origin + (0, .65, 0), (.46, .92, .32))
                    item["color"] = rgb("#202938")
                elif name.endswith("_torso"):
                    item["kind"] = "box"; item["matrix"] = matrix(origin + (0, 1.42, 0), (.82, .85, .58))
                    item["color"] = rgb(jacket)
                elif name.endswith("_head"):
                    item["matrix"] = matrix(origin + (0, 2.28, 0), (.36, .42, .34))
                    item["color"] = rgb("#D1B29B")
                elif name.endswith("_carrot"):
                    item["matrix"][:3, :3] *= .32; item["color"] = rgb("#D1B29B")
                elif any(x in name for x in ("hat_", "holly", "berry", "coal_button", "scarf_tail")):
                    item["kind"] = "hidden"
            # Boots, leather collar and a swept hair silhouette are solid meshes.
            for side in (-1, 1):
                self.box(role + "_rock_boot", origin + (side*.21, .13, .11), (.32, .26, .57), "#141C27")
            self.sphere(role + "_rock_hair", origin + (0, 2.60, -.10), (.41, .19, .38), "#24222E")
            for side in (-1, 1):
                self.sphere(role + "_rock_hair_side", origin + (side*.34, 2.34, -.09), (.12, .38, .28), "#24222E")
            self.box(role + "_rock_belt", origin + (0, 1.04, .28), (.76, .10, .035), "#AD9B79")
            for item in self.instances:
                if item["name"].startswith(role + "_rock_"):
                    item["performer_role"] = role
