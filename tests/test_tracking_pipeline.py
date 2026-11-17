from pathlib import Path

import numpy as np

from yemenvision.detection import Detection
from yemenvision.pipeline import OfflinePipeline
from yemenvision.tracking import IoUTracker, TrackletBuilder


class SyntheticCapture:
    def __init__(self, path: Path, stride: int):
        self.fps = 10.0
        self.frame_count = 4
        self.width = 64
        self.height = 64
        self._frames = [(i, np.full((64, 64, 3), i + 1, dtype=np.uint8)) for i in range(4) if i % stride == 0]

    def __iter__(self):
        return iter(self._frames)

    def close(self):
        return None


class SyntheticDetector:
    synthetic_test = True

    def detect(self, frame):
        del frame
        return [Detection(5, "car", 0.9, (10.0, 10.0, 40.0, 40.0))]


class SyntheticEncoder:
    synthetic_test = True

    def encode(self, crops):
        return np.tile(np.array([[3.0, 4.0]], dtype=np.float32), (len(crops), 1))


def test_tracklet_builder_uses_fps_and_limits_crops():
    builder = TrackletBuilder("cam01", fps=10.0, max_crops=2, max_crop_memory_mb=1)
    frame = np.ones((32, 32, 3), dtype=np.uint8)
    for i in range(5):
        builder.add(1, i, (2, 2, 20, 20), "car", 0.9, frame)
    record = builder.finish()[0]
    assert record.t_end == 0.4
    assert len(record.best_crops) <= 2
    assert record.class_name == "car"


def test_synthetic_pipeline_writes_deterministic_artifacts(tmp_path):
    source = tmp_path / "synthetic_test_video.bin"
    source.write_bytes(b"synthetic_test_input")
    pipeline = OfflinePipeline(SyntheticDetector(), IoUTracker(match_thresh=0.1), SyntheticEncoder(), SyntheticCapture)
    first = pipeline.run(source, camera_id="cam01", output_dir=tmp_path / "runs", run_id="synthetic_test_run")
    assert first["status"] == "COMPLETED"
    root = Path(first["output_dir"])
    assert (root / "tracks.jsonl").is_file()
    assert (root / "tracklets.jsonl").is_file()
    assert (root / "embeddings.npy").is_file()
    assert (root / "run_manifest.json").is_file()
    assert np.allclose(np.load(root / "embeddings.npy"), np.array([[0.6, 0.8]], dtype=np.float32))
