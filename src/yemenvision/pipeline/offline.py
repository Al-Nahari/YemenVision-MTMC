from __future__ import annotations

from pathlib import Path
from typing import Any

class OfflinePipeline:
    """Dependency-injected pipeline shell; missing runtime dependencies fail explicitly."""
    def __init__(self, detector: Any, tracker: Any, encoder: Any | None = None) -> None:
        self.detector, self.tracker, self.encoder = detector, tracker, encoder

    def run(self, video_path: str | Path, *, camera_id: str, output_dir: str | Path) -> dict[str, Any]:
        path = Path(video_path)
        if not path.is_file():
            raise FileNotFoundError(f"Input video does not exist: {path}")
        try:
            import cv2
        except ImportError as exc:
            raise RuntimeError("Video processing requires opencv-python") from exc
        capture = cv2.VideoCapture(str(path))
        if not capture.isOpened():
            raise RuntimeError(f"Could not open video: {path}")
        frame_count = 0
        try:
            while True:
                ok, frame = capture.read()
                if not ok: break
                detections = self.detector.detect(frame)
                self.tracker.update(frame_count, detections)
                frame_count += 1
        finally:
            capture.release()
        return {"status": "COMPLETED", "camera_id": camera_id, "video": str(path), "frames_processed": frame_count, "output_dir": str(output_dir)}
