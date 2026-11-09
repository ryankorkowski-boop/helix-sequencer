"""Explicit preview composition for source-driven review shows only."""


def prepare_review_visibility(garden):
    # Store policy on the model: final refresh_models reserializes models and
    # must preserve it. Legacy gardens never call this, and explicit matte
    # choices remain authoritative. FSEQ/effect/channel data is untouched.
    for model in garden.models:
        model.attrs.setdefault('BlackTransparency', '100')
