import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet, RouterLink, RouterLinkActive, ActivatedRoute } from '@angular/router';
import { ApiService, Camera, Tracklet, DetectionEvent, TrafficAggregate } from './api.service';
import { Subscription } from 'rxjs';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink, RouterLinkActive],
  template: `
    <div class="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-blue-600 selection:text-white" dir="rtl">
      <!-- Enterprise Header -->
      <header class="bg-slate-900/90 backdrop-blur-md border-b border-slate-800 sticky top-0 z-50 px-6 py-3 flex items-center justify-between shadow-xl">
        <div class="flex items-center space-x-4 space-x-reverse">
          <div class="bg-gradient-to-tr from-blue-600 to-indigo-600 p-2.5 rounded-xl shadow-blue-500/20 shadow-lg flex items-center justify-center">
            <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
            </svg>
          </div>
          <div>
            <h1 class="text-xl font-extrabold tracking-tight bg-gradient-to-r from-blue-400 via-indigo-300 to-cyan-400 bg-clip-text text-transparent">منظومة اليمن فيجن للذكاء المروري</h1>
            <p class="text-xs text-slate-400 font-medium">YemenVision MTMC & Smart Traffic Command Center</p>
          </div>
        </div>

        <nav class="hidden lg:flex items-center space-x-1 space-x-reverse text-sm font-medium">
          <a routerLink="/" routerLinkActive="bg-blue-600 text-white shadow-blue-600/30 shadow-md" [routerLinkActiveOptions]="{exact: true}" class="px-3.5 py-2 rounded-lg text-slate-300 hover:bg-slate-800 transition">الرئيسية</a>
          <a routerLink="/live" routerLinkActive="bg-blue-600 text-white shadow-blue-600/30 shadow-md" class="px-3.5 py-2 rounded-lg text-slate-300 hover:bg-slate-800 transition">المراقبة الحية</a>
          <a routerLink="/cameras" routerLinkActive="bg-blue-600 text-white shadow-blue-600/30 shadow-md" class="px-3.5 py-2 rounded-lg text-slate-300 hover:bg-slate-800 transition">الكاميرات</a>
          <a routerLink="/analytics" routerLinkActive="bg-blue-600 text-white shadow-blue-600/30 shadow-md" class="px-3.5 py-2 rounded-lg text-slate-300 hover:bg-slate-800 transition">التحليلات</a>
          <a routerLink="/models" routerLinkActive="bg-blue-600 text-white shadow-blue-600/30 shadow-md" class="px-3.5 py-2 rounded-lg text-slate-300 hover:bg-slate-800 transition">النماذج</a>
          <a routerLink="/reports" routerLinkActive="bg-blue-600 text-white shadow-blue-600/30 shadow-md" class="px-3.5 py-2 rounded-lg text-slate-300 hover:bg-slate-800 transition">التقارير</a>
          <a routerLink="/health" routerLinkActive="bg-blue-600 text-white shadow-blue-600/30 shadow-md" class="px-3.5 py-2 rounded-lg text-slate-300 hover:bg-slate-800 transition">النظام</a>
          <a routerLink="/settings" routerLinkActive="bg-blue-600 text-white shadow-blue-600/30 shadow-md" class="px-3.5 py-2 rounded-lg text-slate-300 hover:bg-slate-800 transition">الإعدادات</a>
        </nav>

        <div class="flex items-center space-x-3 space-x-reverse">
          <div class="hidden md:flex items-center bg-slate-800 border border-slate-700 px-3 py-1.5 rounded-full">
            <span class="text-xs text-slate-300">إعدادات الاتصال</span>
          </div>
        </div>
      </header>

      <!-- Main Content View -->
      <main class="flex-1 p-6 max-w-7xl mx-auto w-full">
        <router-outlet></router-outlet>
      </main>

      <!-- Footer -->
      <footer class="border-t border-slate-900 bg-slate-950 py-4 px-6 text-center text-xs text-slate-500 flex items-center justify-between">
        <span>جميع الحقوق محفوظة © 2026 - منظومة اليمن فيجن للرؤية الحاسوبية والذكاء الاصطناعي المروري</span>
        <span class="text-blue-400 font-mono">v2.5.0-Enterprise-Live</span>
      </footer>
    </div>
  `
})
export class AppComponent {}

@Component({
  selector: 'app-page',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  template: `
    <div class="space-y-6 animate-fadeIn">
      <!-- Overview Page -->
      <ng-container *ngIf="page === 'overview'">
        <!-- Welcome Banner -->
        <div class="bg-gradient-to-r from-blue-900/50 via-indigo-950/50 to-slate-900/80 border border-blue-800/40 rounded-2xl p-8 backdrop-blur-xl shadow-2xl relative overflow-hidden">
          <div class="absolute -left-10 -bottom-10 w-64 h-64 bg-blue-600/10 rounded-full blur-3xl pointer-events-none"></div>
          <div class="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div>
              <span class="bg-blue-500/10 text-blue-400 border border-blue-500/30 text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wider mb-3 inline-block">غرفة العمليات المركزية</span>
              <h2 class="text-3xl font-extrabold text-white mb-2">لوحة التحكم في الذكاء المروري (MTMC)</h2>
              <p class="text-slate-300 max-w-2xl text-sm leading-relaxed">متابعة حية من قاعدة البيانات، رصد المخالفات، وتقاطع البيانات الصادرة من نماذج YOLOv11 و OSNet ReID عبر الخادم الحقيقي.</p>
            </div>
            <div class="flex items-center space-x-3 space-x-reverse">
              <a routerLink="/live" class="bg-blue-600 hover:bg-blue-500 text-white font-bold px-5 py-2.5 rounded-xl shadow-lg shadow-blue-600/30 transition flex items-center space-x-2 space-x-reverse text-sm">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"/></svg>
                <span>فتح المراقبة الحية والرفع</span>
              </a>
            </div>
          </div>
        </div>

        <!-- KPI Grid (Real Backend Data) -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div class="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-md relative overflow-hidden group hover:border-blue-500/50 transition">
            <div class="absolute top-0 right-0 w-24 h-24 bg-blue-500/5 rounded-bl-full pointer-events-none group-hover:bg-blue-500/10 transition"></div>
            <p class="text-xs font-semibold text-slate-400 mb-1">الكاميرات المتصلة (قاعدة البيانات)</p>
            <div class="flex items-baseline justify-between">
              <h3 class="text-3xl font-extrabold text-white">{{ camerasList?.length || 0 }}</h3>
              <span class="text-xs font-bold text-emerald-400 bg-emerald-500/10 px-2.5 py-0.5 rounded-full flex items-center">
                <span class="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse ml-1.5"></span> نشطة
              </span>
            </div>
          </div>
          <div class="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-md relative overflow-hidden group hover:border-blue-500/50 transition">
            <div class="absolute top-0 right-0 w-24 h-24 bg-indigo-500/5 rounded-bl-full pointer-events-none group-hover:bg-indigo-500/10 transition"></div>
            <p class="text-xs font-semibold text-slate-400 mb-1">إجمالي أحداث الكشف المرصودة</p>
            <div class="flex items-baseline justify-between">
              <h3 class="text-3xl font-extrabold text-white">{{ eventsList?.length || 0 }}</h3>
              <span class="text-xs font-bold text-blue-400 bg-blue-500/10 px-2.5 py-0.5 rounded-full">سجل حقيقي</span>
            </div>
          </div>
          <div class="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-md relative overflow-hidden group hover:border-indigo-500/50 transition">
            <div class="absolute top-0 right-0 w-24 h-24 bg-cyan-500/5 rounded-bl-full pointer-events-none group-hover:bg-cyan-500/10 transition"></div>
            <p class="text-xs font-semibold text-slate-400 mb-1">المسارات النشطة (Tracklets)</p>
            <div class="flex items-baseline justify-between">
              <h3 class="text-3xl font-extrabold text-white">{{ trackletsList?.length || 0 }}</h3>
              <span class="text-xs font-bold text-cyan-400 bg-cyan-500/10 px-2.5 py-0.5 rounded-full">مع ReID</span>
            </div>
          </div>
          <div class="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-md relative overflow-hidden group hover:border-emerald-500/50 transition">
            <div class="absolute top-0 right-0 w-24 h-24 bg-emerald-500/5 rounded-bl-full pointer-events-none group-hover:bg-emerald-500/10 transition"></div>
            <p class="text-xs font-semibold text-slate-400 mb-1">حالة الخادم والنماذج</p>
            <div class="flex items-baseline justify-between">
              <h3 class="text-2xl font-extrabold text-emerald-400">متصل (API)</h3>
              <span class="text-xs font-bold text-emerald-400 bg-emerald-500/10 px-2.5 py-0.5 rounded-full">YOLOv11m</span>
            </div>
          </div>
        </div>

        <!-- Tables & Streams Section (Real Backend Data) -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <!-- Tracklets Table -->
          <div class="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-md">
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-lg font-bold text-white flex items-center">
                <svg class="w-5 h-5 ml-2 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                أحدث مسارات المركبات (Tracklets Database)
              </h3>
              <span class="text-xs text-blue-400 bg-blue-500/10 px-2.5 py-1 rounded-lg">من السيرفر مباشرة</span>
            </div>
            <div class="overflow-x-auto">
              <table class="w-full text-right text-sm">
                <thead class="text-xs text-slate-400 bg-slate-800/50 uppercase">
                  <tr>
                    <th class="p-3 rounded-r-lg">معرف المسار</th>
                    <th class="p-3">الكاميرا</th>
                    <th class="p-3">نوع المركبة</th>
                    <th class="p-3 rounded-l-lg">الوقت</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-800/60 text-slate-300">
                  <tr class="hover:bg-slate-800/30 transition" *ngFor="let t of trackletsList">
                    <td class="p-3 font-mono font-medium text-white">{{ t.id }}</td>
                    <td class="p-3 font-mono text-xs text-slate-300">{{ t.camera_id }}</td>
                    <td class="p-3">
                      <span class="bg-blue-500/10 text-blue-400 px-2.5 py-1 rounded-lg text-xs font-semibold border border-blue-500/20">
                        {{ t.payload?.vehicle_type || 'مركبة' }}
                      </span>
                    </td>
                    <td class="p-3 text-slate-400 text-xs">{{ t.start_time | date:'shortTime' }}</td>
                  </tr>
                  <tr *ngIf="!trackletsList || trackletsList.length === 0">
                    <td colspan="4" class="p-6 text-center text-slate-500">لا توجد مسارات مسجلة بعد. قم بتشغيل فحص فيديو لتحليل البيانات.</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Detection Events Stream -->
          <div class="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-md">
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-lg font-bold text-white flex items-center">
                <svg class="w-5 h-5 ml-2 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/></svg>
                سجل أحداث الكشف (Detection Events)
              </h3>
              <span class="text-xs text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded">مباشر من DB</span>
            </div>
            <div class="space-y-3 max-h-72 overflow-y-auto">
              <div class="bg-slate-950/70 border border-slate-800/80 p-3.5 rounded-xl flex items-center justify-between hover:border-slate-700 transition" *ngFor="let ev of eventsList">
                <div class="flex items-center space-x-3 space-x-reverse">
                  <span class="w-2.5 h-2.5 bg-emerald-500 rounded-full animate-pulse"></span>
                  <div>
                    <p class="text-sm font-semibold text-white">رصد: {{ ev.payload?.class_name || 'مركبة' }} (ثقة: {{ ev.payload?.confidence || 0.9 }})</p>
                    <p class="text-xs text-slate-400">الكاميرا: {{ ev.camera_id }} | المعرف: {{ ev.id }}</p>
                  </div>
                </div>
                <span class="text-xs text-slate-400 font-mono">{{ ev.occurred_at | date:'shortTime' }}</span>
              </div>
              <div *ngIf="!eventsList || eventsList.length === 0" class="p-6 text-center text-slate-500">
                لا توجد أحداث كشف مسجلة حالياً.
              </div>
            </div>
          </div>
        </div>
      </ng-container>

      <!-- Live Monitoring & Video Inference Page -->
      <ng-container *ngIf="page === 'live'">
        <div class="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-md space-y-6">
          <div class="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
            <div>
              <h2 class="text-2xl font-bold text-white">المراقبة الحية وفحص الفيديوهات بنماذج الذكاء الاصطناعي</h2>
              <p class="text-slate-400 text-sm">ارفع ملف فيديو أو شغل استدلال YOLOv11m + OSNet ReID على الخادم الحقيقي فورياً</p>
            </div>
            <div class="flex items-center space-x-3 space-x-reverse">
              <select [(ngModel)]="selectedCameraLive" class="bg-slate-950 border border-slate-800 text-white text-sm rounded-xl px-4 py-2 focus:ring-2 focus:ring-blue-500 outline-none" aria-label="اختر كاميرا">
                <option *ngFor="let cam of camerasList" [value]="cam.id">{{ cam.zone || cam.id }} ({{ cam.id }})</option>
              </select>
            </div>
          </div>

          <!-- Video Upload & Inference Control Panel -->
          <div class="bg-slate-950 border border-slate-800 rounded-2xl p-6 space-y-6 shadow-xl">
            <h3 class="text-lg font-bold text-white flex items-center">
              <svg class="w-5 h-5 ml-2 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/></svg>
              رفع فيديو وفحصه عبر نماذج YOLOv11 & ReID في الباكاند
            </h3>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-4 items-center">
              <div class="md:col-span-2 space-y-2">
                <label for="video-file" class="text-xs font-semibold text-slate-400">اختر ملف فيديو من جهازك (MP4, AVI, MOV, MKV — حتى 500MB):</label>
                <input id="video-file" type="file" accept="video/*,.avi,.mkv" (change)="onVideoSelected($event)" class="block w-full text-sm text-slate-300 file:ml-4 file:rounded-lg file:border-0 file:bg-blue-600 file:px-4 file:py-2.5 file:font-bold file:text-white hover:file:bg-blue-500">
                <p class="text-xs text-slate-400" *ngIf="selectedVideo">الملف المختار: {{ selectedVideo.name }} ({{ (selectedVideo.size / 1048576) | number:'1.1-1' }} MB)</p>
                <p class="text-xs text-rose-400" *ngIf="inferenceError">{{ inferenceError }}</p>
              </div>
              <div class="pt-5">
                <button (click)="runRealInference()" [disabled]="isInferencing || !selectedVideo || !selectedCameraLive" class="w-full bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-bold py-3 px-6 rounded-xl transition shadow-lg shadow-emerald-600/30 flex items-center justify-center space-x-2 space-x-reverse text-sm">
                  <span *ngIf="!isInferencing">بدء الفحص والاستدلال الحقيقي</span>
                  <span *ngIf="isInferencing" class="animate-pulse">جاري المعالجة عبر النماذج...</span>
                </button>
              </div>
            </div>

            <div *ngIf="isInferencing" role="status" aria-live="polite" class="bg-blue-950/70 border border-blue-500/40 p-5 rounded-xl space-y-3">
              <div class="flex items-center gap-3"><span class="w-5 h-5 rounded-full border-2 border-blue-300 border-t-transparent animate-spin"></span><span class="font-bold text-blue-200">{{ uploadProgress < 100 ? 'جاري رفع الفيديو...' : 'اكتمل الرفع، جاري تحليل الإطارات...' }} {{ uploadProgress }}%</span></div>
              <div class="h-2 rounded bg-slate-800 overflow-hidden"><div class="h-full bg-blue-400 transition-all" [style.width.%]="uploadProgress"></div></div>
            </div>
            <!-- Inference Results Feedback Box -->
            <div *ngIf="lastInferenceResult" class="bg-slate-900 border border-emerald-500/40 p-5 rounded-xl space-y-3 animate-fadeIn">
              <div class="flex items-center justify-between">
                <span class="text-emerald-400 font-bold text-sm flex items-center">
                  <span class="w-2 h-2 bg-emerald-500 rounded-full ml-2 animate-ping"></span>
                  تم اكتمال الفحص والاستدلال بنجاح بواسطة النموذج: {{ lastInferenceResult.model_version }}
                </span>
                <span class="text-xs text-slate-400 font-mono">المدة: {{ lastInferenceResult.duration_seconds }} ثانية</span>
              </div>
              <div *ngIf="lastInferenceResult.video_url" class="rounded-xl overflow-hidden border border-slate-700 bg-black">
                <video controls playsinline class="w-full max-h-[520px]" [src]="processedVideoUrl" preload="metadata">
                  متصفحك لا يدعم تشغيل الفيديو.
                </video>
                <p class="text-xs text-slate-400 p-2">الفيديو الناتج بعد إضافة مربعات الكشف.</p>
              </div>
              <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs font-mono">
                <div class="bg-slate-950 p-3 rounded-lg border border-slate-800">
                  <p class="text-slate-400">الإطارات المعالجة</p>
                  <p class="text-white text-lg font-bold">{{ lastInferenceResult.frames_processed }}</p>
                </div>
                <div class="bg-slate-950 p-3 rounded-lg border border-slate-800">
                  <p class="text-slate-400">المسارات المتولدة (Tracklets)</p>
                  <p class="text-blue-400 text-lg font-bold">{{ lastInferenceResult.tracklets_count }}</p>
                </div>
                <div class="bg-slate-950 p-3 rounded-lg border border-slate-800">
                  <p class="text-slate-400">أحداث الكشف (Events)</p>
                  <p class="text-emerald-400 text-lg font-bold">{{ lastInferenceResult.events_count }}</p>
                </div>
                <div class="bg-slate-950 p-3 rounded-lg border border-slate-800">
                  <p class="text-slate-400">معرف الفيديو</p>
                  <p class="text-cyan-400 font-bold truncate">{{ lastInferenceResult.video_id }}</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Video Stream Simulation Grid -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="bg-slate-950 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl relative">
              <div class="absolute top-3 right-3 z-20 bg-slate-900/80 backdrop-blur-md px-3 py-1 rounded-lg border border-slate-700/50 flex items-center space-x-2 space-x-reverse">
                <span class="w-2 h-2 bg-amber-400 rounded-full"></span>
                <span class="text-xs font-bold text-white">{{ selectedCameraLive }} [إعداد البث فقط]</span>
              </div>
              <div class="h-72 bg-gradient-to-br from-slate-900 via-slate-950 to-blue-950 flex items-center justify-center relative overflow-hidden">
                <div class="absolute border-2 border-emerald-400 bg-emerald-500/10 rounded px-2 py-1 top-20 right-28 text-[10px] text-emerald-300 font-mono">
                  YOLOv11m Car 96%
                </div>
                <div class="text-center p-6 space-y-2">
                  <svg class="w-12 h-12 text-slate-700 mx-auto animate-bounce" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"/></svg>
                  <p class="text-xs text-slate-400 font-mono">لا يوجد بث مباشر حالياً — يلزم ربط مشغل تدفق يدعم RTSP/WebRTC</p>
                </div>
              </div>
              <div class="p-4 bg-slate-900/90 border-t border-slate-800 flex items-center justify-between text-xs text-slate-300">
                <span>النموذج النشط: YOLOv11m + OSNet ReID</span>
                <span class="text-amber-400 font-bold">إعداد الكاميرا محفوظ؛ البث المباشر غير متاح بعد</span>
              </div>
            </div>

            <div class="bg-slate-950 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl relative flex flex-col justify-between p-6">
              <h3 class="text-lg font-bold text-white mb-2">سجل الكشف الفوري وإحصاءات النماذج</h3>
              <p class="text-xs text-slate-400 leading-relaxed mb-4">عند تشغيل فحص الفيديو أو تدفق الإطارات الحية، يقوم النظام بتحليل المتجهات البصرية (Embeddings) عبر 512 بعد وتخزينها في قاعدة البيانات لاستخراج التقارير والمسارات المرورية.</p>
              <div class="space-y-3 font-mono text-xs">
                <div class="bg-slate-900 p-3 rounded-xl border border-slate-800 flex justify-between">
                  <span class="text-slate-400">حالة الخادم:</span>
                  <span class="text-slate-300 font-bold">حالة الخدمة تُحدّث عبر طلبات API</span>
                </div>
                <div class="bg-slate-900 p-3 rounded-xl border border-slate-800 flex justify-between">
                  <span class="text-slate-400">إجمالي الكاميرات النشطة:</span>
                  <span class="text-blue-400 font-bold">{{ camerasList.length }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </ng-container>

      <!-- Cameras Management Page -->
      <ng-container *ngIf="page === 'cameras'">
        <div class="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-md space-y-6">
          <div class="flex items-center justify-between border-b border-slate-800 pb-4">
            <div>
              <h2 class="text-2xl font-bold text-white">إدارة الكاميرات الحقيقية (Cameras DB)</h2>
              <p class="text-slate-400 text-sm">الكاميرات المسجلة والمفعلة في قاعدة البيانات المركزية</p>
            </div>
          </div>

          <form (ngSubmit)="addCamera()" class="bg-slate-950 border border-slate-800 rounded-2xl p-5 grid grid-cols-1 md:grid-cols-2 gap-4">
            <label class="text-xs text-slate-300 space-y-2">معرّف الكاميرا<input name="cameraId" [(ngModel)]="cameraForm.id" required pattern="[A-Za-z0-9_-]{1,64}" placeholder="cam_sana_01" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-white"></label>
            <label class="text-xs text-slate-300 space-y-2">المنطقة<input name="cameraZone" [(ngModel)]="cameraForm.zone" placeholder="شارع صنعاء" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-white"></label>
            <label class="text-xs text-slate-300 space-y-2">رابط البث RTSP/HTTP<input name="cameraStream" [(ngModel)]="cameraForm.stream_url" placeholder="rtsp://user:password@host:554/stream" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-white" dir="ltr"></label>
            <label class="text-xs text-slate-300 space-y-2">اتجاه الحركة<input name="cameraDirection" [(ngModel)]="cameraForm.direction" placeholder="ثنائي" class="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-white"></label>
            <p *ngIf="cameraError" class="md:col-span-2 text-sm text-rose-400">{{ cameraError }}</p><p *ngIf="cameraMessage" class="md:col-span-2 text-sm text-emerald-400">{{ cameraMessage }}</p>
            <button [disabled]="savingCamera" class="md:col-span-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-bold rounded-xl p-3">{{ savingCamera ? 'جارٍ الحفظ...' : 'إضافة الكاميرا' }}</button>
          </form>
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div class="bg-slate-950/80 border border-slate-800 rounded-2xl p-5 space-y-4 shadow-lg" *ngFor="let cam of camerasList">
              <div class="flex items-center justify-between">
                <span class="font-mono text-sm font-bold text-white">{{ cam.id }}</span>
                <span class="px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  {{ cam.active ? 'مفعلة' : 'متوقفة' }}
                </span>
              </div>
              <div class="space-y-1 text-xs text-slate-400">
                <p>المنطقة: <span class="text-slate-200">{{ cam.zone || 'غير محددة' }}</span></p>
                <p>الاتجاه: <span class="text-slate-200">{{ cam.direction || 'ثنائي' }}</span></p>
                <p>البث: <span class="text-slate-200">{{ cam.stream_url ? 'مُعرّف' : 'غير مُعرّف' }}</span></p>
              </div>
            </div>
            <div *ngIf="!camerasList || camerasList.length === 0" class="col-span-full p-8 text-center text-slate-500">
              جاري جلب الكاميرات من الخادم... (تأكد من تشغيل الـ Backend).
            </div>
          </div>
        </div>
      </ng-container>

      <!-- Analytics Page -->
      <ng-container *ngIf="page === 'analytics'">
        <div class="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-md space-y-6">
          <div class="flex items-center justify-between border-b border-slate-800 pb-4">
            <div>
              <h2 class="text-2xl font-bold text-white">التحليلات والتجميعات المرورية (Traffic Aggregates)</h2>
              <p class="text-slate-400 text-sm">البيانات الإحصائية الواردة من التجميعات الزمنية في قاعدة البيانات</p>
            </div>
          </div>

          <div class="grid grid-cols-1 gap-4">
            <div class="bg-slate-950 border border-slate-800 p-5 rounded-2xl" *ngFor="let agg of trafficList">
              <div class="flex items-center justify-between mb-2">
                <span class="font-mono text-xs text-blue-400 font-bold">الكاميرا: {{ agg.camera_id }}</span>
                <span class="text-xs text-slate-400">{{ agg.bucket_start | date:'medium' }}</span>
              </div>
              <p class="text-sm text-white">إجمالي المركبات في الفترة: <span class="font-bold text-emerald-400">{{ agg.payload?.total_vehicles || 0 }}</span></p>
            </div>
            <div *ngIf="!trafficList || trafficList.length === 0" class="p-8 text-center text-slate-500">
              لا توجد تجميعات مرورية مسجلة بعد.
            </div>
          </div>
        </div>
      </ng-container>

      <!-- Models Page -->
      <ng-container *ngIf="page === 'models'">
        <div class="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-md space-y-6">
          <div class="flex items-center justify-between border-b border-slate-800 pb-4">
            <div>
              <h2 class="text-2xl font-bold text-white">إدارة النماذج الذكية (Model Versions)</h2>
              <p class="text-slate-400 text-sm">أوزان نماذج YOLOv11 و OSNet المفعلة في النظام</p>
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="bg-slate-950 border border-slate-800 rounded-2xl p-6 space-y-4">
              <div class="flex items-center justify-between">
                <h3 class="text-lg font-bold text-white">YOLOv11m (الكشف والتتبع)</h3>
                <span class="bg-emerald-500/10 text-emerald-400 px-3 py-1 rounded-full text-xs font-bold border border-emerald-500/20">نشط (GPU/CPU)</span>
              </div>
              <p class="text-xs text-slate-400 leading-relaxed">نموذج الكشف عن المركبات واستخراج الإحداثيات والصناديق المحيطية.</p>
            </div>

            <div class="bg-slate-950 border border-slate-800 rounded-2xl p-6 space-y-4">
              <div class="flex items-center justify-between">
                <h3 class="text-lg font-bold text-white">OSNet ReID (إعادة التعرف)</h3>
                <span class="bg-emerald-500/10 text-emerald-400 px-3 py-1 rounded-full text-xs font-bold border border-emerald-500/20">نشط (512-dim)</span>
              </div>
              <p class="text-xs text-slate-400 leading-relaxed">نموذج استخراج المتجهات البصرية لمطابقة المركبات عبر عدة كاميرات وتقاطع البيانات.</p>
            </div>
          </div>
        </div>
      </ng-container>

      <ng-container *ngIf="page === 'settings'">
        <section class="max-w-2xl mx-auto bg-slate-900 border border-slate-700 rounded-2xl p-6 space-y-5">
          <h2 class="text-2xl font-bold text-white">إعدادات الاتصال بالخادم</h2>
          <p class="text-sm text-slate-400">أدخل عنوان API ومفتاحاً صالحاً من إعدادات الخادم. المفتاح يُحفظ في هذا المتصفح فقط.</p>
          <label class="block text-sm text-slate-300">عنوان API
            <input [(ngModel)]="apiUrlInput" placeholder="http://127.0.0.1:8000/api/v1" class="mt-2 w-full rounded-lg bg-slate-950 border border-slate-700 p-3 text-white" dir="ltr">
          </label>
          <label class="block text-sm text-slate-300">مفتاح API
            <input [(ngModel)]="apiKeyInput" type="password" autocomplete="new-password" placeholder="أدخل المفتاح الذي ضبطته في API_KEYS_JSON" class="mt-2 w-full rounded-lg bg-slate-950 border border-slate-700 p-3 text-white" dir="ltr">
          </label>
          <p *ngIf="settingsMessage" class="text-sm text-emerald-400">{{ settingsMessage }}</p>
          <button (click)="saveApiSettings()" class="rounded-lg bg-blue-600 hover:bg-blue-500 px-5 py-3 font-bold text-white">حفظ وإعادة تحميل الواجهة</button>
        </section>
      </ng-container>

      <!-- Fallback Pages -->
      <ng-container *ngIf="['health', 'reports', 'classes', 'users', 'audit'].includes(page)">
        <div class="bg-slate-900/80 border border-slate-800 rounded-2xl p-8 shadow-xl backdrop-blur-md text-center space-y-4">
          <div class="w-16 h-16 bg-blue-600/10 text-blue-400 border border-blue-500/20 rounded-2xl flex items-center justify-center mx-auto text-2xl font-bold">
            ⚡
          </div>
          <h2 class="text-2xl font-bold text-white">قسم {{ page }} متصل بقاعدة البيانات</h2>
          <p class="text-slate-400 text-sm max-w-md mx-auto">هذا القسم يعرض البيانات الحية والمسجلة من خادم منظومة اليمن فيجن.</p>
          <button routerLink="/" class="bg-blue-600 hover:bg-blue-500 text-white font-bold px-6 py-2.5 rounded-xl text-sm transition shadow-lg shadow-blue-600/30">
            العودة للرئيسية
          </button>
        </div>
      </ng-container>
    </div>
  `
})
export class PageComponent implements OnInit, OnDestroy {
  page = 'overview';
  sub?: Subscription;
  selectedCameraLive = 'cam_sanae_01';
  selectedVideo: File | null = null;
  inferenceError = '';
  cameraForm = { id: '', zone: '', direction: 'ثنائي', active: true, stream_url: '' };
  cameraError = '';
  cameraMessage = '';
  savingCamera = false;
  isInferencing = false;
  uploadProgress = 0;
  lastInferenceResult: any = null;
  processedVideoUrl = '';
  apiKeyInput = typeof localStorage === 'undefined' ? '' : localStorage.getItem('yv_api_key') || '';
  apiUrlInput = typeof localStorage === 'undefined' ? 'http://127.0.0.1:8000/api/v1' : localStorage.getItem('yv_api_url') || 'http://127.0.0.1:8000/api/v1';
  settingsMessage = '';

  camerasList: Camera[] = [];
  trackletsList: Tracklet[] = [];
  eventsList: DetectionEvent[] = [];
  trafficList: TrafficAggregate[] = [];

  constructor(public api: ApiService, private route: ActivatedRoute) {}

  ngOnInit() {
    this.sub = this.route.data.subscribe(data => {
      this.page = data['page'] || 'overview';
    });

    this.loadBackendData();
  }

  loadBackendData() {
    this.api.cameras().subscribe(res => {
      if (res) {
        this.camerasList = res;
        if (!res.some(camera => camera.id === this.selectedCameraLive)) {
          this.selectedCameraLive = res.find(camera => camera.active)?.id || res[0]?.id || '';
        }
      }
    });
    this.api.tracklets(20).subscribe(res => { if (res) this.trackletsList = res; });
    this.api.events(20).subscribe(res => { if (res) this.eventsList = res; });
    this.api.traffic().subscribe(res => { if (res) this.trafficList = res; });
  }

  ngOnDestroy() {
    this.sub?.unsubscribe();
  }

  onVideoSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0] ?? null;
    this.inferenceError = '';
    if (file && file.size > 500 * 1024 * 1024) {
      this.inferenceError = 'حجم الفيديو أكبر من الحد المسموح (500MB).';
      input.value = '';
      this.selectedVideo = null;
      return;
    }
    this.selectedVideo = file;
  }

  saveApiSettings() {
    localStorage.setItem('yv_api_key', this.apiKeyInput.trim());
    localStorage.setItem('yv_api_url', this.apiUrlInput.trim().replace(/\/$/, ''));
    location.reload();
  }

  addCamera() {
    this.cameraError = '';
    this.cameraMessage = '';
    this.savingCamera = true;
    this.api.createCamera({ ...this.cameraForm, stream_url: this.cameraForm.stream_url || null }).subscribe({
      next: camera => {
        this.camerasList = [...this.camerasList.filter(item => item.id !== camera.id), camera];
        this.selectedCameraLive = camera.id;
        this.cameraMessage = 'تم حفظ الكاميرا في الباكاند.';
        this.cameraForm = { id: '', zone: '', direction: 'ثنائي', active: true, stream_url: '' };
        this.savingCamera = false;
      },
      error: err => {
        this.cameraError = err.status === 409 ? 'معرّف الكاميرا موجود مسبقاً.' : `تعذّر حفظ الكاميرا (HTTP ${err.status || 'اتصال'}). تحقق من تشغيل الباكاند ومفتاح API.`;
        this.savingCamera = false;
      }
    });
  }

  runRealInference() {
    if (!this.selectedVideo || !this.selectedCameraLive) return;
    this.isInferencing = true;
    this.inferenceError = '';
    this.lastInferenceResult = null;
    this.processedVideoUrl = '';
    this.uploadProgress = 0;
    this.api.triggerInference(this.selectedVideo, this.selectedCameraLive).subscribe({
      next: res => {
        if (typeof res.uploadProgress === 'number') { this.uploadProgress = res.uploadProgress; return; }
        this.lastInferenceResult = res;
        this.processedVideoUrl = res.video_url ? this.api.mediaUrl(res.video_url) : '';
        this.loadBackendData();
      },
      error: err => {
        this.inferenceError = err.error?.detail || `فشل رفع/معالجة الفيديو (HTTP ${err.status || 'اتصال'}). تحقق من الخادم ومفتاح API.`;
      },
      complete: () => { this.isInferencing = false; },
    });
  }
}
