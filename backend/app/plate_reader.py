"""Lazy, CPU-friendly license-plate OCR used only by video inference.

The engine is imported on first use so the API still boots on machines without
the optional ``rapidocr-onnxruntime`` dependency. Recognition is heuristic: it
reads the lower portion of a vehicle box, which works for front/rear plates in
typical traffic camera footage. When OCR is unavailable the pipeline keeps
working and records ``ocr_unavailable`` instead of inventing plate text.
"""
import logging
import threading
from typing import Any

LOGGER = logging.getLogger(__name__)

_ENGINE: Any | None = None
_ENGINE_READY = False
_ENGINE_AVAILABLE = False
_LOCK = threading.Lock()


def engine_status() -> dict[str, Any]:
    return {'loaded': _ENGINE_READY, 'available': _ENGINE_AVAILABLE,
            'engine': 'rapidocr-onnxruntime' if _ENGINE_AVAILABLE else None}


def _get_engine() -> Any | None:
    global _ENGINE, _ENGINE_READY, _ENGINE_AVAILABLE
    if _ENGINE_READY:
        return _ENGINE
    with _LOCK:
        if _ENGINE_READY:
            return _ENGINE
        try:
            from rapidocr_onnxruntime import RapidOCR
            _ENGINE = RapidOCR()
            _ENGINE_AVAILABLE = True
            LOGGER.info('Plate OCR engine loaded')
        except Exception as exc:  # optional dependency or model download failure
            LOGGER.warning('Plate OCR unavailable: %s', exc)
            _ENGINE = None
            _ENGINE_AVAILABLE = False
        _ENGINE_READY = True
    return _ENGINE


def _normalize(text: str) -> str | None:
    cleaned = ''.join(char for char in text.upper() if char.isalnum()).strip()
    if not 4 <= len(cleaned) <= 12:
        return None
    if sum(char.isdigit() for char in cleaned) < 2:
        return None
    return cleaned


def _ocr_crop(engine: Any, crop: Any, min_confidence: float) -> dict[str, Any] | None:
    with _LOCK:
        try:
            output = engine(crop)
        except Exception as exc:
            LOGGER.warning('Plate OCR failed on one crop: %s', exc)
            return None
    candidates = output[0] if isinstance(output, tuple) else output
    if not candidates:
        return None
    best: dict[str, Any] | None = None
    for candidate in candidates:
        try:
            raw_text = str(candidate[1])
            score = float(candidate[2])
        except (IndexError, TypeError, ValueError):
            continue
        text = _normalize(raw_text)
        if not text or score < min_confidence:
            continue
        if best is None or score > best['confidence']:
            best = {'text': text, 'confidence': round(score, 3), 'engine': 'rapidocr'}
    return best


def read_plate(frame: Any, box: list[float], min_confidence: float = 0.55) -> dict[str, Any] | None:
    """Return the best plate reading from a vehicle crop, or ``None``.

    ``frame`` is a BGR OpenCV array and ``box`` is ``[x1, y1, x2, y2]`` in the
    same coordinate space. The lower part of the box is tried first; the full
    box is a bounded fallback for plates that sit higher on the vehicle.
    """
    engine = _get_engine()
    if engine is None:
        return None
    import cv2

    x1, y1, x2, y2 = (int(round(value)) for value in box)
    height, width = frame.shape[:2]
    x1, x2 = max(0, x1), min(width, x2)
    y1, y2 = max(0, y1), min(height, y2)
    if x2 - x1 < 12 or y2 - y1 < 6:
        return None

    plate_top = y1 + int(0.45 * (y2 - y1))
    crops = [frame[plate_top:y2, x1:x2]]
    crops.append(frame[y1:y2, x1:x2])
    for crop in crops:
        if crop.size == 0:
            continue
        enlarged = cv2.resize(crop, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_CUBIC)
        reading = _ocr_crop(engine, enlarged, min_confidence)
        if reading:
            return reading
    return None
