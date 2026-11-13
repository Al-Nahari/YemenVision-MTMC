import unittest
from .contracts import Detection
from .engine import TrackingEngine
class EngineTests(unittest.TestCase):
 def test_id_is_local_and_reactivates(self):
  d=Detection((0,0,10,10),.9,0,'car'); t=TrackingEngine('cam1','vid1',min_hits=1,max_lost=2)
  self.assertEqual(t.update(0,[d])[0].track_id,1)
  t.update(1,[]); e=t.update(2,[Detection((1,0,11,10),.9,0,'car')])
  self.assertEqual(e[0].track_id,1); self.assertEqual(e[0].state,'reactivated')
if __name__=='__main__': unittest.main()
