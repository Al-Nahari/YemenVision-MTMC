from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class PlateDetector(Protocol):
    """Optional plate detector plugin; it must return xyxy boxes."""

    def detect(self, frame: Any) -> list[tuple[int, int, int, int]]: ...


class NullPlateDetector:
    enabled = False

    def detect(self, frame: Any) -> list[tuple[int, int, int, int]]:
        del frame
        return []


@dataclass(frozen=True)
class PrivacyDecision:
    allowed: bool
    blurred: bool
    warning: str | None = None


def check_visual_output(*, blur_plates: bool, allow_unblurred_output: bool,
                        plate_detector: PlateDetector | None = None) -> PrivacyDecision:
    """Fail closed when no plate detector exists and unblurred output is not explicit."""
    if blur_plates and plate_detector is not None and getattr(plate_detector, "enabled", True):
        return PrivacyDecision(True, True)
    if allow_unblurred_output:
        return PrivacyDecision(True, False, "unblurred output explicitly enabled; review privacy policy")
    return PrivacyDecision(False, False, "no plate detector is configured; refusing unblurred visual output")
