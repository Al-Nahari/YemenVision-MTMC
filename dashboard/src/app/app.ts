import { Component } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'yv-app-shell',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink, RouterLinkActive],
  template: `
    <div class="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans" dir="rtl">
      <header class="sticky top-0 z-50 border-b border-slate-800 bg-slate-900 px-5 py-4 shadow-xl">
        <div class="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4">
          <a routerLink="/" class="text-lg font-extrabold text-blue-300">YemenVision | غرفة العمليات المرورية</a>
          <nav class="flex flex-wrap gap-2 text-sm" aria-label="التنقل الرئيسي">
            <a *ngFor="let item of navigation" [routerLink]="item.path" routerLinkActive="bg-blue-600 text-white" [routerLinkActiveOptions]="{exact: item.path === '/'}" class="rounded-lg px-3 py-2 text-slate-200 hover:bg-slate-700">{{ item.label }}</a>
          </nav>
        </div>
      </header>
      <main class="mx-auto w-full max-w-7xl flex-1 p-4 md:p-6">
        <router-outlet />
      </main>
      <footer class="border-t border-slate-800 px-5 py-4 text-center text-xs text-slate-400">YemenVision MTMC · منصة تحليل مروري</footer>
    </div>
  `,
})
export class App {
  readonly navigation = [
    { path: '/', label: 'الرئيسية' },
    { path: '/live', label: 'المراقبة الحية' },
    { path: '/cameras', label: 'الكاميرات' },
    { path: '/analytics', label: 'التحليلات' },
    { path: '/models', label: 'النماذج' },
    { path: '/reports', label: 'التقارير' },
    { path: '/health', label: 'حالة النظام' },
    { path: '/settings', label: 'الإعدادات' },
    { path: '/audit', label: 'سجل التدقيق' },
    { path: '/users', label: 'المستخدمون' },
    { path: '/classes', label: 'الفئات' },
  ];
}
