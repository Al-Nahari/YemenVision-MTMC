from __future__ import annotations
from .metrics import aggregate_metrics,event_frame,occupancy,peak_periods
from .quality import camera_health,traffic_anomalies
from .forecast import evaluate_walk_forward
class TrafficIntelligenceEngine:
 """Backend-facing façade; raw event ledger remains the source of truth."""
 def metrics(self,events,frequency='5m'): return aggregate_metrics(events,frequency)
 def dashboard_payload(self,events,frequency='5m'):
  raw=event_frame(events); m=self.metrics(events,frequency)
  return {'metrics':m.to_dict('records'),'peaks':peak_periods(m).to_dict('records') if not m.empty else [],'camera_health':camera_health(raw).to_dict('records') if not raw.empty else [],'definitions':{'flow':'unique local tracks per bin converted to vehicles/hour','occupancy':'occupied usable frames / usable frames','density':'not reported unless calibrated road length/area is supplied','queue_length':'not reported unless zone geometry/calibration is supplied','travel_time':'only aggregate accepted temporary event groups; never individual identity'}}
 def forecast_evaluation(self,series,initial_train): return evaluate_walk_forward(series,initial_train)
