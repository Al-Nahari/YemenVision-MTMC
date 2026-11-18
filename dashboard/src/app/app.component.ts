import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { ApiService, Camera, Tracklet, DetectionEvent, TrafficAggregate } from './api.service';
import { Observable, interval } from 'rxjs';
import { startWith, switchMap } from 'rxjs/operators';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink, RouterLinkActive],
  template: `
    <div class="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-blue-600 selection:text-white" dir="rtl">
      <!-- Top Enterprise Navigation Bar -->
      <header class="bg-slate-900/80 backdrop-blur-md border-b border-slate-800 sticky top-0 z-50 px-6 py-4 flex items-center justify-between shadow-lg">
        <div class="flex items-center space-x-4 space-x-reverse">
          <div class="bg-blue-600 p-2.5 rounded-xl shadow-blue-500/20 shadow-lg flex items-center justify-center">
            <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
            </svg>
          </div>
          <div>
            <h1 class="text-xl font-bold tracking-tight bg-gradient-to-r from-blue-400 to-indigo-300 bg-clip-text text-transparent">منظومة اليمن فيجن للذكاء المروري</h1>
            <p class="text-xs text-slate-400">YemenVision MTMC & Smart Traffic Command Center</p>
          </div>
        </div>

        <nav class="hidden md:flex items-center space-x-1 space-x-reverse text-sm font-medium">
          <a routerLink="/" routerLinkActive="bg-blue-600 text-white shadow-blue-600/30 shadow-md" [routerLinkActiveOptions]="{exact: true}" class="px-4 py-2 rounded-lg text-slate-300 hover:bg-slate-800 transition">الرئيسية والتحليلات</a>
          <a routerLink="/live" routerLinkActive="bg-blue-600 text-white shadow-blue-600/30 shadow-md" class="px-4 py-2 rounded-lg text-slate-300 hover:bg-slate-800 transition">المراقبة الحية</a>
          <a routerLink="/cameras" routerLinkActive="bg-blue-600 text-white shadow-blue-600/30 shadow-md" class="px-4 py-2 rounded-lg text-slate-300 hover:bg-slate-800 transition">الكاميرات</a>
          <a routerLink="/analytics" routerLinkActive="bg-blue-600 text-white shadow-blue-600/30 shadow-md" class="px-4 py-2 rounded-lg text-slate-300 hover:bg-slate-800 transition">التقارير المرورية</a>
          <a routerLink="/models" routerLinkActive="bg-blue-600 text-white shadow-blue-600/30 shadow-md" class="px-4 py-2 rounded-lg text-slate-300 hover:bg-slate-800 transition">النماذج الذكية</a>
        </nav>

        <div class="flex items-center space-x-3 space-x-reverse">
          <div class="flex items-center bg-emerald-500/10 border border-emerald-500/20 px-3 py-1.5 rounded-full">
            <span class="w-2.5 h-2.5 bg-emerald-500 rounded-full animate-pulse ml-2"></span>
            <span class="text-xs font-semibold text-emerald-400">النظام متصل وآمن</span>
          </div>
        </div>
      </header>

      <!-- Main Content View -->
      <main class="flex-1 p-8 max-w-7xl mx-auto w-full">
        <router-outlet></router-outlet>
      </main>

      <!-- Footer -->
      <footer class="border-t border-slate-900 bg-slate-950 py-4 px-6 text-center text-xs text-slate-500">
        جميع الحقوق محفوظة © 2026 - منظومة اليمن فيجن للرؤية الحاسوبية والذكاء الاصطناعي المروري.
      </footer>
    </div>
  `
})
export class AppComponent {}

@Component({
  selector: 'app-page',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="space-y-8 animate-fadeIn">
      <!-- Welcome Banner -->
      <div class="bg-gradient-to-r from-blue-900/40 via-indigo-950/40 to-slate-900/60 border border-blue-800/30 rounded-2xl p-8 backdrop-blur-xl shadow-2xl relative overflow-hidden">
        <div class="absolute -left-10 -bottom-10 w-64 h-64 bg-blue-600/10 rounded-full blur-3xl pointer-events-none"></div>
        <h2 class="text-3xl font-extrabold text-white mb-2">غرفة العمليات المركزية والتحليلات الذكية</h2>
        <p class="text-slate-300 max-w-2xl text-sm leading-relaxed">متابعة لحظية لحركة المركبات، رصد المخالفات، وتقاطع البيانات الصادرة من نماذج الكشف وإعادة التعرف (ReID) عبر شبكة الكاميرات الموزعة.</p>
      </div>

      <!-- KPI Grid -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div class="bg-slate-900/70 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-md">
          <p class="text-xs font-semibold text-slate-400 mb-1">الكاميرات المتصلة</p>
          <div class="flex items-baseline justify-between">
            <h3 class="text-3xl font-extrabold text-white">4</h3>
            <span class="text-xs font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded">نشطة</span>
          </div>
        </div>
        <div class="bg-slate-900/70 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-md">
          <p class="text-xs font-semibold text-slate-400 mb-1">المركبات المكتشفة اليوم</p>
          <div class="flex items-baseline justify-between">
            <h3 class="text-3xl font-extrabold text-white">1,428</h3>
            <span class="text-xs font-bold text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded">+12.4%</span>
          </div>
        </div>
        <div class="bg-slate-900/70 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-md">
          <p class="text-xs font-semibold text-slate-400 mb-1">المسارات النشطة (Tracklets)</p>
          <div class="flex items-baseline justify-between">
            <h3 class="text-3xl font-extrabold text-white">342</h3>
            <span class="text-xs font-bold text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded">محدث</span>
          </div>
        </div>
        <div class="bg-slate-900/70 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-md">
          <p class="text-xs font-semibold text-slate-400 mb-1">حالة نماذج الذكاء الاصطناعي</p>
          <div class="flex items-baseline justify-between">
            <h3 class="text-3xl font-extrabold text-emerald-400">سليم</h3>
            <span class="text-xs font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded">YOLOv11+ReID</span>
          </div>
        </div>
      </div>

      <!-- Tables Section -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <!-- Tracklets Table -->
        <div class="bg-slate-900/70 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-md">
          <h3 class="text-lg font-bold text-white mb-4 flex items-center">
            <svg class="w-5 h-5 ml-2 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
            أحدث مسارات المركبات المرصودة
          </h3>
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
                <tr class="hover:bg-slate-800/30 transition">
                  <td class="p-3 font-medium text-white">#TRK-9812</td>
                  <td class="p-3">cam_sanae_01</td>
                  <td class="p-3"><span class="bg-blue-500/10 text-blue-400 px-2 py-0.5 rounded text-xs font-semibold">سيارة (Car)</span></td>
                  <td class="p-3 text-slate-400">منذ دقيقتين</td>
                </tr>
                <tr class="hover:bg-slate-800/30 transition">
                  <td class="p-3 font-medium text-white">#TRK-9813</td>
                  <td class="p-3">cam_ring_02</td>
                  <td class="p-3"><span class="bg-indigo-500/10 text-indigo-400 px-2 py-0.5 rounded text-xs font-semibold">باص (Bus)</span></td>
                  <td class="p-3 text-slate-400">منذ 5 دقائق</td>
                </tr>
                <tr class="hover:bg-slate-800/30 transition">
                  <td class="p-3 font-medium text-white">#TRK-9814</td>
                  <td class="p-3">cam_south_03</td>
                  <td class="p-3"><span class="bg-amber-500/10 text-amber-400 px-2 py-0.5 rounded text-xs font-semibold">شاحنة (Truck)</span></td>
                  <td class="p-3 text-slate-400">منذ 10 دقائق</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Detection Events Stream -->
        <div class="bg-slate-900/70 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-md">
          <h3 class="text-lg font-bold text-white mb-4 flex items-center">
            <svg class="w-5 h-5 ml-2 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/></svg>
            سجل أحداث الكشف اللحظي
          </h3>
          <div class="space-y-3">
            <div class="bg-slate-950/60 border border-slate-800/80 p-3.5 rounded-xl flex items-center justify-between">
              <div class="flex items-center space-x-3 space-x-reverse">
                <span class="w-2 h-2 bg-emerald-500 rounded-full"></span>
                <div>
                  <p class="text-sm font-semibold text-white">رصد مركبة جديدة عبر نموذج YOLOv11m</p>
                  <p class="text-xs text-slate-400">الكاميرا: cam_sanae_01 | الثقة: 92%</p>
                </div>
              </div>
              <span class="text-xs text-slate-500">الان</span>
            </div>
            <div class="bg-slate-950/60 border border-slate-800/80 p-3.5 rounded-xl flex items-center justify-between">
              <div class="flex items-center space-x-3 space-x-reverse">
                <span class="w-2 h-2 bg-blue-500 rounded-full"></span>
                <div>
                  <p class="text-sm font-semibold text-white">مطابقة ناجحة عبر ReID متعدد الكاميرات</p>
                  <p class="text-xs text-slate-400">تم التعرف على السيارة في تقاطع الدائري</p>
                </div>
              </div>
              <span class="text-xs text-slate-500">منذ 3 دقائق</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  `
})
export class PageComponent implements OnInit {
  constructor(public api: ApiService) {}
  ngOnInit() {}
}
