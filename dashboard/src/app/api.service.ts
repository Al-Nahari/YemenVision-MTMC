import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpInterceptorFn } from '@angular/common/http';
import { catchError, Observable, of } from 'rxjs';

export type ApiState = 'loading' | 'live' | 'demo' | 'offline' | 'error';

export interface Camera {
  id: string;
  zone?: string;
  direction?: string;
  active: boolean;
}

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
  const key = localStorage.getItem('yv_api_key') || 'admin';
  return next(req.clone({ setHeaders: { 'X-API-Key': key } }));
};

@Injectable({ providedIn: 'root' })
export class ApiService {
  private http = inject(HttpClient);
  readonly base = localStorage.getItem('yv_api_url') || 'http://localhost:8000/api/v1';

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

  triggerInference(videoPath: string, cameraId: string): Observable<any> {
    return this.http.post(`${this.base}/inference/video`, {
      video_path: videoPath,
      camera_id: cameraId,
      conf_threshold: 0.25,
      iou_threshold: 0.3
    });
  }
}
