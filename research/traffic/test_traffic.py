import unittest
from datetime import datetime,timezone
from .contracts import TrafficEvent
from .metrics import aggregate_metrics
from .forecast import evaluate_walk_forward
class TestTraffic(unittest.TestCase):
 def test_unique_track_count(self):
  t=datetime(2026,1,1,tzinfo=timezone.utc); ev=[TrafficEvent('c',t,'car','n',7,.9,'entry'),TrafficEvent('c',t,'car','n',7,.8,'observed')]
  self.assertEqual(int(aggregate_metrics(ev,'1m').vehicle_count.iloc[0]),1)
 def test_walk_forward_no_zero_mape_crash(self): self.assertEqual(evaluate_walk_forward([0,1,0,2],2)['n_test'],2)
if __name__=='__main__': unittest.main()
