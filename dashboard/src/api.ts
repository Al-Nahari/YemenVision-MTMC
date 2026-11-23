// In dev, requests go through Vite's proxy which injects the local API key.
// In a production build the browser talks to the backend directly, so the
// address (and key) must be configured on the Settings page.
const DEFAULT_API_BASE = import.meta.env.DEV
  ? '/api/v1'
  : (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8001/api/v1');


export interface Camera {
  id: string;
  zone?: string;
  direction?: string;
  active: boolean;
  stream_url?: string | null;
}

export interface CameraInput extends Camera {
  stream_url: string | null;
}

export interface CameraUpdate {
  zone?: string | null;
  direction?: string | null;
  active?: boolean;
  stream_url?: string | null;
}

export interface ProcessedVideo {
  id: string;
  file_name: string;
  original_name: string;
  video_id: string;
  camera_id: string | null;
  created_at: string;
  frames_processed: number;
  duration_seconds: number;
  file_size: number;
  model_version: string | null;
  plate_count: number;
  source: 'upload' | 'legacy';
  video_url: string;
}

export interface PlateReading {
  id: string;
  camera_id: string;
  occurred_at: string;
  plate_text: string;
  video_id?: string | null;
  frame_index?: number | null;
  track_id?: number | null;
  class_name?: string | null;
  confidence?: number | null;
  status?: string | null;
}

export interface DetectionEvent {
  id: string;
  camera_id: string;
  occurred_at: string;
  plate_text?: string | null;
  payload: {
    class_name?: string;
    confidence?: number;
    plate_text?: string | null;
    plate_confidence?: number;
    plate_status?: string;
    [key: string]: unknown;
  } | null;
}

export interface Tracklet {
  id: string;
  camera_id: string;
  video_id: string;
  local_track_id: number;
  start_time: string;
  end_time: string;
  payload: {
    vehicle_type?: string;
    box?: number[];
    embedding_dim?: number;
    frames_tracked?: number;
    model_version?: string;
    reid_matched?: boolean;
    confidence?: number;
  } | null;
}

export interface TrafficAggregate {
  id: string;
  camera_id: string;
  bucket_start: string;
  granularity: string;
  payload: { total_vehicles?: number; [key: string]: unknown } | null;
}

export interface InferenceResult {
  model_version: string;
  duration_seconds: number;
  frames_processed: number;
  tracklets_count: number;
  events_count: number;
  video_id: string;
  video_url?: string | null;
  [key: string]: unknown;
}

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export function apiBase(): string {
  return (localStorage.getItem('yv_api_url') || DEFAULT_API_BASE).replace(/\/+$/, '');
}

function authHeaders(): Record<string, string> {
  const key = localStorage.getItem('yv_api_key') || '';
  return key ? { 'X-API-Key': key } : {};
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 15_000);
  let response: Response;
  try {
    response = await fetch(`${apiBase()}${path}`, {
      ...init,
      signal: init.signal || controller.signal,
      headers: {
        ...authHeaders(),
        ...(init.body ? { 'Content-Type': 'application/json' } : {}),
        ...init.headers,
      },
    });
  } catch (error) {
    const message = error instanceof DOMException && error.name === 'AbortError'
      ? 'انتهت مهلة الاتصال بالخادم. تحقق من تشغيل Backend.'
      : 'تعذّر الاتصال بالخادم. تحقق من تشغيل Backend.';
    throw new ApiError(0, message);
  } finally {
    window.clearTimeout(timeout);
  }

  if (response.status === 401) {
    window.dispatchEvent(new CustomEvent('yv-api-unauthorized'));
  }

  if (!response.ok) {
    let detail = '';
    try {
      const body = (await response.json()) as { detail?: unknown };
      detail = typeof body.detail === 'string' ? body.detail : '';
    } catch {
      // The error body is optional.
    }
    throw new ApiError(response.status, detail || `HTTP ${response.status}`);
  }

  return (await response.json()) as T;
}

async function list<T>(path: string): Promise<T[]> {
  try {
    return await request<T[]>(path);
  } catch {
    return [];
  }
}

export const api = {
  cameras: () => list<Camera>('/cameras'),
  events: (limit = 20) => list<DetectionEvent>(`/events?limit=${limit}`),
  tracklets: (limit = 20) => list<Tracklet>(`/tracklets?limit=${limit}`),
  traffic: () => list<TrafficAggregate>('/traffic'),

  createCamera: (camera: CameraInput) =>
    request<Camera>('/cameras', {
      method: 'POST',
      body: JSON.stringify(camera),
    }),

  updateCamera: (id: string, changes: CameraUpdate) =>
    request<Camera>(`/cameras/${encodeURIComponent(id)}`, {
      method: 'PUT',
      body: JSON.stringify(changes),
    }),

  deleteCamera: (id: string) =>
    request<{
      status: string;
      camera_id: string;
      historical_rows_kept: { events: number; tracklets: number };
    }>(`/cameras/${encodeURIComponent(id)}`, { method: 'DELETE' }),

  videos: (params: { camera_id?: string; search?: string; limit?: number; offset?: number } = {}) => {
    const query = new URLSearchParams();
    if (params.camera_id) query.set('camera_id', params.camera_id);
    if (params.search) query.set('search', params.search);
    if (params.limit) query.set('limit', String(params.limit));
    if (params.offset) query.set('offset', String(params.offset));
    const suffix = query.toString();
    return list<ProcessedVideo>(`/videos${suffix ? `?${suffix}` : ''}`);
  },

  video: (id: string) => request<ProcessedVideo>(`/videos/${encodeURIComponent(id)}`),

  deleteVideo: (id: string) =>
    request<{ status: string }>(`/videos/${encodeURIComponent(id)}`, { method: 'DELETE' }),

  plates: (params: { camera_id?: string; plate?: string; limit?: number; offset?: number } = {}) => {
    const query = new URLSearchParams();
    if (params.camera_id) query.set('camera_id', params.camera_id);
    if (params.plate) query.set('plate', params.plate);
    if (params.limit) query.set('limit', String(params.limit));
    if (params.offset) query.set('offset', String(params.offset));
    const suffix = query.toString();
    return list<PlateReading>(`/plates${suffix ? `?${suffix}` : ''}`);
  },

  mediaUrl(path: string): string {
    const root = apiBase().replace(/\/api\/v1\/?$/, '');
    if (!root) {
      return path.startsWith('/') ? path : `/${path}`;
    }
    return new URL(path, `${root}/`).toString();
  },

  liveStreamUrl(
    url: string,
    cameraId: string | null,
    maxFps: number = 5,
    maxWidth: number = 640,
  ): string {
    const query = new URLSearchParams();
    query.set('url', url);
    query.set('max_fps', String(maxFps));
    query.set('max_width', String(maxWidth));
    const key = localStorage.getItem('yv_api_key') || '';
    if (key) query.set('api_key', key);
    if (cameraId) query.set('camera_id', cameraId);
    const root = apiBase().replace(/\/api\/v1\/?$/, '');
    const path = `/live/stream?${query.toString()}`;
    if (!root) {
      return path.startsWith('/') ? path : `/${path}`;
    }
    return new URL(path, `${root}/`).toString();
  },

  uploadVideo(
    file: File,
    cameraId: string,
    onProgress: (percent: number) => void,
    maxFrames: number = 300,
  ): Promise<InferenceResult> {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      const params = new URLSearchParams({
        camera_id: cameraId,
        max_frames: String(maxFrames),
      });
      xhr.open('POST', `${apiBase()}/inference/upload?${params.toString()}`);
      xhr.setRequestHeader('Content-Type', file.type || 'application/octet-stream');
      xhr.setRequestHeader('X-File-Name', encodeURIComponent(file.name));

      const key = localStorage.getItem('yv_api_key') || '';
      if (key) xhr.setRequestHeader('X-API-Key', key);

      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          onProgress(Math.round((event.loaded * 100) / event.total));
        }
      };

      xhr.onload = () => {
        if (xhr.status === 401) {
          window.dispatchEvent(new CustomEvent('yv-api-unauthorized'));
        }
        if (xhr.status < 200 || xhr.status >= 300) {
          let detail = '';
          try {
            const body = JSON.parse(xhr.responseText) as { detail?: unknown };
            detail = typeof body.detail === 'string' ? body.detail : '';
          } catch {
            // The error body is optional.
          }
          reject(new ApiError(xhr.status, detail || `HTTP ${xhr.status}`));
          return;
        }

        try {
          resolve(JSON.parse(xhr.responseText) as InferenceResult);
        } catch {
          reject(new ApiError(xhr.status, 'استجابة غير صالحة من الخادم'));
        }
      };

      xhr.onerror = () => reject(new ApiError(0, 'تعذّر الاتصال بالخادم'));
      xhr.onabort = () => reject(new ApiError(0, 'تم إلغاء الرفع'));
      xhr.send(file);
    });
  },
};
