import tempfile, unittest
from pathlib import Path
import numpy as np
from .data import load_manifest
from .similarity import SimilarityEngine
class ReIDTests(unittest.TestCase):
 def test_reject_identity_leakage(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'m.csv'; p.write_text('image,identity_id,camera_id,split\na.jpg,1,c1,train\nb.jpg,1,c2,test\n')
   with self.assertRaises(ValueError): load_manifest(p)
 def test_cosine_not_probability_without_calibration(self):
  result=SimilarityEngine().decide(np.array([1.,0]),np.array([1.,0]))
  self.assertEqual(result.label,'unknown'); self.assertIsNone(result.calibrated_probability)
if __name__=='__main__': unittest.main()
