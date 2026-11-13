# Vehicle ReID model card

## Intended use

Rank visual similarity among authorized vehicle crops and express calibrated uncertainty. An embedding or match score is **not proof of vehicle identity** and is not a cross-camera identity record.

## Data and leakage guard

The manifest loader requires `identity_id`, `camera_id`, and `split`, and rejects any identity shared across train/validation/test. Positive evaluation pairs must cross cameras when testing cross-camera retrieval.

## Calibration

Cosine similarity is a retrieval score, not a probability. Fit calibration only on held-out validation pairs, then reserve an independent test set for FMR/FNMR and decision-quality measurement. Emit `likely_match`, `ambiguous`, `unknown`, or `insufficient_visual_evidence`.

## Current evidence

No ReID images, identity labels, models, or measurements are supplied. This phase makes no Rank-k, mAP, ROC-AUC, throughput, or false-match claim.
