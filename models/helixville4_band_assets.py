from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Point2D:
    x: float
    y: float

    def to_svg(self) -> str:
        return f"{self.x:.1f},{self.y:.1f}"


@dataclass(frozen=True)
class OutlineSegment:
    name: str
    submodel: str
    points: tuple[Point2D, ...]
    closed: bool = False
    stroke: str = "#ffffff"
    stroke_width: float = 3.0

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["points"] = [asdict(point) for point in self.points]
        return payload


@dataclass(frozen=True)
class BandModelAsset:
    asset_id: str
    member_id: str
    display_name: str
    model_prefix: str
    width_px: int
    height_px: int
    view: str
    background_role: str
    outline_segments: tuple[OutlineSegment, ...]
    submodel_order: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "member_id": self.member_id,
            "display_name": self.display_name,
            "model_prefix": self.model_prefix,
            "width_px": self.width_px,
            "height_px": self.height_px,
            "view": self.view,
            "background_role": self.background_role,
            "outline_segments": [segment.to_dict() for segment in self.outline_segments],
            "submodel_order": list(self.submodel_order),
        }


W = 420
H = 620


def p(x: float, y: float) -> Point2D:
    return Point2D(x, y)


def _dedupe_submodels(segments: tuple[OutlineSegment, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(segment.submodel for segment in segments))


def _snowman_body(prefix: str) -> tuple[OutlineSegment, ...]:
    return (
        OutlineSegment(f"{prefix}_hat", f"{prefix}_HAT", (p(145, 104), p(275, 104), p(288, 136), p(132, 136)), True, stroke_width=3.4),
        OutlineSegment(f"{prefix}_head", f"{prefix}_HEAD", (p(165, 150), p(210, 124), p(255, 150), p(270, 206), p(240, 246), p(180, 246), p(150, 206)), True, stroke_width=3.8),
        OutlineSegment(f"{prefix}_face", f"{prefix}_FACE", (p(176, 180), p(196, 172), p(220, 176), p(242, 190), p(238, 215), p(210, 226), p(182, 214)), True, stroke_width=2.6),
        OutlineSegment(f"{prefix}_torso", f"{prefix}_TORSO", (p(135, 260), p(285, 260), p(332, 438), p(290, 545), p(130, 545), p(88, 438)), True, stroke_width=4.0),
        OutlineSegment(f"{prefix}_buttons", f"{prefix}_BUTTONS", (p(210, 300), p(210, 362), p(210, 424), p(210, 486)), False, stroke_width=4.5),
    )


def _vocal_asset(member_id: str, prefix: str, display_name: str, *, harmony: bool = False) -> BandModelAsset:
    segments = (
        *_snowman_body(prefix),
        OutlineSegment(f"{prefix}_hair_left", f"{prefix}_HAIR", (p(145, 140), p(118, 205), p(128, 302), p(96, 390), p(118, 496), p(150, 548)), False, stroke_width=3.0),
        OutlineSegment(f"{prefix}_hair_right", f"{prefix}_HAIR", (p(275, 140), p(302, 210), p(292, 310), p(326, 402), p(300, 520), p(270, 552)), False, stroke_width=3.0),
        OutlineSegment(f"{prefix}_left_arm", f"{prefix}_LEFT_ARM", (p(135, 292), p(70, 226), p(42, 188), p(58, 170), p(96, 206), p(150, 262)), False, stroke_width=6.0),
        OutlineSegment(f"{prefix}_right_arm", f"{prefix}_RIGHT_ARM", (p(288, 292), p(346, 238), p(374, 198), p(390, 214), p(362, 270), p(302, 332)), False, stroke_width=6.0),
        OutlineSegment(f"{prefix}_microphone", f"{prefix}_MICROPHONE", (p(300, 150), p(365, 112), p(386, 132), p(322, 174)), False, stroke_width=5.2),
        OutlineSegment(f"{prefix}_mic_stand", f"{prefix}_MIC_STAND", (p(322, 174), p(292, 544)), False, stroke_width=3.4),
        OutlineSegment(f"{prefix}_scarf", f"{prefix}_SCARF", (p(155, 236), p(258, 238), p(296, 284), p(246, 304), p(182, 288)), False, stroke_width=4.4),
        OutlineSegment(f"{prefix}_mouth_phoneme", f"{prefix}_MOUTH_PHONEME", (p(185, 202), p(204, 194), p(230, 198), p(240, 216), p(222, 230), p(196, 224)), True, stroke="#ff9bc6", stroke_width=3.0),
    )
    if harmony:
        segments += (
            OutlineSegment(f"{prefix}_call_response_step", f"{prefix}_CALL_RESPONSE", (p(96, 548), p(136, 572), p(190, 556), p(246, 574), p(304, 548)), False, stroke_width=3.0),
        )
    return BandModelAsset(
        asset_id=f"{prefix}_front_background",
        member_id=member_id,
        display_name=display_name,
        model_prefix=prefix,
        width_px=W,
        height_px=H,
        view="front",
        background_role="performer_background_and_white_outline_map",
        outline_segments=segments,
        submodel_order=_dedupe_submodels(segments),
    )


def _guitar_asset(member_id: str, prefix: str, display_name: str, *, bass: bool = False) -> BandModelAsset:
    instrument = "BASS" if bass else "GUITAR"
    hand_zone = "PLUCK_ZONE" if bass else "STRUM_ZONE"
    segments = (
        *_snowman_body(prefix),
        OutlineSegment(f"{prefix}_hair_left", f"{prefix}_HAIR", (p(150, 132), p(120, 218), p(136, 350), p(102, 486), p(138, 560)), False, stroke_width=3.0),
        OutlineSegment(f"{prefix}_hair_right", f"{prefix}_HAIR", (p(270, 132), p(306, 228), p(290, 350), p(326, 490), p(286, 560)), False, stroke_width=3.0),
        OutlineSegment(f"{prefix}_glasses", f"{prefix}_GLASSES", (p(170, 184), p(200, 172), p(222, 174), p(252, 188)), False, stroke_width=3.0),
        OutlineSegment(f"{prefix}_left_arm", f"{prefix}_LEFT_ARM", (p(132, 310), p(82, 382), p(112, 426), p(164, 352)), False, stroke_width=6.0),
        OutlineSegment(f"{prefix}_right_arm", f"{prefix}_RIGHT_ARM", (p(285, 300), p(350, 236), p(378, 254), p(324, 338)), False, stroke_width=6.0),
        OutlineSegment(f"{prefix}_{instrument.lower()}_body", f"{prefix}_{instrument}_BODY", (p(112, 385), p(178, 336), p(260, 356), p(286, 440), p(230, 510), p(140, 496)), True, stroke="#ffd7a3", stroke_width=4.4),
        OutlineSegment(f"{prefix}_{instrument.lower()}_neck", f"{prefix}_{instrument}_NECK", (p(250, 356), p(370, 232), p(390, 250), p(276, 380)), False, stroke="#ffd7a3", stroke_width=5.0),
        OutlineSegment(f"{prefix}_{instrument.lower()}_strings", f"{prefix}_{instrument}_STRINGS", (p(146, 448), p(378, 238)), False, stroke="#ffffff", stroke_width=2.0),
        OutlineSegment(f"{prefix}_hand_zone", f"{prefix}_{hand_zone}", (p(174, 402), p(222, 388), p(250, 426), p(210, 462), p(166, 446)), True, stroke="#fff4c2", stroke_width=3.0),
        OutlineSegment(f"{prefix}_fret_hand", f"{prefix}_FRET_HAND", (p(314, 292), p(348, 254), p(366, 268), p(334, 310)), True, stroke_width=3.0),
    )
    return BandModelAsset(
        asset_id=f"{prefix}_front_background",
        member_id=member_id,
        display_name=display_name,
        model_prefix=prefix,
        width_px=W,
        height_px=H,
        view="front",
        background_role="performer_background_and_white_outline_map",
        outline_segments=segments,
        submodel_order=_dedupe_submodels(segments),
    )


def _drummer_asset() -> BandModelAsset:
    prefix = "HX_SNOWMAN_DRUMMER"
    segments = (
        *_snowman_body(prefix),
        OutlineSegment("drummer_left_arm_windup", f"{prefix}_LEFT_ARM", (p(150, 292), p(76, 170), p(56, 108), p(78, 96), p(110, 168), p(166, 276)), False, stroke_width=6.2),
        OutlineSegment("drummer_right_arm_windup", f"{prefix}_RIGHT_ARM", (p(270, 292), p(344, 170), p(362, 108), p(340, 96), p(308, 168), p(254, 276)), False, stroke_width=6.2),
        OutlineSegment("drummer_left_stick", f"{prefix}_LEFT_STICK", (p(58, 110), p(28, 52)), False, stroke="#fff4c2", stroke_width=3.0),
        OutlineSegment("drummer_right_stick", f"{prefix}_RIGHT_STICK", (p(362, 110), p(392, 52)), False, stroke="#fff4c2", stroke_width=3.0),
        OutlineSegment("drummer_sticks", f"{prefix}_STICKS", (p(28, 52), p(58, 110), p(362, 110), p(392, 52)), False, stroke="#fff4c2", stroke_width=2.0),
        OutlineSegment("drummer_kick", f"{prefix}_KICK", (p(156, 420), p(210, 388), p(264, 420), p(264, 514), p(156, 514)), True, stroke="#bcd7ff", stroke_width=4.0),
        OutlineSegment("drummer_snare", f"{prefix}_SNARE", (p(78, 396), p(138, 382), p(168, 420), p(116, 452), p(70, 432)), True, stroke="#c8ffc8", stroke_width=3.6),
        OutlineSegment("drummer_snare_rim", f"{prefix}_SNARE_RIM", (p(84, 400), p(132, 388), p(158, 420), p(116, 446), p(76, 430)), True, stroke="#ffffff", stroke_width=2.0),
        OutlineSegment("drummer_tom_left", f"{prefix}_TOM_LEFT", (p(150, 344), p(198, 330), p(224, 364), p(184, 392), p(140, 378)), True, stroke="#c8ffff", stroke_width=3.4),
        OutlineSegment("drummer_tom_right", f"{prefix}_TOM_RIGHT", (p(222, 344), p(270, 330), p(300, 364), p(258, 394), p(216, 378)), True, stroke="#c8ffff", stroke_width=3.4),
        OutlineSegment("drummer_floor_tom", f"{prefix}_FLOOR_TOM", (p(266, 408), p(330, 396), p(352, 438), p(316, 482), p(258, 462)), True, stroke="#c8ffff", stroke_width=3.4),
        OutlineSegment("drummer_tom", f"{prefix}_TOM", (p(140, 330), p(300, 330), p(352, 438), p(316, 482), p(184, 392)), True, stroke="#c8ffff", stroke_width=2.2),
        OutlineSegment("drummer_hihat", f"{prefix}_HI_HAT", (p(58, 324), p(120, 316), p(156, 328), p(116, 342), p(62, 338)), True, stroke="#fff48f", stroke_width=3.4),
        OutlineSegment("drummer_crash_cymbal", f"{prefix}_CRASH_CYMBAL", (p(56, 240), p(128, 224), p(184, 238), p(126, 258)), True, stroke="#fff48f", stroke_width=3.4),
        OutlineSegment("drummer_ride_cymbal", f"{prefix}_RIDE_CYMBAL", (p(236, 238), p(306, 220), p(374, 240), p(304, 260)), True, stroke="#fff48f", stroke_width=3.4),
        OutlineSegment("drummer_cymbals", f"{prefix}_CYMBALS", (p(56, 240), p(184, 238), p(236, 238), p(374, 240), p(304, 260), p(126, 258)), True, stroke="#fff48f", stroke_width=2.2),
    )
    return BandModelAsset(
        asset_id=f"{prefix}_front_background",
        member_id="snowman_drummer",
        display_name="Mad Drummer Snowman",
        model_prefix=prefix,
        width_px=W,
        height_px=H,
        view="front",
        background_role="performer_background_and_white_outline_map",
        outline_segments=segments,
        submodel_order=_dedupe_submodels(segments),
    )


HELIXVILLE4_BAND_ASSETS: tuple[BandModelAsset, ...] = (
    _vocal_asset("snowman_singer", "HX_SNOWMAN_SINGER", "Lead Vocal Snowman"),
    _vocal_asset("snowman_singer_female", "HX_SNOWMAN_SINGER_FEMALE", "Harmony Vocal Snowman", harmony=True),
    _guitar_asset("snowman_guitarist", "HX_SNOWMAN_GUITARIST", "Rock Guitar Snowman"),
    _guitar_asset("snowman_bassist", "HX_SNOWMAN_BASSIST", "Bass Snowman", bass=True),
    _drummer_asset(),
)


def svg_for_band_asset(asset: BandModelAsset) -> str:
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{asset.width_px}" height="{asset.height_px}" viewBox="0 0 {asset.width_px} {asset.height_px}">',
        '<rect width="100%" height="100%" fill="#0c1220"/>',
        '<g opacity="0.28" stroke="#6e7f99" stroke-width="1">',
    ]
    for x in range(0, asset.width_px + 1, 20):
        lines.append(f'<line x1="{x}" y1="0" x2="{x}" y2="{asset.height_px}"/>')
    for y in range(0, asset.height_px + 1, 20):
        lines.append(f'<line x1="0" y1="{y}" x2="{asset.width_px}" y2="{y}"/>')
    lines.extend([
        '</g>',
        f'<text x="20" y="36" fill="#ffffff" font-size="22" font-family="monospace">{asset.display_name}</text>',
        f'<text x="20" y="60" fill="#b9c7ff" font-size="12" font-family="monospace">{asset.asset_id}</text>',
        '<g fill="none" stroke-linecap="round" stroke-linejoin="round">',
    ])
    for segment in asset.outline_segments:
        coords = " ".join(point.to_svg() for point in segment.points)
        if segment.closed:
            lines.append(
                f'<polygon points="{coords}" stroke="{segment.stroke}" stroke-width="{segment.stroke_width:.1f}" fill="none" data-submodel="{segment.submodel}"/>'
            )
        else:
            lines.append(
                f'<polyline points="{coords}" stroke="{segment.stroke}" stroke-width="{segment.stroke_width:.1f}" fill="none" data-submodel="{segment.submodel}"/>'
            )
    lines.extend(['</g>', '</svg>'])
    return "\n".join(lines) + "\n"


def build_helixville4_band_asset_catalog() -> dict[str, Any]:
    return {
        "schema": "helixville4.band_assets.v1",
        "scope": "background_svg_and_white_outline_maps",
        "asset_count": len(HELIXVILLE4_BAND_ASSETS),
        "assets": [asset.to_dict() for asset in HELIXVILLE4_BAND_ASSETS],
    }


def band_asset_by_member(member_id: str) -> BandModelAsset:
    normalized = member_id.strip().lower().replace("-", "_").replace(" ", "_")
    for asset in HELIXVILLE4_BAND_ASSETS:
        if asset.member_id == normalized:
            return asset
    known = ", ".join(asset.member_id for asset in HELIXVILLE4_BAND_ASSETS)
    raise KeyError(f"Unknown Helixville4 band asset {member_id!r}. Known assets: {known}")
