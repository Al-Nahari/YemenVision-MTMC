from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from .associator import CrossCameraAssociator, Link, Tracklet


@dataclass(frozen=True)
class MTMCResult:
    global_vehicles: list[dict[str, Any]]
    links: list[dict[str, Any]]
    events: list[dict[str, Any]]
    abstentions: list[dict[str, Any]]


class _UnionFind:
    def __init__(self, items: list[tuple[str, int]]) -> None:
        self.parent = {item: item for item in items}

    def find(self, item: tuple[str, int]) -> tuple[str, int]:
        parent = self.parent[item]
        if parent != item:
            self.parent[item] = self.find(parent)
        return self.parent[item]

    def union(self, left: tuple[str, int], right: tuple[str, int]) -> None:
        root_left = self.find(left); root_right = self.find(right)
        if root_left != root_right:
            self.parent[max(root_left, root_right)] = min(root_left, root_right)


def load_topology(path: str | Path) -> dict[str, dict[str, dict[str, float]]]:
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"topology file does not exist: {source}")
    data = yaml.safe_load(source.read_text(encoding="utf-8")) or {}
    result: dict[str, dict[str, dict[str, float]]] = {}
    for camera_id, camera in (data.get("cameras") or {}).items():
        transitions = camera.get("transitions") or {}
        result[str(camera_id)] = {
            str(target): {"min_seconds": float(spec["min_seconds"]), "max_seconds": float(spec["max_seconds"])}
            for target, spec in transitions.items()
            if isinstance(spec, dict) and "min_seconds" in spec and "max_seconds" in spec
        }
    return result


def _load_run(run_dir: Path) -> list[Tracklet]:
    tracklet_path = run_dir / "tracklets.jsonl"
    if not tracklet_path.is_file():
        raise FileNotFoundError(f"missing tracklets.jsonl: {tracklet_path}")
    embeddings_path = run_dir / "embeddings.npy"
    embeddings = np.load(embeddings_path) if embeddings_path.is_file() else np.empty((0, 0), dtype=np.float32)
    result = []
    for row in tracklet_path.read_text(encoding="utf-8").splitlines():
        if not row.strip():
            continue
        item = json.loads(row)
        index = item.get("embedding_index")
        embedding = embeddings[int(index)].tolist() if index is not None and int(index) < len(embeddings) else None
        result.append(Tracklet(str(item["camera_id"]), int(item["track_id"]),
                               datetime.fromtimestamp(float(item["t_start"]), timezone.utc),
                               datetime.fromtimestamp(float(item["t_end"]), timezone.utc), embedding,
                               str(item.get("class_name", "unknown"))))
    return result


def run_mtmc(run_dirs: list[str | Path], output_dir: str | Path, topology_path: str | Path | None,
             threshold: float = 0.5, allow_appearance_only: bool = False) -> MTMCResult:
    runs = sorted(Path(item).resolve() for item in run_dirs)
    tracklets = [tracklet for run in runs for tracklet in _load_run(run)]
    nodes = sorted((item.camera_id, item.track_id) for item in tracklets)
    topology = load_topology(topology_path) if topology_path else {}
    abstentions: list[dict[str, Any]] = []
    if not topology and not allow_appearance_only:
        abstentions = [{"node": list(node), "reason": "missing_camera_topology"} for node in nodes]
        links: list[Link] = []
    else:
        links = []
        associator = CrossCameraAssociator(topology, threshold=threshold)
        for source in sorted(tracklets, key=lambda item: (item.camera_id, item.track_id)):
            targets = [item for item in tracklets if item.camera_id != source.camera_id and item.t_start >= source.t_end]
            if not topology and allow_appearance_only:
                abstentions.append({"node": [source.camera_id, source.track_id], "reason": "appearance_only_explicitly_enabled"})
            links.extend(associator.associate([source], targets))
    link_rows = [{"source": list(link.source), "target": list(link.target), "confidence": link.confidence,
                  "score": link.score, "reasons": link.reasons} for link in sorted(links, key=lambda item: (item.source, item.target))]
    union = _UnionFind(nodes)
    for link in links:
        union.union(link.source, link.target)
    groups: dict[tuple[str, int], list[tuple[str, int]]] = {}
    for node in nodes:
        groups.setdefault(union.find(node), []).append(node)
    ordered_groups = sorted((sorted(group) for group in groups.values()), key=lambda group: group[0])
    global_vehicles = [{"global_id": f"gv_{index:06d}", "tracklets": [list(node) for node in group]}
                       for index, group in enumerate(ordered_groups, 1)]
    events = [{"global_id": vehicle["global_id"], "event": "camera_transition", "camera_id": camera,
               "track_id": track_id} for vehicle in global_vehicles for camera, track_id in vehicle["tracklets"]]
    result = MTMCResult(global_vehicles, link_rows, events, abstentions)
    target = Path(output_dir); target.mkdir(parents=True, exist_ok=True)
    (target / "global_vehicles.json").write_text(json.dumps({"global_vehicles": global_vehicles, "links": link_rows,
                                                               "abstentions": abstentions}, indent=2), encoding="utf-8")
    with (target / "events.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["global_id", "event", "camera_id", "track_id"])
        writer.writeheader(); writer.writerows(events)
    return result
