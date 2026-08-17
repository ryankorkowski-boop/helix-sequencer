from core.spatial_render_bridge import build_render_scene, validate_true_3d
from core.spatial_scene import (
    LAYOUT_CAPABILITY_2D,
    LAYOUT_CAPABILITY_3D,
    LayoutCapabilityReport,
    SceneNode,
    SpatialScene,
)


def _scene(capability: str) -> SpatialScene:
    node_a = SceneNode(
        name="A",
        kind="model",
        center_xyz=(0.0, 0.0, 0.0),
        extents_xyz=(10.0, 10.0, 2.0),
        projected_xy=(0.0, 0.0),
        bounds_xyz=(-5.0, -5.0, -1.0, 5.0, 5.0, 1.0),
        projected_bounds_xy=(-5.0, -5.0, 5.0, 5.0),
        projected_outline_xy=((-5.0, -5.0), (5.0, 5.0)),
        tags=("model", "root"),
        groups=(),
    )
    node_b = SceneNode(
        name="B",
        kind="model",
        center_xyz=(0.0, 0.0, 100.0),
        extents_xyz=(10.0, 10.0, 10.0),
        projected_xy=(0.0, 0.0),
        bounds_xyz=(-5.0, -5.0, 95.0, 5.0, 5.0, 105.0),
        projected_bounds_xy=(-5.0, -5.0, 5.0, 5.0),
        projected_outline_xy=((-5.0, -5.0), (5.0, 5.0)),
        tags=("model", "root"),
        groups=(),
    )
    report = LayoutCapabilityReport(
        capability=capability,
        model_count=2,
        horizontal_span=0.0,
        vertical_span=0.0,
        depth_span=100.0,
        depth_ratio=100.0,
        depth_layer_count=2,
        layered_model_ratio=1.0,
        volumetric_model_ratio=1.0,
    )
    return SpatialScene(
        path=None,
        capability=capability,
        capability_report=report,
        nodes={"A": node_a, "B": node_b},
        group_nodes={},
        groups={},
        aliases={},
    )


def test_bridge_preserves_xyz_and_marks_true_3d():
    render_scene = build_render_scene(_scene(LAYOUT_CAPABILITY_3D))
    assert render_scene.is_true_3d
    assert render_scene.bounds == (-5.0, -5.0, -1.0, 5.0, 5.0, 105.0)
    assert render_scene.nodes[1].position == (0.0, 0.0, 100.0)
    assert validate_true_3d(render_scene) == (True, "true 3D scene")


def test_bridge_does_not_claim_2d_scene_is_3d():
    render_scene = build_render_scene(_scene(LAYOUT_CAPABILITY_2D))
    assert not render_scene.is_true_3d
    ok, message = validate_true_3d(render_scene)
    assert not ok
    assert "not '3d'" in message
