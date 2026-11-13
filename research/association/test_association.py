import unittest
from .contracts import Tracklet
from .topology import CameraTopology,Transition
from .engine import AssociationEngine
class TestAssociation(unittest.TestCase):
 def test_uncalibrated_path_abstains(self):
  topo=CameraTopology({},[Transition('a','b',1,10,.5,False)]); e=AssociationEngine(topo)
  a=Tracklet(1,'a','v',0,2,[1.,0.],quality='usable'); b=Tracklet(1,'b','v',5,6,[1.,0.],quality='usable')
  self.assertEqual(e.decide(a,b).state,'rejected')
 def test_calibrated_needs_probability_model(self):
  topo=CameraTopology({},[Transition('a','b',1,10,.5,True)]); e=AssociationEngine(topo)
  a=Tracklet(1,'a','v',0,2,[1.,0.],quality='usable'); b=Tracklet(1,'b','v',5,6,[1.,0.],quality='usable')
  self.assertEqual(e.decide(a,b).state,'unknown')
if __name__=='__main__': unittest.main()
