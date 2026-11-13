"""Scope gate and append-only audit. No cross-site/global exploration."""
from __future__ import annotations
import json,time
from pathlib import Path
class AssociationAccess:
 def __init__(self,allowed_cameras,expires_at,audit_path): self.allowed=set(allowed_cameras); self.expires_at=expires_at; self.audit=Path(audit_path)
 def authorize(self,source,target,purpose,actor):
  ok=time.time()<=self.expires_at and source.camera_id in self.allowed and target.camera_id in self.allowed
  self.audit.parent.mkdir(parents=True,exist_ok=True)
  with self.audit.open('a',encoding='utf-8') as f: f.write(json.dumps({'at':time.time(),'actor':actor,'purpose':purpose,'source_camera':source.camera_id,'target_camera':target.camera_id,'allowed':ok})+'\n')
  if not ok: raise PermissionError('Association blocked: camera scope or retention period is invalid')
