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
    """Exact BoT inference shape: ResNet feature map -> pool -> BNNeck -> L2."""
    def __init__(self, checkpoint: str | Path, device: str = "auto", flip_tta: bool = True) -> None:
        try:
            import torch
            from torch import nn
            from torchvision import models, transforms
        except ImportError as exc:
            raise RuntimeError("ReID requires torch and torchvision; install yemenvision-mtmc[reid]") from exc
        self.torch = torch
        self.device = self._resolve_device(device)
        ckpt = torch.load(Path(checkpoint), map_location="cpu", weights_only=False)
        cfg = ckpt.get("cfg")
        state = ckpt.get("state_dict")
        if not isinstance(cfg, dict) or not isinstance(state, dict):
            raise ValueError("ReID checkpoint must contain cfg and state_dict")
        if cfg.get("backbone") != "resnet50" or tuple(cfg.get("size", ())) != (224, 224):
            raise ValueError("ReID checkpoint cfg must be resnet50 with size (224, 224)")
        base = models.resnet50(weights=None)
        self.model = nn.Module()
        self.model.backbone = nn.Sequential(*list(base.children())[:-2])
        self.model.pool = nn.AdaptiveAvgPool2d(1)
        self.embedding_dim = int(cfg.get("embedding_dim", 2048))
        if self.embedding_dim != 2048:
            raise ValueError("This checkpoint contract requires a 2048-dimensional ResNet50 feature")
        self.model.bn = nn.BatchNorm1d(self.embedding_dim)
        self.model.classifier = nn.Linear(self.embedding_dim, int(cfg.get("n_cls", 576)))
        required = {"backbone.", "bn."}
        if not all(any(k.startswith(prefix) for k in state) for prefix in required):
            raise ValueError("ReID checkpoint lacks required backbone or BNNeck keys; partial loading refused")
        missing, unexpected = self.model.load_state_dict(state, strict=False)
        forbidden_missing = [k for k in missing if k.startswith(("backbone.", "bn."))]
        if forbidden_missing or unexpected:
            raise ValueError(f"invalid ReID checkpoint keys: missing={forbidden_missing}, unexpected={unexpected}")
        self.model.to(self.device).eval()
        self.flip_tta = flip_tta
        size = tuple(cfg.get("size", (224, 224)))
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
                    vectors = self.torch.nn.functional.normalize(tensors, dim=1)
                else:
                    vectors = self.torch.nn.functional.normalize(self._forward(tensors), dim=1)
                outputs.append(vectors.detach().float().cpu().numpy())
        return np.concatenate(outputs, axis=0)

    def _forward(self, tensors: Any) -> Any:
        features = self.model.pool(self.model.backbone(tensors)).flatten(1)
        return self.model.bn(features)

class _nullcontext:
    def __enter__(self): return self
    def __exit__(self, *args): return False
