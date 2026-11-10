from __future__ import annotations

from models.helixville4_performer_runtime import HELIXVILLE4_PERFORMERS
from tools.build_helpers.helixville4_full_band import FULL_BAND_SPECS


def test_runtime_catalog_matches_full_band_model_specs() -> None:
    specs_by_model = {spec.model_name: spec for spec in FULL_BAND_SPECS}

    assert set(specs_by_model) == {performer.model_name for performer in HELIXVILLE4_PERFORMERS}

    for performer in HELIXVILLE4_PERFORMERS:
        full_spec = specs_by_model[performer.model_name]
        generated_submodels = {f"{full_spec.model_name}_{part.name}" for part in full_spec.parts}
        assert set(performer.submodels) == generated_submodels
        for state in performer.states:
            assert set(state.primary_submodels) <= generated_submodels
