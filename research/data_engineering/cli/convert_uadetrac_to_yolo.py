"""Convert UA-DETRAC XML annotations to YOLO format with zero video-sequence leakage."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Set, Tuple
import yaml

VEHICLE_CLASS_MAP = {
    'car': 0,
    'bus': 1,
    'van': 2,
    'others': 3
}

def is_box_inside_ignore(box: Tuple[float, float, float, float], ignore_boxes: List[Tuple[float, float, float, float]]) -> bool:
    """Check if center of target box falls inside any ignore region."""
    bx1, by1, bx2, by2 = box
    cx, cy = (bx1 + bx2) / 2.0, (by1 + by2) / 2.0
    for ix1, iy1, ix2, iy2 in ignore_boxes:
        if ix1 <= cx <= ix2 and iy1 <= cy <= iy2:
            return True
    return False

def parse_xml_annotations(
    xml_path: Path,
    img_width: float = 960.0,
    img_height: float = 540.0
) -> Tuple[Dict[int, List[Tuple[int, float, float, float, float]]], Set[str]]:
    """Parse UA-DETRAC sequence XML, ignoring masked regions."""
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # 1. Parse ignored regions
    ignore_regions: List[Tuple[float, float, float, float]] = []
    for ig in root.iter('ignored_region'):
        box = ig.find('box')
        if box is not None:
            left = float(box.attrib.get('left', 0))
            top = float(box.attrib.get('top', 0))
            w = float(box.attrib.get('width', 0))
            h = float(box.attrib.get('height', 0))
            ignore_regions.append((left, top, left + w, top + h))

    frames_data: Dict[int, List[Tuple[int, float, float, float, float]]] = {}
    observed_classes: Set[str] = set()

    # 2. Parse target boxes per frame
    for frame in root.iter('frame'):
        num_str = frame.attrib.get('num') or frame.attrib.get('frameID')
        if not num_str:
            continue
        frame_num = int(num_str)
        frame_boxes: List[Tuple[int, float, float, float, float]] = []

        for target in frame.iter('target'):
            vehicle = target.find('vehicle')
            box = target.find('box')
            if box is None:
                continue

            left = float(box.attrib.get('left', 0))
            top = float(box.attrib.get('top', 0))
            w = float(box.attrib.get('width', 0))
            h = float(box.attrib.get('height', 0))

            # Filter out boxes in ignored regions
            if is_box_inside_ignore((left, top, left + w, top + h), ignore_regions):
                continue

            v_type = vehicle.attrib.get('type', 'car').lower() if vehicle is not None else 'car'
            observed_classes.add(v_type)
            cls_id = VEHICLE_CLASS_MAP.get(v_type, 0)

            # YOLO normalized bbox: x_center, y_center, w, h
            xc = min(max((left + w / 2.0) / img_width, 0.0), 1.0)
            yc = min(max((top + h / 2.0) / img_height, 0.0), 1.0)
            nw = min(max(w / img_width, 0.0), 1.0)
            nh = min(max(h / img_height, 0.0), 1.0)

            if nw > 0.005 and nh > 0.005:  # discard degenerated tiny boxes
                frame_boxes.append((cls_id, xc, yc, nw, nh))

        frames_data[frame_num] = frame_boxes

    return frames_data, observed_classes

def split_sequence(sequence_name: str, seed: int = 17) -> str:
    """Deterministic video-level hash split: 70% train, 15% val, 15% test."""
    val = int(hashlib.sha256(f"{seed}:{sequence_name}".encode('utf-8')).hexdigest()[:8], 16) / 0xffffffff
    if val < 0.70:
        return 'train'
    elif val < 0.85:
        return 'val'
    return 'test'

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw-dir', type=Path, required=True, help="Path to RAW UA-DETRAC directory")
    parser.add_argument('--output-dir', type=Path, required=True, help="Path to prepared/detection directory")
    parser.add_argument('--sample-rate', type=int, default=5, help="Sample every N frames (default: 5)")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for s in ['train', 'val', 'test']:
        (args.output_dir / 'images' / s).mkdir(parents=True, exist_ok=True)
        (args.output_dir / 'labels' / s).mkdir(parents=True, exist_ok=True)

    xml_files = list(args.raw_dir.rglob('*.xml'))
    if not xml_files:
        print(f"No XML files found in {args.raw_dir}")
        return

    manifest_rows = []
    all_classes: Set[str] = set()

    for xml_path in xml_files:
        seq_name = xml_path.stem
        split = split_sequence(seq_name)
        frames_dict, obs_cls = parse_xml_annotations(xml_path)
        all_classes.update(obs_cls)

        for frame_num, boxes in frames_dict.items():
            if frame_num % args.sample_rate != 0:
                continue

            lbl_name = f"{seq_name}_img{frame_num:05d}.txt"
            lbl_path = args.output_dir / 'labels' / split / lbl_name
            with open(lbl_path, 'w', encoding='utf-8') as f:
                for b in boxes:
                    f.write(f"{b[0]} {b[1]:.6f} {b[2]:.6f} {b[3]:.6f} {b[4]:.6f}\n")

            manifest_rows.append({
                'sequence': seq_name,
                'frame': frame_num,
                'split': split,
                'boxes_count': len(boxes)
            })

    # Write split manifest
    manifest_file = args.output_dir / 'split_manifest.json'
    with open(manifest_file, 'w', encoding='utf-8') as f:
        json.dump(manifest_rows, f, indent=2)

    # Write data.yaml
    names_dict = {v: k for k, v in sorted(VEHICLE_CLASS_MAP.items(), key=lambda x: x[1])}
    data_yaml = {
        'path': str(args.output_dir.resolve()),
        'train': 'images/train',
        'val': 'images/val',
        'test': 'images/test',
        'names': names_dict
    }
    with open(args.output_dir / 'data.yaml', 'w', encoding='utf-8') as f:
        yaml.safe_dump(data_yaml, f)

    print(f"Completed! Converted {len(xml_files)} sequences. Sample rate N={args.sample_rate}.")
    print(f"Wrote data.yaml and split_manifest.json to {args.output_dir}")

if __name__ == '__main__':
    main()
