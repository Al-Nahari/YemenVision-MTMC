from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from yemenvision.registry import EXPECTED_CLASSES


@dataclass(frozen=True)
class Detection:
    class_id: int
    class_name: str
    confidence: float
    xyxy: tuple[float, float, float, float]

class VehicleDetector:
    def __init__(self, weights: str | Path, confidence: float = 0.25, iou: float = 0.45, imgsz: int = 640, device: str = "auto", amp: bool = True, allowed_classes: Iterable[str] | None = None) -> None:
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise RuntimeError("Detection requires ultralytics; install yemenvision-mtmc[detection]") from exc
        self.model = YOLO(str(weights))
        names = self.model.names
        actual = [names[i] for i in range(len(names))] if isinstance(names, dict) else list(names)
        if actual != EXPECTED_CLASSES:
            raise ValueError(f"Detector classes mismatch: expected 21-class contract, got {actual}")
        self.confidence, self.iou, self.imgsz, self.device, self.amp = confidence, iou, imgsz, device, amp
        self.allowed = set(allowed_classes) if allowed_classes else None

    def detect(self, frame: Any) -> list[Detection]:
        device = None if self.device == "auto" else self.device
        result = self.model.predict(frame, conf=self.confidence, iou=self.iou, imgsz=self.imgsz, device=device, amp=self.amp, verbose=False)[0]
        names = self.model.names
        detections = []
        for box, score, class_id in zip(result.boxes.xyxy.tolist(), result.boxes.conf.tolist(), result.boxes.cls.tolist()):
            cid = int(class_id); name = str(names[cid])
            if self.allowed is None or name in self.allowed:
                detections.append(Detection(cid, name, float(score), tuple(float(x) for x in box)))
        return detections
