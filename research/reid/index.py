"""Small local vector index with explicit access scope and expiry metadata."""
from __future__ import annotations
import json, time
from pathlib import Path
import numpy as np
class FeatureIndex:
 def __init__(self, embeddings, records, access_scope, expires_at):
  self.x=np.asarray(embeddings,dtype='float32'); self.x/=np.linalg.norm(self.x,axis=1,keepdims=True).clip(1e-12); self.records=records; self.access_scope=access_scope; self.expires_at=expires_at
 def search(self, embedding,k=10):
  if time.time()>self.expires_at: raise PermissionError('Feature index expired; rebuild under retention policy')
  v=np.asarray(embedding,dtype='float32'); v/=max(np.linalg.norm(v),1e-12); ids=np.argsort(-(self.x@v))[:k]
  return [{'record':self.records[int(i)],'cosine_similarity':float(self.x[i]@v)} for i in ids]
 def save(self,path):
  p=Path(path); np.savez_compressed(p,embeddings=self.x); p.with_suffix('.json').write_text(json.dumps({'records':self.records,'access_scope':self.access_scope,'expires_at':self.expires_at}))
