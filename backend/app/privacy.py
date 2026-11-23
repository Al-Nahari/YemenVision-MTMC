"""Privacy redaction for saved visual output.

The project policy is fail-closed for unblurred imagery. Until a dedicated
plate detector is wired in, this module applies a conservative heuristic:
blur the lower part of every vehicle box (where plates normally appear), or
the whole vehicle box when ``YV_PRIVACY_BLUR_MODE=vehicle``.
"""
from __future__ import annotations

import logging
from collections.abc import Iterable
from typing import Any

from app.config import settings

LOGGER = logging.getLogger(__name__)
_warned = False


def _regions(box: Iterable[float], width: int, height: int) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = (float(value) for value in box)
    # Plates are usually in the lower half of a vehicle. Blur from 55% of the
    # box height down to the bottom, with a small margin, unless the whole
    # vehicle is being redacted.
    top = y1 if settings.blur_mode == 'vehicle' else y1 + (y2 - y1) * 0.55
    left = max(0, round(x1))
    right = min(width, round(x2))
    upper = max(0, round(top))
    lower = min(height, round(y2))
    return left, upper, right, lower


def redact_frame(frame: Any, vehicle_boxes: Iterable[Iterable[float]]) -> Any:
    """Return a frame with plate/vehicle regions blurred in place.

    The caller must provide the same boxes that will be drawn on the frame.
    """
    global _warned
    if not settings.blur_plates or settings.blur_mode == 'off':
        if settings.allow_unblurred_output and not _warned:
            LOGGER.warning('Unblurred visual output is explicitly enabled; review the privacy policy')
            _warned = True
        return frame

    import cv2

    height, width = frame.shape[:2]
    boxes = list(vehicle_boxes)
    if not boxes:
        # Fail closed: without a detection we do not know where a plate is, so
        # the only safe frame is a fully redacted one. This is intentionally
        # conservative and keeps "no unblurred saved media" true even on misses.
        frame[:] = cv2.GaussianBlur(frame, (31, 31), 0)
        return frame
    for box in boxes:
        left, upper, right, lower = _regions(box, width, height)
        if right <= left or lower <= upper:
            continue
        region = frame[upper:lower, left:right]
        if region.size:
            frame[upper:lower, left:right] = cv2.GaussianBlur(region, (31, 31), 0)
    return frame
