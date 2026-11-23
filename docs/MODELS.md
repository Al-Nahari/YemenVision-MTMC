# Model contract and registry

YemenVision never downloads or overwrites model weights. The registry in
`src/yemenvision/registry/registry.py` discovers `.pt` files, hashes them, and
checks them against `models/manifest.json` before a production component is
allowed to load them.

## Class contract

Every detector must expose exactly these 21 names, in this order:

```
ambulance, army vehicle, auto rickshaw, bicycle, bus, car, garbagevan,
human hauler, minibus, minivan, motorbike, pickup, policecar, rickshaw,
scooter, suv, taxi, three wheelers -CNG-, truck, van, wheelbarrow
```

A checkpoint with a different label space is rejected. The former silent
fallback to an 80-class COCO model has been removed.

## Manifest

`models/manifest.json` is the local trust root:

```json
{
  "models": {
    "detector_best.pt": {"sha256": "<promoted sha256>", "kind": "detector"},
    "reid_best.pt": {"sha256": "<promoted sha256>", "kind": "reid"}
  },
  "revoked": {
    "reid_best.pt": "reason this file must not be loaded"
  }
}
```

Rules:

- A file whose SHA-256 does not match `models.<name>.sha256` is invalid.
- A file listed under `revoked` is invalid even if its hash matches.
- `trusted_models_only=true` (the production default) refuses any checkpoint
  without a matching manifest hash.
- A truncated PyTorch archive is reported as a corrupted checkpoint before
  `torch.load` is attempted.
- `*_last.pt` files are never accepted for inference.

`models/production_manifest.json` records the promoted artifact set and the
reason for any revocation. Both manifests must agree on the promoted hash; the
local `manifest.json` may also record the observed local hash for diagnosis.

## Current local status (2026-11-22)

| File | SHA-256 matches manifest | Usable | Notes |
|---|---|---|---|
| `detector_best.pt` | yes | no in this shell | Valid ZIP/hash, but checkpoint validation needs a working OpenCV runtime (`cv2`). |
| `reid_best.pt` | no | **no** | Local file is truncated (not a ZIP) and is revoked in both manifests. Do not report ReID or MTMC results from it. |
| `vehicle_attributes.pt` | yes | auxiliary | Attribute model only; not a production ReID encoder. |

The ReID checkpoint must be re-exported from the promoted artifact
(`956b55a3...`) or a newly evaluated model, hashed, and promoted through the
manifest before ReID or MTMC evaluation can run.

## Commands

```powershell
# Discover and validate everything (non-zero exit on any ERROR)
$env:YV_MODELS_DIR = "models"
yv check-models

# Require a matching manifest hash for every file
yv check-models --trusted-models-only

# Machine-readable output for CI or a baseline report
yv check-models --json
```

The backend exposes the same registry state at `GET /api/v1/models` and refuses
to start inference when no verified detector is available (`503`).

## Security

PyTorch checkpoints are executable pickle containers. Only load checkpoints
that are trusted by hash, keep the models directory read-only in production, and
never accept a user-uploaded checkpoint as a model.
