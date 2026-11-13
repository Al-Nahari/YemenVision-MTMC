from __future__ import annotations
from dataclasses import dataclass
import yaml
@dataclass(frozen=True)
class Transition:
 source:str; target:str; min_seconds:float; max_seconds:float; probability:float|None=None; calibrated:bool=False
class CameraTopology:
 def __init__(self,cameras,transitions): self.cameras,self.transitions=cameras,transitions
 @classmethod
 def load(cls,path):
  with open(path,encoding='utf-8') as f: d=yaml.safe_load(f) or {}
  return cls(d.get('cameras',{}),[Transition(**x) for x in d.get('transitions',[])])
 def transition(self,source,target): return next((x for x in self.transitions if x.source==source and x.target==target),None)
