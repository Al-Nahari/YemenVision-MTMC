"""Probe local compute/runtime capabilities without assuming a GPU or CUDA version."""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def run_command(command: list[str]) -> str | None:
    """Run a lightweight command and return stdout, or None when unavailable."""
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    output = completed.stdout.strip()
    return output or None


def probe_torch() -> dict[str, Any]:
    """Collect optional PyTorch and CUDA information."""
    try:
        import torch  # type: ignore
    except ImportError:
        return {"installed": False}

    result: dict[str, Any] = {
        "installed": True,
        "version": torch.__version__,
        "cuda_available": bool(torch.cuda.is_available()),
    }
    if torch.cuda.is_available():
        result["cuda_version"] = torch.version.cuda
        result["device_count"] = torch.cuda.device_count()
        result["devices"] = [
            {
                "index": index,
                "name": torch.cuda.get_device_name(index),
                "capability": torch.cuda.get_device_capability(index),
                "memory_bytes": torch.cuda.get_device_properties(index).total_memory,
            }
            for index in range(torch.cuda.device_count())
        ]
    return result


def build_report() -> dict[str, Any]:
    """Build a JSON-serializable environment report."""
    return {
        "python": sys.version,
        "executable": sys.executable,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "cpu_count": __import__("os").cpu_count(),
        "ram_bytes": None,
        "git": shutil.which("git"),
        "nvidia_smi": run_command(["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"]),
        "torch": probe_torch(),
        "notes": [
            "This is an observation of the current environment, not a training result.",
            "Install optional resource readers only if the project policy allows them.",
        ],
    }


def main() -> None:
    """Write the environment report to JSON."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("reports/environment_probe.json"))
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(build_report(), indent=2), encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
