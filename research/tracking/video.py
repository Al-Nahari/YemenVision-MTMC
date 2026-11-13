"""Video runner, unified JSONL event export, and visual diagnostics."""
from __future__ import annotations
import argparse, json, time
from pathlib import Path
import cv2
from .engine import TrackingEngine
from .detectors import UltralyticsDetector

def draw(frame, events, trajectories):
    for e in events:
        x1,y1,x2,y2=map(int,e.xyxy); color=(0,200,0) if e.state=="confirmed" else (0,170,255)
        cv2.rectangle(frame,(x1,y1),(x2,y2),color,2); cv2.putText(frame,f"{e.class_name} #{e.track_id} {e.confidence:.2f} [{e.state}]",(x1,max(20,y1-6)),cv2.FONT_HERSHEY_SIMPLEX,.45,color,1)
        trajectories.setdefault(e.track_id,[]).append(((x1+x2)//2,(y1+y2)//2))
        pts=trajectories[e.track_id][-50:]
        if len(pts)>1: cv2.polylines(frame,[__import__('numpy').array(pts)],False,color,2)
    return frame
def main():
    p=argparse.ArgumentParser(); p.add_argument("--weights",required=True); p.add_argument("--source",required=True); p.add_argument("--camera-id",required=True); p.add_argument("--video-id",required=True); p.add_argument("--output",default="runs/tracking"); p.add_argument("--conf",type=float,default=.25); p.add_argument("--iou",type=float,default=.3); p.add_argument("--min-hits",type=int,default=3); p.add_argument("--max-lost",type=int,default=30)
    a=p.parse_args(); out=Path(a.output); out.mkdir(parents=True,exist_ok=True)
    cap=cv2.VideoCapture(a.source); fps=cap.get(cv2.CAP_PROP_FPS) or 30; w,h=int(cap.get(3)),int(cap.get(4)); writer=cv2.VideoWriter(str(out/'diagnostic.mp4'),cv2.VideoWriter_fourcc(*'mp4v'),fps,(w,h))
    detector=UltralyticsDetector(a.weights,a.conf); tracker=TrackingEngine(a.camera_id,a.video_id,a.iou,a.min_hits,a.max_lost); history={}; frame=0; started=time.perf_counter()
    with (out/'events.jsonl').open('w',encoding='utf-8') as f:
        while True:
            ok,image=cap.read()
            if not ok: break
            events=tracker.update(frame,list(detector.detect(image)))
            for event in events: f.write(json.dumps(event.to_dict())+'\n')
            writer.write(draw(image,events,history)); frame+=1
    cap.release(); writer.release(); elapsed=time.perf_counter()-started
    (out/'run.json').write_text(json.dumps({'frames':frame,'seconds':elapsed,'processing_fps':frame/elapsed if elapsed else 0,'camera_id':a.camera_id,'video_id':a.video_id,'id_scope':'local_camera_video'},indent=2))
if __name__=='__main__': main()
