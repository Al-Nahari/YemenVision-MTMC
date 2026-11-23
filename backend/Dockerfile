FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
      ffmpeg libglib2.0-0 libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Install the shared yemenvision core once; the API must not duplicate CV logic.
COPY pyproject.toml requirements-lock.txt ./
COPY src ./src
COPY backend/requirements.txt ./backend/requirements.txt
RUN python -m pip install --upgrade pip \
    && python -m pip install -r backend/requirements.txt \
    && python -m pip install .

COPY backend/app ./app
COPY configs ./configs
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
