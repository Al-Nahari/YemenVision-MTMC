from __future__ import annotations
import pandas as pd
def camera_health(events,frequency='5min',missing_intervals=3):
 d=events.copy(); d.timestamp=pd.to_datetime(d.timestamp,utc=True); rows=[]
 for cam,g in d.groupby('camera_id'):
  index=pd.date_range(g.timestamp.min().floor(frequency),g.timestamp.max().ceil(frequency),freq=frequency,tz='UTC'); n=g.set_index('timestamp').resample(frequency).size().reindex(index,fill_value=0)
  gap=n.eq(0).rolling(missing_intervals).sum().ge(missing_intervals)
  rows.extend({'camera_id':cam,'timestamp':t,'event_count':int(n.loc[t]),'system_quality_anomaly':bool(gap.loc[t])} for t in index)
 return pd.DataFrame(rows)
def traffic_anomalies(metrics,z=3.):
 d=metrics.copy(); d['baseline_mean']=d.groupby('camera_id').vehicle_count.transform('mean'); d['baseline_std']=d.groupby('camera_id').vehicle_count.transform('std').replace(0,float('nan')); d['traffic_anomaly']=((d.vehicle_count-d.baseline_mean).abs()/d.baseline_std)>=z; return d
