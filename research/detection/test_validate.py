import tempfile
import unittest
from pathlib import Path
from .validate import load_contract

class ContractTests(unittest.TestCase):
    def test_rejects_missing_root(self):
        with tempfile.TemporaryDirectory() as temp:
            config = Path(temp) / "data.yaml"
            config.write_text("path: absent\ntrain: train\nval: val\ntest: test\nnames: [car]\n")
            with self.assertRaises(ValueError): load_contract(str(config))

if __name__ == "__main__": unittest.main()
