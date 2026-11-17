from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .status import EvaluationStatus, Result


def build_evaluation_report(*, output_dir: str | Path, reid_result: Result | None = None,
                            association_result: Result | None = None,
                            detector_result: Result | None = None,
                            mot_result: Result | None = None) -> dict[str, Any]:
    results = [result for result in (detector_result, reid_result, association_result, mot_result) if result is not None]
    if not results:
        results = [Result("evaluation", EvaluationStatus.NOT_EVALUATED, {}, "No evaluation datasets were supplied")]
    payload = {"results": [result.as_dict() for result in results],
               "status": "PASS" if all(result.status == EvaluationStatus.PASS for result in results) else
                         "FAIL" if any(result.status == EvaluationStatus.FAIL for result in results) else "NOT_EVALUATED"}
    root = Path(output_dir); root.mkdir(parents=True, exist_ok=True)
    (root / "eval_report.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    lines = [f"# Evaluation report\n\nStatus: **{payload['status']}**\n"]
    for result in payload["results"]:
        lines.append(f"## {result['name']} — {result['status']}\n")
        if result.get("reason"): lines.append(f"Reason: {result['reason']}\n")
        if result.get("metrics"): lines.append("```json\n" + json.dumps(result["metrics"], indent=2) + "\n```\n")
    (root / "eval_report.md").write_text("\n".join(lines), encoding="utf-8")
    return payload
