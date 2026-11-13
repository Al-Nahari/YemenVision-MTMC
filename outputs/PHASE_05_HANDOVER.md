# Phase 05 handover

Delivered: identity-leakage-checked ReID manifest tooling, pair preparation, a normalized embedding model, batch-hard triplet loss, extractor, retrieval index with access/retention controls, calibrated similarity decisions, standard CMC/mAP evaluator, five notebooks, and a model card.

The output labels are `likely_match`, `ambiguous`, `unknown`, and `insufficient_visual_evidence`; they are not identity claims. No model or metric has been fabricated because the workspace contains no identity-labelled data or approved weights.

Before experimentation: validate external code/weights and licenses; create identity-disjoint splits; calibrate on validation pairs only; then measure FMR/FNMR and Rank-k/mAP on unseen identities/cameras.
