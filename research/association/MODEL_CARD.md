# Multi-camera association model card

## Scope

This engine links local tracklets only inside authorized camera scope and purpose. It outputs a temporary vehicle-event group for accepted evidence, never a confirmed global vehicle identity or personal inference.

## Confidence

Raw appearance cosine is a retrieval feature, not probability. A probability is emitted only when a calibration model trained on independent validation pairs is provided. Low-evidence cases abstain as `unknown` or `ambiguous`.

## Security and retention

Every association is scope-checked and audited. The feature index and authorization have expiry; implementation owners must delete records according to the approved retention period. Number-plate data is neither requested nor emitted.

## Evidence status

There is no calibrated topology, local tracklets, cross-camera ground truth, or ReID embedding model in the supplied workspace. No association accuracy, IDF1/HOTA, FMR, latency, or pairwise claim is made.
