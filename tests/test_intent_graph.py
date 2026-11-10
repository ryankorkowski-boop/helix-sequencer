from core.choreography_intent import (
    ChoreographyIntent,
    MotionVocabulary,
)
from core.intent_graph import IntentGraph



def build_intent(start: float, duration: float, section: str, style: str, event_type: str):
    return ChoreographyIntent(
        start=start,
        duration=duration,
        section=section,
        event_type=event_type,
        style=style,
        emotional_energy=0.5,
        intensity=0.5,
        focal_region="center",
        motion_vocabulary=(MotionVocabulary.SWEEP,),
    )



def test_graph_orders_intents_by_start_time():
    graph = IntentGraph()

    graph.add_intent(build_intent(20.0, 1.0, "chorus", "SpatialHelix", "drop"))
    graph.add_intent(build_intent(5.0, 1.0, "verse", "ClassicChristmas", "beat"))
    graph.add_intent(build_intent(10.0, 1.0, "bridge", "CinematicSweep", "build"))

    starts = [intent.start for intent in graph]

    assert starts == [5.0, 10.0, 20.0]



def test_graph_section_queries_work():
    graph = IntentGraph(
        [
            build_intent(0.0, 2.0, "verse", "SpatialHelix", "beat"),
            build_intent(3.0, 2.0, "verse", "SpatialHelix", "build"),
            build_intent(6.0, 2.0, "chorus", "SpatialHelix", "drop"),
        ]
    )

    verse_intents = graph.by_section("verse")

    assert len(verse_intents) == 2



def test_graph_style_queries_work():
    graph = IntentGraph(
        [
            build_intent(0.0, 2.0, "verse", "SpatialHelix", "beat"),
            build_intent(3.0, 2.0, "verse", "ClassicChristmas", "build"),
        ]
    )

    helix_intents = graph.by_style("SpatialHelix")

    assert len(helix_intents) == 1



def test_overlap_detection_works():
    graph = IntentGraph(
        [
            build_intent(0.0, 5.0, "verse", "SpatialHelix", "beat"),
            build_intent(3.0, 5.0, "chorus", "SpatialHelix", "drop"),
        ]
    )

    overlaps = graph.detect_overlaps()

    assert len(overlaps) == 1
    assert overlaps[0].overlap_duration == 2.0



def test_window_queries_work():
    graph = IntentGraph(
        [
            build_intent(0.0, 2.0, "intro", "ClassicChristmas", "texture"),
            build_intent(5.0, 2.0, "verse", "SpatialHelix", "beat"),
        ]
    )

    active = graph.within_window(4.5, 5.5)

    assert len(active) == 1
    assert active[0].section == "verse"



def test_timeline_density_returns_expected_points():
    graph = IntentGraph(
        [
            build_intent(0.0, 5.0, "verse", "SpatialHelix", "beat"),
            build_intent(2.0, 5.0, "chorus", "SpatialHelix", "drop"),
        ]
    )

    density = graph.timeline_density(resolution=1.0)

    assert len(density) > 0
    assert density[0][1] >= 1



def test_graph_serialization_contains_expected_fields():
    graph = IntentGraph(
        [
            build_intent(0.0, 2.0, "intro", "ClassicChristmas", "texture"),
        ]
    )

    data = graph.to_dict()

    assert data["intent_count"] == 1
    assert data["ordered_sections"] == ["intro"]
    assert len(data["intents"]) == 1
