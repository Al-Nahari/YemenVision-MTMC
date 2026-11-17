from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from yemenvision.config import load_settings
from yemenvision.registry import ModelRegistry
from yemenvision.association import run_mtmc

def check_models(args: argparse.Namespace) -> int:
    registry = ModelRegistry(args.models_dir, trusted_models_only=args.trusted_models_only)
    records = registry.discover()
    errors = sum(not record.valid for record in records)
    if args.json:
        print(json.dumps({"models_dir": str(registry.models_dir), "records": [r.as_dict() for r in records],
                          "status": "PASS" if records and not errors else "NOT_EVALUATED" if not records else "FAIL"},
                         ensure_ascii=False, indent=2))
    else:
        print("kind\tstatus\tfilename\tsize_bytes\tsha256")
        for record in records:
            print(f"{record.kind}\t{'OK' if record.valid else 'ERROR'}\t{record.path.name}\t{record.size_bytes}\t{record.sha256}")
            for issue in record.issues:
                print(f"  {issue.level}: {issue.message}")
        if not records:
            print(f"NOT_EVALUATED\tno .pt files found in {registry.models_dir}")
    return 1 if not records or errors else 0

def run_mtmc_command(args: argparse.Namespace) -> int:
    result = run_mtmc(args.runs, args.output_dir, args.topology, args.threshold, args.allow_appearance_only)
    payload = {"global_vehicles": result.global_vehicles, "links": result.links,
               "events": result.events, "abstentions": result.abstentions}
    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else payload)
    return 0 if not result.abstentions or args.allow_appearance_only else 2


def run_video(args: argparse.Namespace) -> int:
    settings = load_settings(args.config, {"output_dir": args.output_dir} if args.output_dir else None)
    registry = ModelRegistry(settings.models_dir, trusted_models_only=args.trusted_models_only)
    detector_record = registry.select("detector", args.detector)
    reid_record = registry.select("reid", args.reid) if args.reid else None
    from yemenvision.detection import VehicleDetector
    from yemenvision.pipeline import OfflinePipeline, PipelineMetadata
    from yemenvision.reid import ReIDEncoder
    from yemenvision.tracking import IoUTracker
    detector = VehicleDetector(detector_record.path, confidence=settings.detection.confidence,
                               iou=settings.detection.iou, imgsz=settings.detection.imgsz,
                               device=settings.detection.device, amp=settings.detection.amp)
    encoder = ReIDEncoder(reid_record.path, device=settings.detection.device, flip_tta=settings.reid.flip_tta) if reid_record else None
    tracker = IoUTracker(match_thresh=settings.tracking.match_thresh,
                          track_buffer=settings.tracking.track_buffer,
                          new_track_thresh=settings.tracking.new_track_thresh)
    pipeline = OfflinePipeline(detector, tracker, encoder,
                               model_metadata={"detector": detector_record.as_dict(), "reid": reid_record.as_dict() if reid_record else None})
    result = pipeline.run(args.video, camera_id=args.camera_id, output_dir=settings.output_dir,
                          vid_stride=args.vid_stride, config=settings.as_dict())
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else result)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="yv")
    sub = parser.add_subparsers(dest="command", required=True)
    mtmc = sub.add_parser("mtmc", help="associate tracklets from multiple runs")
    mtmc.add_argument("runs", nargs="+", help="run directories containing tracklets.jsonl")
    mtmc.add_argument("--output-dir", required=True); mtmc.add_argument("--topology", default=None)
    mtmc.add_argument("--threshold", type=float, default=0.5); mtmc.add_argument("--allow-appearance-only", action="store_true")
    mtmc.add_argument("--json", action="store_true"); mtmc.set_defaults(func=run_mtmc_command)
    run = sub.add_parser("run", help="run the real detector/tracker/ReID pipeline")
    run.add_argument("video"); run.add_argument("--camera-id", required=True)
    run.add_argument("--output-dir", default=None); run.add_argument("--config", default=None)
    run.add_argument("--detector", default=None); run.add_argument("--reid", default=None)
    run.add_argument("--vid-stride", type=int, default=1); run.add_argument("--trusted-models-only", action="store_true")
    run.add_argument("--json", action="store_true"); run.set_defaults(func=run_video)
    check = sub.add_parser("check-models")
    check.add_argument("--models-dir", default=None)
    check.add_argument("--trusted-models-only", action="store_true")
    check.add_argument("--json", action="store_true")
    check.set_defaults(func=check_models)
    args = parser.parse_args(argv)
    return int(args.func(args))

if __name__ == "__main__": sys.exit(main())
