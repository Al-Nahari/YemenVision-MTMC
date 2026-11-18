FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04
ENV DEBIAN_FRONTEND=noninteractive PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-pip python3-venv ffmpeg libglib2.0-0 libgl1 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY pyproject.toml requirements-lock.txt ./
COPY src ./src
RUN python3 -m pip install --no-cache-dir --upgrade pip && python3 -m pip install --no-cache-dir .[detection,reid,api]
COPY configs ./configs
COPY models/README.md models/manifest.json models/detector_inference_config.json ./models/
COPY models/detector_best.pt models/reid_best.pt models/vehicle_attributes.pt ./models/
ENTRYPOINT ["yv"]
CMD ["serve", "--host", "0.0.0.0", "--port", "8000"]
