"""Standard cross-camera CMC/mAP computation; query/gallery identity overlap is expected, split overlap is not."""
from __future__ import annotations
import numpy as np
def evaluate(query_embeddings, query_ids, query_cams, gallery_embeddings, gallery_ids, gallery_cams, ranks=(1,5,10)):
 q=np.asarray(query_embeddings); g=np.asarray(gallery_embeddings); q/=np.linalg.norm(q,axis=1,keepdims=True); g/=np.linalg.norm(g,axis=1,keepdims=True)
 cmc=np.zeros(max(ranks)); aps=[]
 for i,scores in enumerate(q@g.T):
  order=np.argsort(-scores); valid=np.array([(gallery_ids[j]!=query_ids[i] or gallery_cams[j]!=query_cams[i]) for j in order])
  matches=np.array([gallery_ids[j]==query_ids[i] for j in order])[valid]
  if not matches.any(): continue
  cmc+=np.maximum.accumulate(matches); precision=np.cumsum(matches)/(np.arange(len(matches))+1); aps.append(float((precision*matches).sum()/matches.sum()))
 return {'mAP':float(np.mean(aps)) if aps else float('nan'), **{f'Rank-{r}':float(cmc[r-1]/len(aps)) if aps else float('nan') for r in ranks}, 'valid_queries':len(aps)}
