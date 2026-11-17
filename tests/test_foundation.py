from datetime import datetime, timezone

from yemenvision.association import CrossCameraAssociator, Tracklet
from yemenvision.eval import EvaluationStatus, Result
from yemenvision.registry import EXPECTED_CLASSES, ModelRegistry


def test_class_contract():
    assert len(EXPECTED_CLASSES) == 21
    assert EXPECTED_CLASSES[0] == "ambulance"


def test_association_is_one_to_one_and_auditable():
    t = datetime.now(timezone.utc)
    source = Tracklet("a", 1, t, t, [1.0, 0.0], "car")
    target = Tracklet("b", 2, t, t, [1.0, 0.0], "car")
    links = CrossCameraAssociator({"a": {"b": {"min_seconds": -1, "max_seconds": 1}}}, threshold=0.1).associate([source], [target])
    assert len(links) == 1
    assert links[0].reasons["appearance_cosine"] == 1.0
    assert 0 <= links[0].confidence <= 1


def test_not_evaluated_is_explicit():
    result = Result("official_mtmc", EvaluationStatus.NOT_EVALUATED, {}, "No synchronized multi-camera ground truth")
    assert result.as_dict()["status"] == "NOT_EVALUATED"


def test_missing_models_are_not_silent():
    assert ModelRegistry("does-not-exist").discover() == []
