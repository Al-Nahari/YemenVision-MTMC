import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpInterceptorFn } from '@angular/common/http';
import { catchError, Observable, of } from 'rxjs';

export type ApiState = 'loading' | 'live' | 'demo' | 'offline' | 'error';

export interface Camera {
  id: string;
  zone?: string;
  direction?: string;
  active: boolean;
  stream_url?: string | null;
}

export interface CameraInput extends Camera {}

export interface DetectionEvent {
  id: string;
  camera_id: string;
  occurred_at: string;
  payload: any;
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
  };
}

export interface TrafficAggregate {
  id: string;
  camera_id: string;
  bucket_start: string;
  granularity: string;
  payload: any;
}

export interface AuditRecord {
  id: string;
  occurred_at: string;
  actor: string;
  action: string;
  resource: string;
  detail: any;
}

export const apiKeyInterceptor: HttpInterceptorFn = (req, next) => {
  // SSR has no localStorage; configure a key in the browser before making API calls.
  const key = typeof localStorage === 'undefined' ? null : localStorage.getItem('yv_api_key');
  return next(key ? req.clone({ setHeaders: { 'X-API-Key': key } }) : req);
};

@Injectable({ providedIn: 'root' })
export class ApiService {
  private http = inject(HttpClient);
  readonly base = typeof localStorage === 'undefined'
    ? 'http://localhost:8000/api/v1'
    : localStorage.getItem('yv_api_url') || 'http://localhost:8000/api/v1';

  cameras(): Observable<Camera[] | null> {
    return this.http.get<Camera[]>(`${this.base}/cameras`).pipe(catchError(() => of(null)));
  }

  events(limit: number = 50): Observable<DetectionEvent[] | null> {
    return this.http.get<DetectionEvent[]>(`${this.base}/events?limit=${limit}`).pipe(catchError(() => of(null)));
  }

  tracklets(limit: number = 50): Observable<Tracklet[] | null> {
    return this.http.get<Tracklet[]>(`${this.base}/tracklets?limit=${limit}`).pipe(catchError(() => of(null)));
  }

  traffic(): Observable<TrafficAggregate[] | null> {
    return this.http.get<TrafficAggregate[]>(`${this.base}/traffic`).pipe(catchError(() => of(null)));
  }

  audit(): Observable<AuditRecord[] | null> {
    return this.http.get<AuditRecord[]>(`${this.base}/audit`).pipe(catchError(() => of(null)));
  }

  createCamera(camera: CameraInput): Observable<Camera> {
    return this.http.post<Camera>(`${this.base}/cameras`, camera);
  }

  mediaUrl(path: string): string {
    const apiRoot = this.base.replace(/\/api\/v1\/?$/, '');
    return new URL(path, `${apiRoot}/`).toString();
  }

  triggerInference(file: File, cameraId: string): Observable<any> {
    const uploadUrl = `${this.base}/inference/upload?camera_id=${encodeURIComponent(cameraId)}`;
    return new Observable(observer => {
      const xhr = new XMLHttpRequest();
      xhr.open('POST', uploadUrl);
      xhr.setRequestHeader('Content-Type', file.type || 'application/octet-stream');
      xhr.setRequestHeader('X-File-Name', encodeURIComponent(file.name));
      const key = typeof localStorage === 'undefined' ? null : localStorage.getItem('yv_api_key');
      if (key) xhr.setRequestHeader('X-API-Key', key);
      xhr.upload.onprogress = event => {
        if (event.lengthComputable) observer.next({ uploadProgress: Math.round(event.loaded * 100 / event.total) });
      };
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try { observer.next(JSON.parse(xhr.responseText)); observer.complete(); }
          catch (error) { observer.error(error); }
        } else {
          observer.error({ status: xhr.status, error: (() => { try { return JSON.parse(xhr.responseText); } catch { return {}; } })() });
        }
      };
      xhr.onerror = () => observer.error({ status: 0 });
      xhr.onabort = () => observer.error({ status: 0, aborted: true });
      xhr.send(file);
      return () => xhr.abort();
    });
  }

  sendLiveFrame(cameraId: string, frameIndex: number, detections: any[]): Observable<any> {
    return this.http.post(`${this.base}/inference/frame`, {
      camera_id: cameraId,
      frame_index: frameIndex,
      detections: detections
    });
  }
}
