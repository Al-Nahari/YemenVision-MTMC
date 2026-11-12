"""Acceptance smoke tests for the Phase 01 research package."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    ROOT / "README.md",
    ROOT / "literature_review" / "RESEARCH_REVIEW.md",
    ROOT / "dataset_catalog" / "DATASET_CATALOG.md",
    ROOT / "model_benchmarks" / "MODEL_BENCHMARK.md",
    ROOT / "system_architecture" / "SYSTEM_ARCHITECTURE.md",
    ROOT / "EXPERIMENTAL_ROADMAP.md",
    ROOT / "RESEARCH_GAPS.md",
    ROOT / "RISK_REGISTER.md",
    ROOT / "references" / "REFERENCES.bib",
    ROOT / "tools" / "environment_probe.py",
]


class Phase01ArtifactTests(unittest.TestCase):
    """Verify that the required foundation artifacts exist and are substantive."""

    def test_required_artifacts_exist(self) -> None:
        for path in REQUIRED:
            with self.subTest(path=path):
                self.assertTrue(path.is_file(), f"Missing artifact: {path}")
                self.assertGreater(path.stat().st_size, 200, f"Artifact is too small: {path}")

    def test_references_contain_verifiable_identifiers(self) -> None:
        bib = (ROOT / "references" / "REFERENCES.bib").read_text(encoding="utf-8")
        self.assertRegex(bib, r"10\.1109/CVPR\.2019\.00440")
        self.assertRegex(bib, r"10\.1109/TMM\.2020\.3014488")
        self.assertIn("https://www.aicitychallenge.org/", bib)

    def test_documents_state_no_local_results(self) -> None:
        review = (ROOT / "literature_review" / "RESEARCH_REVIEW.md").read_text(encoding="utf-8")
        self.assertIn("ليست نتائج YemenVision", review)
        self.assertIn("لا توجد في هذه الحزمة دعوى", review)

    def test_architecture_contains_privacy_and_abstention(self) -> None:
        architecture = (ROOT / "system_architecture" / "SYSTEM_ARCHITECTURE.md").read_text(encoding="utf-8")
        self.assertIn("privacy by design", architecture)
        self.assertIn("abstain", architecture)
        self.assertIn("RBAC", architecture)

    def test_no_obvious_secrets(self) -> None:
        text = "\n".join(path.read_text(encoding="utf-8") for path in REQUIRED)
        self.assertIsNone(re.search(r"(?i)(api[_ -]?key|secret|password)\s*[:=]\s*['\"]\S+", text))


if __name__ == "__main__":
    unittest.main()
