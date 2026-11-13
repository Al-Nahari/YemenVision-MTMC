# Vehicle detector model card

## Status

**Not trained.** This codebase was created from a Phase 02 package whose provenance declares no downloaded datasets or weights. No metric, FPS, latency, memory, exported artifact, or demo video is available yet.

## Intended use

Detect the classes explicitly declared in an approved YOLO dataset contract, on authorized road imagery. The model is not an identity system, traffic-enforcement decision maker, or safety-critical autonomous-driving component.

## Taxonomy policy

The class list comes exclusively from `names` in the approved YAML. Candidate labels such as `van` and `other_vehicle` must not be introduced unless they are labelled sufficiently and can be reliably distinguished in an independent test set.

## Evaluation protocol

Run `detection.evaluate` separately on public and Yemen-local held-out splits. Preserve camera/video/group separation. Report Precision, Recall, F1, mAP50, mAP50-95, per-class AP, confusion matrix, PR curve, latency, FPS, peak GPU memory, and serialized model size. Analyze false positives/negatives by small/distant objects, occlusion, illumination, weather/dust, motion blur, and camera angle.

## Known limitations

Performance cannot be inferred before measurement. Synthetic weather or blur is disabled by default because it can invalidate labels. Results vary with camera, class distribution, resolution, hardware, codec, and confidence threshold.
