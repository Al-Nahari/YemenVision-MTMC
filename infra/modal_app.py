"""Optional Modal GPU runner for YemenVision video inference.

Run from the repository root:
    modal run infra/modal_app.py

The dashboard/backend remain local by default. This file is the remote GPU
entry point for deployments that want to offload a video URL to Modal.
"""
from __future__ import annotations

import modal


APP_NAME = "yemenvision-gpu"
DEFAULT_VIDEO_URL = "https://storage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4"
MODEL_LOCAL_PATH = "models/detector_best.pt"
MODEL_REMOTE_PATH = "/models/detector_best.pt"

app = modal.App(APP_NAME)

image = (
    modal.Image.from_registry("nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04", add_python="3.11")
    .apt_install("ffmpeg", "libgl1", "libglib2.0-0")
    .pip_install("numpy<2.3", "opencv-python-headless", "requests", "ultralytics")
    .add_local_file(MODEL_LOCAL_PATH, MODEL_REMOTE_PATH)
)


@app.function(image=image, gpu="T4", timeout=3600, retries=1)
def process_video_url(video_url: str = DEFAULT_VIDEO_URL, max_frames: int = 120) -> dict:
    """Download a public video and run the verified detector on Modal GPU."""
    import time
    from pathlib import Path

    import cv2
    import requests
    import torch
    from ultralytics import YOLO

    target = Path("/tmp/input-video.mp4")
    with requests.get(video_url, stream=True, timeout=60) as response:
        response.raise_for_status()
        with target.open("wb") as output:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    output.write(chunk)

    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    model = YOLO(MODEL_REMOTE_PATH)
    model.to(device)
    capture = cv2.VideoCapture(str(target))
    if not capture.isOpened():
        raise RuntimeError("Modal worker could not open the downloaded video")

    frames = 0
    detections = 0
    classes: dict[str, int] = {}
    started = time.time()
    try:
        while frames < max_frames:
            ok, frame = capture.read()
            if not ok:
                break
            result = model.predict(frame, conf=0.25, verbose=False, device=device)[0]
            boxes = result.boxes
            count = len(boxes) if boxes is not None else 0
            detections += count
            if boxes is not None:
                for class_id in boxes.cls.int().cpu().tolist():
                    name = str(result.names.get(class_id, class_id))
                    classes[name] = classes.get(name, 0) + 1
            frames += 1
    finally:
        capture.release()

    return {
        "status": "completed",
        "device": device,
        "gpu_name": torch.cuda.get_device_name(0) if device.startswith("cuda") else None,
        "video_url": video_url,
        "frames_processed": frames,
        "detections": detections,
        "classes": classes,
        "duration_seconds": round(time.time() - started, 3),
    }


@app.local_entrypoint()
def main(video_url: str = DEFAULT_VIDEO_URL, max_frames: int = 120):
    result = process_video_url.remote(video_url, max_frames)
    print(result)
