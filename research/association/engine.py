"""Candidate filtering, optional evidence fusion, Hungarian matching and abstention."""
from __future__ import annotations
import hashlib
import numpy as np
from .contracts import Tracklet,AssociationDecision
class AssociationEngine:
 def __init__(self,topology, calibrated_model=None, accept=.90, low=.65, require_calibrated_transition=True):
  self.topology,self.model,self.accept,self.low,self.require_calibrated_transition=topology,calibrated_model,accept,low,require_calibrated_transition
 def evidence(self,a,b):
  transition=self.topology.transition(a.camera_id,b.camera_id)
  if not transition: return None,{'filter':'no_valid_camera_path'}
  elapsed=b.start_time-a.end_time
  if self.require_calibrated_transition and not transition.calibrated: return None,{'filter':'uncalibrated_transition'}
  if not transition.min_seconds<=elapsed<=transition.max_seconds: return None,{'filter':'impossible_travel_time','elapsed_seconds':elapsed}
  if a.vehicle_type!='unknown' and b.vehicle_type!='unknown' and a.vehicle_type!=b.vehicle_type: return None,{'filter':'conflicting_vehicle_type'}
  if a.quality!='usable' or b.quality!='usable': return None,{'filter':'insufficient_visual_evidence'}
  e={'elapsed_seconds':elapsed,'transition_probability':transition.probability,'appearance':None,'attribute_agreement':float(a.color==b.color) if a.color!='unknown' and b.color!='unknown' else None,'direction_agreement':float(a.direction==b.direction) if a.direction!='unknown' and b.direction!='unknown' else None}
  if a.embedding is not None and b.embedding is not None:
   x,y=np.asarray(a.embedding),np.asarray(b.embedding); e['appearance']=float(x@y/(np.linalg.norm(x)*np.linalg.norm(y)+1e-12))
  return e,e
 def score(self,e):
  if e.get('appearance') is None: return None
  if self.model is not None:
   features=[[e['appearance'],e.get('attribute_agreement') if e.get('attribute_agreement') is not None else .5,e.get('direction_agreement') if e.get('direction_agreement') is not None else .5,e.get('transition_probability') if e.get('transition_probability') is not None else .5]]
   return float(self.model.predict_proba(features)[0,1])
  return None # never call raw cosine a probability
 def decide(self,a,b):
  e,detail=self.evidence(a,b)
  if e is None: return AssociationDecision(a,b,'rejected' if detail['filter']!='insufficient_visual_evidence' else 'unknown',None,detail)
  p=self.score(e)
  if p is None:return AssociationDecision(a,b,'unknown',None,e)
  state='accepted_candidate' if p>=self.accept else ('low_confidence' if p>=self.low else 'rejected')
  group=None
  if state=='accepted_candidate': group='evt_'+hashlib.sha256(f'{a.camera_id}:{a.video_id}:{a.local_track_id}|{b.camera_id}:{b.video_id}:{b.local_track_id}'.encode()).hexdigest()[:16]
  return AssociationDecision(a,b,state,p,e,group)
 def match(self,sources,targets):
  try:
   from scipy.optimize import linear_sum_assignment
  except ImportError as exc:
   raise RuntimeError('Hungarian matching requires scipy; install requirements-phase06.txt') from exc
  decisions=[[self.decide(a,b) for b in targets] for a in sources]
  costs=np.array([[1-d.score if d.score is not None else 1e6 for d in row] for row in decisions]); rows,cols=linear_sum_assignment(costs)
  chosen={(r,c) for r,c in zip(rows,cols)}; out=[]
  for r,row in enumerate(decisions):
   viable=[d for d in row if d.state in {'accepted_candidate','low_confidence'}]
   for c,d in enumerate(row):
    if (r,c) in chosen: out.append(d)
    elif d.state=='accepted_candidate': out.append(AssociationDecision(d.source,d.target,'ambiguous',d.score,{**d.evidence,'reason':'not_selected_by_one_to_one_assignment'}))
  return out
