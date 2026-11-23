"""Short-lived FFmpeg HLS sessions for browser-friendly live playback."""
from __future__ import annotations

import secrets
import shutil
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class HlsSession:
    id: str
    token: str
    directory: Path
    process: subprocess.Popen
    created_at: float


class HlsManager:
    def __init__(self, root: Path):
        self.root = root / '.hls'
        self.root.mkdir(parents=True, exist_ok=True)
        self.sessions: dict[str, HlsSession] = {}
        self.lock = threading.RLock()

    def start(self, source: str) -> HlsSession:
        self.cleanup()
        session_id = secrets.token_hex(12)
        token = secrets.token_urlsafe(24)
        directory = self.root / session_id
        directory.mkdir(parents=True, exist_ok=True)
        playlist = directory / 'index.m3u8'
        command = [
            'ffmpeg', '-hide_banner', '-loglevel', 'error',
            '-rtsp_transport', 'tcp', '-i', source,
            '-an', '-c:v', 'libx264', '-preset', 'ultrafast',
            '-tune', 'zerolatency', '-g', '30', '-keyint_min', '30',
            '-f', 'hls', '-hls_time', '1', '-hls_list_size', '5',
            '-hls_flags', 'delete_segments+append_list', str(playlist),
        ]
        try:
            process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        except FileNotFoundError as exc:
            shutil.rmtree(directory, ignore_errors=True)
            raise RuntimeError('FFmpeg is not installed or is not available on PATH') from exc
        session = HlsSession(session_id, token, directory, process, time.time())
        with self.lock:
            self.sessions[session_id] = session
        return session

    def get(self, session_id: str, token: str) -> HlsSession | None:
        self.cleanup()
        with self.lock:
            session = self.sessions.get(session_id)
            return session if session and secrets.compare_digest(session.token, token) else None

    def stop(self, session_id: str, token: str) -> bool:
        with self.lock:
            session = self.sessions.get(session_id)
            if not session or not secrets.compare_digest(session.token, token):
                return False
            self.sessions.pop(session_id, None)
        session.process.terminate()
        shutil.rmtree(session.directory, ignore_errors=True)
        return True

    def cleanup(self, max_age: int = 900) -> None:
        now = time.time()
        with self.lock:
            expired = [sid for sid, s in self.sessions.items() if now - s.created_at > max_age or s.process.poll() is not None]
            for sid in expired:
                session = self.sessions.pop(sid)
                if session.process.poll() is None:
                    session.process.terminate()
                shutil.rmtree(session.directory, ignore_errors=True)
