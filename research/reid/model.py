"""Backbone factory with L2-normalized embedding head."""
from __future__ import annotations
import torch
from torch import nn
class ReIDModel(nn.Module):
 def __init__(self, backbone='resnet50', embedding_dim=512, num_ids=0):
  super().__init__(); import torchvision.models as models
  if backbone=='resnet50': net=models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V2); dim=net.fc.in_features; net.fc=nn.Identity()
  elif backbone=='resnet18': net=models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1); dim=net.fc.in_features; net.fc=nn.Identity()
  else: raise ValueError('Supported built-in backbones: resnet18, resnet50. Use DINOv2 only after approved weight provenance.')
  self.backbone=net; self.embed=nn.Linear(dim,embedding_dim); self.classifier=nn.Linear(embedding_dim,num_ids) if num_ids else None
 def forward(self,x):
  z=torch.nn.functional.normalize(self.embed(self.backbone(x)),dim=1)
  return z, (self.classifier(z) if self.classifier else None)
def batch_hard_triplet(embeddings, labels, margin=.3):
 import torch
 dist=1-embeddings@embeddings.T; same=labels[:,None].eq(labels[None,:]); same.fill_diagonal_(False)
 hardest_pos=dist.masked_fill(~same,-1).max(1).values; hardest_neg=dist.masked_fill(same,1e9).min(1).values
 return torch.relu(hardest_pos-hardest_neg+margin).mean()
