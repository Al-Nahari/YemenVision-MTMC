# Models

Weights are user-provided, read-only artifacts. Set `YV_MODELS_DIR` or use `models/`. The registry rejects inference checkpoints named `*_last.pt`, synthetic `reid_attr_*` checkpoints, and ReID checkpoints that do not contain both the ResNet backbone and BNNeck keys.

The detector class order is fixed and validated at runtime against `model.names`. A mismatch is an error, not a silent remapping. The production ReID output is 2048 dimensions after BNNeck and L2 normalization, with 224x224 ImageNet preprocessing and optional flip-TTA.

No weight is included in this repository. Without weights, `yv check-models` returns a non-zero status and all model-dependent evaluation is `NOT_EVALUATED`.
