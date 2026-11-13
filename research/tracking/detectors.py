from __future__ import annotations
from .contracts import Detection
class UltralyticsDetector:
    """Adapter; any detector only needs to implement detect(frame)."""
    def __init__(self, weights: str, conf: float = .25, imgsz: int = 960):
        from ultralytics import YOLO
        self.model, self.conf, self.imgsz = YOLO(weights), conf, imgsz
    def detect(self, frame):
        result = self.model.predict(frame, conf=self.conf, imgsz=self.imgsz, verbose=False)[0]
        names = result.names
        for b in result.boxes:
            yield Detection(tuple(map(float, b.xyxy[0].tolist())), float(b.conf[0]), int(b.cls[0]), str(names[int(b.cls[0])]))
