"""Time-ordered baselines and walk-forward evaluation; never creates future-leaking features."""
from __future__ import annotations
import numpy as np
def moving_average(history,window=3): return float(np.mean(history[-window:])) if len(history) else 0.
def seasonal_naive(history,season=24): return float(history[-season]) if len(history)>=season else moving_average(history)
def evaluate_walk_forward(values,initial_train,forecaster=seasonal_naive):
 actual=[]; pred=[]
 for i in range(initial_train,len(values)):
  pred.append(forecaster(values[:i])); actual.append(values[i])
 a=np.asarray(actual); p=np.asarray(pred); err=a-p
 return {'mae':float(np.mean(abs(err))),'rmse':float(np.sqrt(np.mean(err**2))),'wape':float(abs(err).sum()/max(abs(a).sum(),1e-12)),'smape':float(np.mean(2*abs(err)/(abs(a)+abs(p)+1e-12))),'mape_nonzero':float(np.mean(abs(err[a!=0]/a[a!=0]))) if (a!=0).any() else None,'n_test':len(a)}
