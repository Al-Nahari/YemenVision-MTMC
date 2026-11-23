import json
from datetime import datetime, timezone

from yemenvision.association import CrossCameraAssociator, Tracklet
from yemenvision.config import load_settings
from yemenvision.registry import EXPECTED_CLASSES, ModelRegistry


def test_config_env_override(monkeypatch, tmp_path):
    monkeypatch.setenv("YV_MODELS_DIR", str(tmp_path / "weights"))
    settings = load_settings("configs/default.yaml")
    assert settings.models_dir == (tmp_path / "weights")
    assert settings.detection.imgsz == 800


def test_registry_rejects_invalid_names_without_torch(tmp_path):
    model = tmp_path / "best.pt"
    model.write_bytes(b"not-a-checkpoint")
    registry = ModelRegistry(tmp_path)
    record = registry.discover()[0]
    assert record.path == model
    # No manifest means no unsafe deserialization during normal discovery.
    assert record.valid
    assert registry.select("detector").path == model


def test_registry_class_contract_constant_is_stable():
    assert len(EXPECTED_CLASSES) == 21
    assert EXPECTED_CLASSES[-1] == "wheelbarrow"


def test_registry_revokes_a_manifest_model_even_when_the_hash_matches(tmp_path):
    model = tmp_path / "reid_best.pt"
    model.write_bytes(b"truncated")
    registry = ModelRegistry(tmp_path)
    expected = registry.sha256(model)
    (tmp_path / "manifest.json").write_text(json.dumps({
        "models": {"reid_best.pt": {"sha256": expected}},
        "revoked": {"reid_best.pt": "truncated local artifact"},
    }), encoding="utf-8")

    record = ModelRegistry(tmp_path).discover()[0]

    assert not record.valid
    assert any("revoked" in issue.message for issue in record.issues)


def test_registry_detects_a_truncated_checkpoint_before_torch_load(tmp_path):
    model = tmp_path / "detector_best.pt"
    model.write_bytes(b"not-a-zip")

    record = ModelRegistry(tmp_path).validate_checkpoint(model)

    assert not record.valid
    assert any("ZIP archive" in issue.message for issue in record.issues)


def test_registry_flags_a_manifest_hash_mismatch(tmp_path):
    model = tmp_path / "detector_best.pt"
    model.write_bytes(b"payload")
    (tmp_path / "manifest.json").write_text(json.dumps({
        "models": {"detector_best.pt": {"sha256": "0" * 64}},
    }), encoding="utf-8")

    record = ModelRegistry(tmp_path).discover()[0]

    assert not record.valid
    assert any("SHA-256" in issue.message for issue in record.issues)


def test_associator_rejects_zero_norm_and_dimension_mismatch():
    t = datetime.now(timezone.utc)
    association = CrossCameraAssociator({"a": {"b": {"min_seconds": -1, "max_seconds": 1}}}, threshold=0.1)
    zero = Tracklet("a", 1, t, t, [0.0, 0.0])
    good = Tracklet("b", 2, t, t, [1.0, 0.0])
    assert association.associate([zero], [good]) == []
    wrong = Tracklet("b", 3, t, t, [1.0, 0.0, 0.0])
    assert association.associate([good], [wrong]) == []
