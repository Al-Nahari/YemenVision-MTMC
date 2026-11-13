"""Deterministic local-ID tracker with lifecycle management and pluggable association."""
from __future__ import annotations
from dataclasses import dataclass
from .contracts import Detection, TrackEvent

def iou(a, b):
    x1,y1,x2,y2=map(float,a); X1,Y1,X2,Y2=map(float,b)
    inter=max(0,min(x2,X2)-max(x1,X1))*max(0,min(y2,Y2)-max(y1,Y1))
    union=(x2-x1)*(y2-y1)+(X2-X1)*(Y2-Y1)-inter
    return inter/union if union else 0.

@dataclass
class _Track:
    id: int; box: list[float]; cls: int; name: str; conf: float; hits: int=1; missed: int=0; state: str="tentative"
    velocity: tuple[float,float,float,float]=(0,0,0,0)
    def predict(self):
        self.box=[v+d for v,d in zip(self.box,self.velocity)]
    def update(self,d):
        old=self.box; self.box=list(d.xyxy); self.velocity=tuple(n-o for n,o in zip(self.box,old)); self.conf=d.confidence; self.hits+=1; self.missed=0

class TrackingEngine:
    """Baseline IoU+constant velocity lifecycle. IDs reset per engine/video instance."""
    def __init__(self, camera_id: str, video_id: str, iou_threshold=.3, min_hits=3, max_lost=30):
        self.camera_id, self.video_id = camera_id, video_id
        self.iou_threshold, self.min_hits, self.max_lost = iou_threshold, min_hits, max_lost
        self._tracks=[]; self._next_id=1
    def update(self, frame_index: int, detections: list[Detection]) -> list[TrackEvent]:
        for t in self._tracks: t.predict()
        candidates=sorted(((iou(t.box,d.xyxy),ti,di) for ti,t in enumerate(self._tracks) for di,d in enumerate(detections) if t.cls==d.class_id), reverse=True)
        used_t,used_d=set(),set()
        for score,ti,di in candidates:
            if score < self.iou_threshold or ti in used_t or di in used_d: continue
            t=self._tracks[ti]; reactivated=t.missed > 0; t.update(detections[di]); t.state="reactivated" if reactivated else ("confirmed" if t.hits>=self.min_hits else "tentative"); used_t.add(ti); used_d.add(di)
        for ti,t in enumerate(self._tracks):
            if ti not in used_t: t.missed+=1; t.state="lost"
        for di,d in enumerate(detections):
            if di not in used_d:
                created=_Track(self._next_id,list(d.xyxy),d.class_id,d.class_name,d.confidence)
                if self.min_hits <= 1: created.state="confirmed"
                self._tracks.append(created); self._next_id+=1
        # Suppress duplicate confirmed tracks of the same class; retain the more established one.
        duplicates=set()
        for a,t in enumerate(self._tracks):
            for b,u in enumerate(self._tracks[a+1:], a+1):
                if t.cls == u.cls and iou(t.box,u.box) > .85:
                    duplicates.add(b if (t.hits, -t.missed) >= (u.hits, -u.missed) else a)
        alive=[]; events=[]
        for index,t in enumerate(self._tracks):
            terminal=t.missed>self.max_lost or index in duplicates
            state="terminated" if terminal else t.state
            if t.state in {"confirmed", "reactivated"} or state in {"lost","terminated"}:
                events.append(TrackEvent(frame_index,self.camera_id,self.video_id,t.id,state,t.box,t.conf,t.cls,t.name))
            if not terminal: alive.append(t)
        self._tracks=alive
        return events
