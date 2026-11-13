"""Definitions: counts are unique local tracks entering a zone; flow=count/bin duration; occupancy=observed occupancy frames / usable frames."""
from __future__ import annotations
import pandas as pd
FREQUENCIES={'1m':'1min','5m':'5min','15m':'15min','1h':'1h','daily':'1D','weekly':'1W'}
def event_frame(events):
 rows=[e.to_dict() if hasattr(e,'to_dict') else e for e in events]; df=pd.DataFrame(rows)
 if df.empty:return df
 df['timestamp']=pd.to_datetime(df['timestamp'],utc=True); return df
def aggregate_metrics(events,frequency='5m'):
 df=event_frame(events)
 if df.empty:return df
 rule=FREQUENCIES[frequency]; df=df.sort_values('timestamp')
 # count detections/entries once per local track in each bin; no personal ID emitted.
 grouped=df.groupby([pd.Grouper(key='timestamp',freq=rule),'camera_id','vehicle_class','direction'],dropna=False)
 out=grouped.agg(vehicle_count=('local_track_id','nunique'),mean_detection_confidence=('detection_confidence','mean'),event_count=('event_id','count')).reset_index()
 seconds=pd.Timedelta(rule).total_seconds() if rule not in {'1D','1W'} else (86400 if rule=='1D' else 604800)
 out['flow_vehicles_per_hour']=out.vehicle_count*3600/seconds
 out['quality_flagged_events']=grouped.quality_flags.apply(lambda x:sum(bool(v) for v in x)).to_numpy()
 return out
def occupancy(frame_observations):
 """Input columns camera_id,timestamp,occupied,usable. Unknown frames are excluded."""
 d=frame_observations.copy(); d=d[d.usable.astype(bool)]; return d.groupby('camera_id').occupied.mean().rename('occupancy').reset_index()
def peak_periods(metrics,quantile=.9):
 threshold=metrics.vehicle_count.quantile(quantile); return metrics[metrics.vehicle_count>=threshold].copy()
