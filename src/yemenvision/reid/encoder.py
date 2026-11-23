from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


@dataclass(frozen=True)
class ReIDModelSpec:
    backbone: str = "resnet50"
    size: tuple[int, int] = (224, 224)
    embedding_dim: int = 2048

class ReIDEncoder:
    """Exact BoT inference shape: ResNet feature map -> pool -> BNNeck -> L2.

    Uses ReIDNetV2 architecture (with GeM/AvgPool and BNNeck) to match the
    trained checkpoint structure from yemenvision_loaders.py.
    """
    def __init__(self, checkpoint: str | Path, device: str = "auto", flip_tta: bool = True) -> None:
        try:
            import torch
            import torch.nn.functional as F
            from torch import nn
            from torchvision import models, transforms
        except ImportError as exc:
            raise RuntimeError("ReID requires torch and torchvision; install yemenvision-mtmc[reid]") from exc
        self.torch = torch
        self._F = F
        self.device = self._resolve_device(device)
        ckpt = torch.load(Path(checkpoint), map_location="cpu", weights_only=False)
        cfg = ckpt.get("cfg")
        state = ckpt.get("state_dict")
        if not isinstance(cfg, dict) or not isinstance(state, dict):
            raise ValueError("ReID checkpoint must contain cfg and state_dict")

        backbone_name = cfg.get("backbone", "resnet50")
        size = tuple(cfg.get("size", (224, 224)))
        n_cls = int(cfg.get("n_cls", 2))
        last_stride = int(cfg.get("last_stride", 2))
        pool_type = cfg.get("pool", "avg")

        if backbone_name != "resnet50":
            raise ValueError(f"ReID checkpoint backbone must be resnet50, got {backbone_name}")
        if size != (224, 224):
            raise ValueError(f"ReID checkpoint size must be (224, 224), got {size}")

        # Build the same ReIDNetV2 architecture used during training
        class GeM(nn.Module):
            def __init__(self, p=3.0, eps=1e-6):
                super().__init__()
                self.p = nn.Parameter(torch.ones(1) * p)
                self.eps = eps
            def forward(self, x):
                return F.avg_pool2d(
                    x.clamp(min=self.eps).pow(self.p),
                    (x.size(-2), x.size(-1))
                ).pow(1.0 / self.p).flatten(1)

        base = models.resnet50(weights=None)
        if last_stride == 1:
            blk = base.layer4[0]
            if hasattr(blk, 'conv3'):
                blk.conv2.stride = (1, 1)
            else:
                blk.conv1.stride = (1, 1)
            blk.downsample[0].stride = (1, 1)

        dim = base.fc.in_features  # 2048
        self.embedding_dim = dim

        self.model = nn.Module()
        self.model.backbone = nn.Sequential(
            base.conv1, base.bn1, base.relu, base.maxpool,
            base.layer1, base.layer2, base.layer3, base.layer4,
        )
        self.model.pool = GeM() if pool_type == "gem" else nn.AdaptiveAvgPool2d(1)
        self.model.bn = nn.BatchNorm1d(dim)
        self.model.bn.bias.requires_grad_(False)
        self.model.classifier = nn.Linear(dim, n_cls, bias=False)

        required = {"backbone.", "bn."}
        if not all(any(k.startswith(prefix) for k in state) for prefix in required):
            raise ValueError("ReID checkpoint lacks required backbone or BNNeck keys; partial loading refused")
        missing, _unexpected = self.model.load_state_dict(state, strict=False)
        forbidden_missing = [k for k in missing if k.startswith(("backbone.", "bn.", "pool."))]
        if forbidden_missing:
            raise ValueError(f"invalid ReID checkpoint keys: missing={forbidden_missing}")
        self.model.to(self.device).eval()
        self.flip_tta = flip_tta
        self.transform = transforms.Compose([
            transforms.ToPILImage(), transforms.Resize(size), transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ])

    def _resolve_device(self, requested: str) -> Any:
        if requested != "auto":
            return self.torch.device(requested)
        return self.torch.device("cuda" if self.torch.cuda.is_available() else "cpu")

    def encode(self, crops: list[np.ndarray], batch_size: int = 32) -> np.ndarray:
        if not crops:
            return np.empty((0, self.embedding_dim), dtype=np.float32)
        outputs: list[np.ndarray] = []
        autocast = self.torch.autocast(device_type="cuda", dtype=self.torch.float16) if self.device.type == "cuda" else _nullcontext()
        with self.torch.inference_mode(), autocast:
            for start in range(0, len(crops), batch_size):
                batch_crops = crops[start:start + batch_size]
                tensors = self.torch.stack([self.transform(c) for c in batch_crops]).to(self.device)
                if self.flip_tta:
                    tensors = self._forward(tensors) + self._forward(self.torch.flip(tensors, dims=[3]))
                    vectors = self._F.normalize(tensors, dim=1)
                else:
                    vectors = self._F.normalize(self._forward(tensors), dim=1)
                outputs.append(vectors.detach().float().cpu().numpy())
        return np.concatenate(outputs, axis=0)

    def _forward(self, tensors: Any) -> Any:
        features = self.model.pool(self.model.backbone(tensors))
        if features.dim() > 2:
            features = features.flatten(1)
        return self.model.bn(features)

class _nullcontext:
    def __enter__(self): return self
    def __exit__(self, *args): return False
