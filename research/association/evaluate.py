"""Association metrics with abstentions; calculate by camera pair as well as aggregate."""
from __future__ import annotations
def metrics(decisions, truth):
 # truth maps (source camera/video/track, target camera/video/track) -> bool
 tp=fp=fn=0
 for d in decisions:
  key=((d.source.camera_id,d.source.video_id,d.source.local_track_id),(d.target.camera_id,d.target.video_id,d.target.local_track_id)); actual=truth.get(key,False); predicted=d.state=='accepted_candidate'
  tp+=predicted and actual; fp+=predicted and not actual; fn+=not predicted and actual
 precision=tp/(tp+fp) if tp+fp else 0.; recall=tp/(tp+fn) if tp+fn else 0.
 return {'precision':precision,'recall':recall,'f1':2*precision*recall/(precision+recall) if precision+recall else 0.,'false_match_rate':fp/(tp+fp) if tp+fp else 0.,'false_non_match_rate':fn/(tp+fn) if tp+fn else 0.,'tp':tp,'fp':fp,'fn':fn}
