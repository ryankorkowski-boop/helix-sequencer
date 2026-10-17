import pytest
from tools.sequence_quality_benchmark import score_entries, summarize

def entry(kind="helix", reviewer="r1", scores=None):
    return {"id":"sample","kind":kind,"reviewer":reviewer,
            "scores":scores or {"synchronization":5,"choreography":4,"performance":3,"compatibility":2,"import":1}}

def test_weighted_score():
    result=score_entries([entry()])
    assert result[0]["score_100"]==70.0

def test_grouped_reviewer_scores():
    a=entry()
    b=entry(reviewer="r2",scores={k:0 for k in a["scores"]})
    summary=summarize([a,b])
    assert summary["items"][0]["review_count"]==2
    assert summary["items"][0]["mean_score_100"]==35.0

@pytest.mark.parametrize("change",[
    {"kind":"unknown"},
    {"scores":{"synchronization":5}},
    {"scores":{"synchronization":True,"choreography":4,"performance":3,"compatibility":2,"import":1}},
    {"scores":{"synchronization":6,"choreography":4,"performance":3,"compatibility":2,"import":1}},
    {"reviewer":""}
])
def test_invalid_reviews_rejected(change):
    with pytest.raises(ValueError):score_entries([{**entry(),**change}])

def test_duplicate_reviewer_rejected():
    with pytest.raises(ValueError):score_entries([entry(),entry()])
