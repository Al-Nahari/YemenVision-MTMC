from __future__ import annotations
import argparse, json, time
from pathlib import Path
import torch
from torchvision.io import read_image
from torchvision.transforms import v2
from .model import ReIDModel
def main():
 p=argparse.ArgumentParser(); p.add_argument('--checkpoint',required=True); p.add_argument('--images',nargs='+',required=True); p.add_argument('--output',default='runs/reid_embeddings.npz'); p.add_argument('--backbone',default='resnet50'); p.add_argument('--embedding-dim',type=int,default=512); a=p.parse_args()
 model=ReIDModel(a.backbone,a.embedding_dim); model.load_state_dict(torch.load(a.checkpoint,map_location='cpu')['model']); model.eval(); tfm=v2.Compose([v2.Resize((256,256)),v2.ToDtype(torch.float32,scale=True),v2.Normalize([.485,.456,.406],[.229,.224,.225])])
 started=time.perf_counter(); x=torch.stack([tfm(read_image(i)[:3]) for i in a.images]);
 with torch.no_grad(): z,_=model(x)
 import numpy as np; np.savez_compressed(a.output,embeddings=z.numpy(),images=a.images); print(json.dumps({'images':len(a.images),'seconds':time.perf_counter()-started,'output':a.output}))
if __name__=='__main__': main()
