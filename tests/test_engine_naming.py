from __future__ import annotations

from core.engine_naming import internal_engine_name, public_engine_name


def test_birdsong_exports_under_helix_flow_public_name() -> None:
    assert public_engine_name("birdsong") == "Helix Flow Engine"
    assert internal_engine_name("birdsong") == "Birdsong Engine"
