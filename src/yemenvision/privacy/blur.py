from __future__ import annotations

from typing import Any

def blur_plates(frame: Any, boxes: list[tuple[int, int, int, int]]) -> Any:
    """Blur explicitly supplied plate boxes; no OCR or plate detection is implied."""
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("Plate blur requires opencv-python") from exc
    output = frame.copy()
    for x1, y1, x2, y2 in boxes:
        crop = output[max(0, y1):max(0, y2), max(0, x1):max(0, x2)]
        if crop.size:
            output[max(0, y1):max(0, y2), max(0, x1):max(0, x2)] = cv2.GaussianBlur(crop, (31, 31), 0)
    return output
