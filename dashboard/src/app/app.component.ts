import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, ActivatedRoute } from '@angular/router';
import { ApiService, Camera, DetectionEvent, Tracklet, TrafficAggregate } from './api.service';

@Component({
  selector: 'app-page',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <div class="page-container">
      <!-- KPI Top Summary Row -->
      <div class="kpi-grid">
        <div class="kpi-card">
          <div class="kpi-label">Active Cameras</div>
          <div class="kpi-value">{{ cameras.length }}</div>
          <div class="kpi-sub">Connected sources</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Active Vehicle Tracklets</div>
          <div class="kpi-value">{{ tracklets.length }}</div>
          <div class="kpi-sub">Tracked trajectories</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Detection Events</div>
          <div class="kpi-value">{{ events.length }}</div>
          <div class="kpi-sub">Total verified boxes</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">System Backend Status</div>
          <div class="kpi-value" [ngClass]="{'status-live': backendOnline, 'status-offline': !backendOnline}">
            {{ backendOnline ? 'ONLINE' : 'CONNECTING' }}
          </div>
          <div class="kpi-sub">FastAPI platform v0.2.0</div>
        </div>
      </div>

      <!-- Main Content Tabs / Data Tables -->
      <div class="content-section">
        <div class="section-header">
          <h2>Vehicle Tracklets (ReID-Indexed Tracks)</h2>
          <button class="btn-refresh" (click)="loadAllData()">Refresh Data</button>
        </div>

        <div class="table-wrapper">
          <table class="data-table" *ngIf="tracklets.length > 0; else noTracks">
            <thead>
              <tr>
                <th>Tracklet ID</th>
                <th>Camera ID</th>
                <th>Local ID</th>
                <th>Vehicle Class</th>
                <th>Start Time</th>
                <th>Duration (Frames)</th>
                <th>Embedding Dim</th>
                <th>Model Version</th>
              </tr>
            </thead>
            <tbody>
              <tr *ngFor="let t of tracklets">
                <td class="mono-id">{{ t.id }}</td>
                <td><span class="badge badge-camera">{{ t.camera_id }}</span></td>
                <td>#{{ t.local_track_id }}</td>
                <td><span class="badge badge-class">{{ t.payload?.vehicle_type || 'vehicle' }}</span></td>
                <td>{{ t.start_time | date:'HH:mm:ss' }}</td>
                <td>{{ t.payload?.frames_tracked || '-' }}</td>
                <td>{{ t.payload?.embedding_dim || 512 }}D</td>
                <td class="subtle">{{ t.payload?.model_version || 'yolo11n_vehicle' }}</td>
              </tr>
            </tbody>
          </table>
          <ng-template #noTracks>
            <div class="empty-state">
              <p>No tracklets recorded yet. Run inference on a video stream or post events via API.</p>
            </div>
          </ng-template>
        </div>
      </div>

      <!-- Recent Detection Events Log -->
      <div class="content-section">
        <div class="section-header">
          <h2>Real-Time Detection Events Stream</h2>
        </div>
        <div class="table-wrapper">
          <table class="data-table" *ngIf="events.length > 0; else noEvents">
            <thead>
              <tr>
                <th>Event ID</th>
                <th>Camera</th>
                <th>Timestamp</th>
                <th>Event Type</th>
                <th>Vehicle / Object</th>
                <th>Confidence</th>
              </tr>
            </thead>
            <tbody>
              <tr *ngFor="let e of events | slice:0:15">
                <td class="mono-id">{{ e.id }}</td>
                <td><span class="badge badge-camera">{{ e.camera_id }}</span></td>
                <td>{{ e.occurred_at | date:'yyyy-MM-dd HH:mm:ss' }}</td>
                <td>{{ e.payload?.event_type || 'detection' }}</td>
                <td><span class="badge badge-class">{{ e.payload?.class_name || 'vehicle' }}</span></td>
                <td>{{ (e.payload?.confidence ? (e.payload.confidence * 100).toFixed(1) + '%' : '-') }}</td>
              </tr>
            </tbody>
          </table>
          <ng-template #noEvents>
            <div class="empty-state">
              <p>No recent detection events found in the database.</p>
            </div>
          </ng-template>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .page-container { display: flex; flex-direction: column; gap: 24px; padding: 24px; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; min-height: 100vh; }
    .kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; }
    .kpi-card { background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 18px; }
    .kpi-label { font-size: 13px; color: #94a3b8; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; }
    .kpi-value { font-size: 28px; font-weight: 700; margin: 8px 0 4px; color: #f8fafc; }
    .kpi-sub { font-size: 12px; color: #64748b; }
    .status-live { color: #10b981; }
    .status-offline { color: #f59e0b; }
    .content-section { background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 20px; }
    .section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
    .section-header h2 { font-size: 18px; font-weight: 600; margin: 0; color: #e2e8f0; }
    .btn-refresh { background: #3b82f6; color: white; border: none; padding: 8px 16px; border-radius: 6px; font-weight: 500; cursor: pointer; transition: background 0.2s; }
    .btn-refresh:hover { background: #2563eb; }
    .table-wrapper { overflow-x: auto; }
    .data-table { width: 100%; border-collapse: collapse; font-size: 14px; text-align: left; }
    .data-table th { background: #0f172a; color: #94a3b8; padding: 12px 14px; font-weight: 600; border-bottom: 1px solid #334155; }
    .data-table td { padding: 12px 14px; border-bottom: 1px solid #334155; color: #cbd5e1; }
    .data-table tr:hover { background: #243248; }
    .mono-id { font-family: monospace; font-size: 12px; color: #38bdf8; }
    .badge { padding: 3px 8px; border-radius: 4px; font-size: 12px; font-weight: 500; }
    .badge-camera { background: #1e3a8a; color: #93c5fd; }
    .badge-class { background: #064e3b; color: #6ee7b7; text-transform: capitalize; }
    .subtle { color: #64748b; font-size: 12px; }
    .empty-state { padding: 32px; text-align: center; color: #64748b; }
  `]
})
export class PageComponent implements OnInit {
  private api = inject(ApiService);

  cameras: Camera[] = [];
  events: DetectionEvent[] = [];
  tracklets: Tracklet[] = [];
  trafficList: TrafficAggregate[] = [];
  backendOnline: boolean = false;

  ngOnInit(): void {
    this.loadAllData();
  }

  loadAllData(): void {
    this.api.cameras().subscribe(c => {
      this.cameras = c || [];
      this.backendOnline = c !== null;
    });

    this.api.tracklets(100).subscribe(t => {
      this.tracklets = t || [];
    });

    this.api.events(100).subscribe(e => {
      this.events = e || [];
    });

    this.api.traffic().subscribe(tr => {
      this.trafficList = tr || [];
    });
  }
}

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterModule],
  template: `
    <div class="app-layout">
      <header class="navbar">
        <div class="brand">
          <span class="logo-badge">YV</span>
          <span class="title">YemenVision MTMC — Traffic Intelligence Platform</span>
        </div>
        <div class="nav-links">
          <a routerLink="/" routerLinkActive="active" [routerLinkActiveOptions]="{exact: true}">Overview</a>
          <a routerLink="/cameras" routerLinkActive="active">Cameras</a>
          <a routerLink="/live" routerLinkActive="active">Live MTMC</a>
          <a routerLink="/analytics" routerLinkActive="active">Analytics</a>
          <a routerLink="/audit" routerLinkActive="active">Audit Logs</a>
        </div>
      </header>
      <main class="main-body">
        <router-outlet></router-outlet>
      </main>
    </div>
  `,
  styles: [`
    .app-layout { display: flex; flex-direction: column; min-height: 100vh; background: #0f172a; }
    .navbar { display: flex; justify-content: space-between; align-items: center; padding: 14px 24px; background: #1e293b; border-bottom: 1px solid #334155; }
    .brand { display: flex; align-items: center; gap: 12px; }
    .logo-badge { background: #3b82f6; color: white; font-weight: 800; padding: 4px 8px; border-radius: 6px; font-size: 14px; }
    .title { font-weight: 600; color: #f8fafc; font-size: 16px; }
    .nav-links { display: flex; gap: 16px; }
    .nav-links a { color: #94a3b8; text-decoration: none; font-size: 14px; font-weight: 500; padding: 6px 12px; border-radius: 6px; transition: all 0.2s; }
    .nav-links a:hover, .nav-links a.active { color: #f8fafc; background: #334155; }
    .main-body { flex: 1; }
  `]
})
export class AppComponent {}
