import json
from pathlib import Path

import numpy as np

from yemenvision.association import run_mtmc


def _run(root: Path, camera: str, track: int, embedding: list[float]) -> Path:
    run = root / camera
    run.mkdir()
    (run / "tracklets.jsonl").write_text(json.dumps({
        "camera_id": camera, "track_id": track, "class_name": "car",
        "t_start": 10.0 if camera == "cam02" else 0.0, "t_end": 11.0 if camera == "cam02" else 1.0,
        "embedding_index": 0,
    }) + "\n", encoding="utf-8")
    np.save(run / "embeddings.npy", np.asarray([embedding], dtype=np.float32))
    return run


def test_mtmc_abstains_without_topology(tmp_path):
    first = _run(tmp_path, "cam01", 1, [1.0, 0.0])
    second = _run(tmp_path, "cam02", 2, [1.0, 0.0])
    result = run_mtmc([first, second], tmp_path / "out", None)
    assert result.links == []
    assert result.abstentions
    assert (tmp_path / "out" / "global_vehicles.json").is_file()


def test_mtmc_global_ids_are_deterministic(tmp_path):
    first = _run(tmp_path, "cam01", 1, [1.0, 0.0])
    second = _run(tmp_path, "cam02", 2, [1.0, 0.0])
    topology = tmp_path / "cameras.yaml"
    topology.write_text("cameras:\n  cam01:\n    transitions:\n      cam02: {min_seconds: 1, max_seconds: 20}\n  cam02:\n    transitions: {}\n", encoding="utf-8")
    result = run_mtmc([first, second], tmp_path / "out", topology, threshold=0.1)
    assert result.global_vehicles[0]["global_id"] == "gv_000001"
    assert len(result.global_vehicles[0]["tracklets"]) == 2
