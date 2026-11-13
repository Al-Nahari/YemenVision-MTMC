"""Manifest validation and pair construction with identity-disjoint splits."""
from __future__ import annotations
import csv
from collections import defaultdict
from .contracts import ReIDSample
REQUIRED={'image','identity_id','camera_id','split'}
def load_manifest(path):
 with open(path,encoding='utf-8',newline='') as f: rows=list(csv.DictReader(f))
 if not rows or not REQUIRED.issubset(rows[0]): raise ValueError(f'Manifest requires {sorted(REQUIRED)}')
 samples=[ReIDSample(**{k:(r.get(k) or 'unknown') for k in ReIDSample.__dataclass_fields__}) for r in rows]
 ids=defaultdict(set)
 for s in samples: ids[s.identity_id].add(s.split)
 leakage={i:v for i,v in ids.items() if len(v)>1}
 if leakage: raise ValueError(f'Identity leakage across splits: {list(leakage)[:5]}')
 return samples
def build_pairs(samples):
 """Positive cross-camera pairs and hard candidates (same type/color) without test leakage."""
 positives=[]; negatives=[]
 for i,a in enumerate(samples):
  for b in samples[i+1:]:
   if a.split != b.split: continue
   if a.identity_id==b.identity_id and a.camera_id!=b.camera_id: positives.append((a,b,1,'cross_camera_positive'))
   elif a.identity_id!=b.identity_id:
    hard=a.vehicle_type!='unknown' and a.vehicle_type==b.vehicle_type and a.color!='unknown' and a.color==b.color
    negatives.append((a,b,0,'hard_negative' if hard else 'negative'))
 return positives,negatives
