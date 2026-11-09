"""Single mallet performer with keyboard/marimba/xylophone note zones.

One musician, not a duplicate keyboardist. A front-view geometric asset,
with both hands and a shared pitched-instrument playing surface.
"""
from models.helixville4_band_assets import (
    BandModelAsset, OutlineSegment, _snowman_body, _dedupe_submodels, p, W, H,
)


def mallet_performer_asset() -> BandModelAsset:
    prefix = "HX_SNOWMAN_MALLET"
    segments = (
        *_snowman_body(prefix),
        OutlineSegment("mallet_left_arm", prefix + "_LEFT_ARM",
                       (p(132, 310), p(104, 365), p(155, 405)), False, stroke_width=6),
        OutlineSegment("mallet_right_arm", prefix + "_RIGHT_ARM",
                       (p(288, 310), p(316, 365), p(266, 405)), False, stroke_width=6),
        OutlineSegment("mallet_left_stick", prefix + "_LEFT_MALLET",
                       (p(155, 405), p(170, 442)), False, stroke_width=5),
        OutlineSegment("mallet_right_stick", prefix + "_RIGHT_MALLET",
                       (p(266, 405), p(250, 442)), False, stroke_width=5),
        OutlineSegment("mallet_keys_low", prefix + "_KEYS_LOW",
                       (p(52, 454), p(156, 454), p(156, 510), p(52, 510)), True),
        OutlineSegment("mallet_keys_mid", prefix + "_KEYS_MID",
                       (p(156, 454), p(264, 454), p(264, 510), p(156, 510)), True),
        OutlineSegment("mallet_keys_high", prefix + "_KEYS_HIGH",
                       (p(264, 454), p(368, 454), p(368, 510), p(264, 510)), True),
        OutlineSegment("mallet_instrument_frame", prefix + "_FRAME",
                       (p(44, 445), p(376, 445), p(376, 535), p(44, 535)), True),
    )
    return BandModelAsset(
        asset_id=prefix + "_front_background",
        member_id="snowman_mallet_player",
        display_name="Mallet / Keys Snowman",
        model_prefix=prefix,
        width_px=W, height_px=H, view="front",
        background_role="performer_background_and_white_outline_map",
        outline_segments=segments,
        submodel_order=_dedupe_submodels(segments),
    )
