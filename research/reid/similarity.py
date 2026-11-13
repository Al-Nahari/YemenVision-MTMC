from __future__ import annotations
import numpy as np
from .contracts import MatchDecision
class SimilarityEngine:
 """Cosine retrieval plus held-out calibration. Cosine is never reported as probability."""
 def __init__(self, calibrator=None, likely=.90, ambiguous=.55): self.calibrator,self.likely,self.ambiguous=calibrator,likely,ambiguous
 def fit_calibrator(self, similarities, labels):
  from sklearn.linear_model import LogisticRegression
  self.calibrator=LogisticRegression().fit(np.asarray(similarities).reshape(-1,1),labels); return self
 def decide(self,a,b,quality_a='usable',quality_b='usable'):
  cosine=float(np.dot(a,b)/(np.linalg.norm(a)*np.linalg.norm(b)+1e-12))
  if quality_a!='usable' or quality_b!='usable': return MatchDecision('insufficient_visual_evidence',None,cosine,'crop quality is insufficient')
  if self.calibrator is None: return MatchDecision('unknown',None,cosine,'calibration is unavailable')
  p=float(self.calibrator.predict_proba([[cosine]])[0,1])
  label='likely_match' if p>=self.likely else ('ambiguous' if p>=self.ambiguous else 'unknown')
  return MatchDecision(label,p,cosine,'calibrated on held-out validation pairs')
