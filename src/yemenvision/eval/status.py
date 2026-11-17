from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

class EvaluationStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_EVALUATED = "NOT_EVALUATED"

@dataclass(frozen=True)
class Result:
    name: str
    status: EvaluationStatus
    metrics: dict[str, float]
    reason: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {"name": self.name, "status": self.status.value, "metrics": self.metrics, "reason": self.reason}
