import { Component, lazy, Suspense, useEffect, useState, type ErrorInfo, type ReactNode } from 'react';
import { Link, NavLink, Navigate, Route, Routes } from 'react-router-dom';

// Route-level code splitting keeps the initial dashboard bundle small. Heavy
// pages (archive, analytics and live processing) are downloaded only when
// opened, which matters on weak machines and slow local networks.
const OverviewPage = lazy(() => import('./pages/OverviewPage'));
const LivePage = lazy(() => import('./pages/LivePage'));
const CamerasPage = lazy(() => import('./pages/CamerasPage'));
const VideosPage = lazy(() => import('./pages/VideosPage'));
const PlatesPage = lazy(() => import('./pages/PlatesPage'));
const AnalyticsPage = lazy(() => import('./pages/AnalyticsPage'));
const ModelsPage = lazy(() => import('./pages/ModelsPage'));
const SettingsPage = lazy(() => import('./pages/SettingsPage'));
const PlaceholderPage = lazy(() => import('./pages/PlaceholderPage'));

const navigation = [
  { path: '/', label: 'الرئيسية' },
  { path: '/live', label: 'المراقبة الحية' },
  { path: '/cameras', label: 'الكاميرات' },
  { path: '/videos', label: 'أرشيف الفيديو' },
  { path: '/plates', label: 'اللوحات' },
  { path: '/analytics', label: 'التحليلات' },
  { path: '/models', label: 'النماذج' },
  { path: '/reports', label: 'التقارير' },
  { path: '/health', label: 'حالة النظام' },
  { path: '/settings', label: 'الإعدادات' },
  { path: '/audit', label: 'سجل التدقيق' },
  { path: '/users', label: 'المستخدمون' },
  { path: '/classes', label: 'الفئات' },
];

const placeholderTitles: Record<string, string> = {
  reports: 'التقارير',
  health: 'حالة النظام',
  audit: 'سجل التدقيق',
  users: 'المستخدمون',
  classes: 'الفئات',
};

type ErrorBoundaryState = { error: Error | null };

class DashboardErrorBoundary extends Component<{ children: ReactNode }, ErrorBoundaryState> {
  state: ErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('Dashboard render error', error, info);
  }

  render() {
    if (this.state.error) {
      return (
        <div dir="rtl" className="flex min-h-screen items-center justify-center bg-slate-950 p-6 text-slate-100">
          <div className="w-full max-w-xl rounded-2xl border border-rose-500/40 bg-slate-900 p-6 text-center shadow-xl">
            <h1 className="text-xl font-bold text-rose-300">تعذر تحميل لوحة التحكم</h1>
            <p className="mt-3 text-sm text-slate-300">
              حدث خطأ في الواجهة. أعد تحميل الصفحة بعد التأكد من تشغيل Backend على المنفذ 8001.
            </p>
            <button
              type="button"
              onClick={() => window.location.reload()}
              className="mt-5 rounded-lg bg-blue-600 px-4 py-2 font-bold text-white hover:bg-blue-500"
            >
              إعادة تحميل الصفحة
            </button>
            <pre dir="ltr" className="mt-4 overflow-auto rounded-lg bg-slate-950 p-3 text-left text-xs text-rose-200">
              {this.state.error.message}
            </pre>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

export default function App() {
  const [unauthorized, setUnauthorized] = useState(false);

  useEffect(() => {
    const onUnauthorized = () => setUnauthorized(true);
    window.addEventListener('yv-api-unauthorized', onUnauthorized);
    return () => window.removeEventListener('yv-api-unauthorized', onUnauthorized);
  }, []);

  return (
    <DashboardErrorBoundary>
      <div dir="rtl" className="flex min-h-screen flex-col bg-slate-950 font-sans text-slate-100">
      <header className="sticky top-0 z-50 border-b border-slate-800 bg-slate-900/90 px-5 py-3 shadow-xl backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4">
          <NavLink to="/" className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-bl from-blue-600 to-indigo-600 shadow-lg shadow-blue-500/20">
              <svg className="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                />
              </svg>
            </span>
            <span>
              <span className="block text-base font-extrabold text-white">منظومة اليمن فيجن للذكاء المروري</span>
              <span className="block text-xs text-slate-400">YemenVision MTMC</span>
            </span>
          </NavLink>

          <nav aria-label="التنقل الرئيسي" className="flex flex-wrap items-center gap-1 text-sm">
            {navigation.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.path === '/'}
                className={({ isActive }) =>
                  `rounded-lg px-3 py-2 transition ${
                    isActive
                      ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30'
                      : 'text-slate-300 hover:bg-slate-800'
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>

      {unauthorized && (
        <div className="border-b border-amber-500/30 bg-amber-500/10 px-5 py-3 text-sm text-amber-200">
          <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3">
            <span>الخادم يتطلب مفتاح API صالحاً. اضبطه من صفحة الإعدادات ثم أعد المحاولة.</span>
            <div className="flex items-center gap-2">
              <Link to="/settings" className="rounded-lg bg-amber-500 px-3 py-1.5 font-bold text-slate-950">
                فتح الإعدادات
              </Link>
              <button
                type="button"
                onClick={() => setUnauthorized(false)}
                className="rounded-lg border border-amber-500/40 px-3 py-1.5"
              >
                إخفاء
              </button>
            </div>
          </div>
        </div>
      )}

      <main className="mx-auto w-full max-w-7xl flex-1 p-4 md:p-6">
        <Suspense
          fallback={
            <div className="flex min-h-64 items-center justify-center text-sm text-slate-400" role="status">
              جاري تحميل الصفحة…
            </div>
          }
        >
          <Routes>
            <Route path="/" element={<OverviewPage />} />
            <Route path="/live" element={<LivePage />} />
            <Route path="/cameras" element={<CamerasPage />} />
            <Route path="/videos" element={<VideosPage />} />
            <Route path="/plates" element={<PlatesPage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="/models" element={<ModelsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            {Object.entries(placeholderTitles).map(([path, title]) => (
              <Route key={path} path={`/${path}`} element={<PlaceholderPage title={title} />} />
            ))}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </main>

      <footer className="flex flex-wrap items-center justify-between gap-2 border-t border-slate-800 px-5 py-4 text-center text-xs text-slate-500">
        <span>جميع الحقوق محفوظة © 2026 - منظومة اليمن فيجن للرؤية الحاسوبية</span>
        <span className="font-mono text-blue-400">v3.0.0-React</span>
      </footer>
      </div>
    </DashboardErrorBoundary>
  );
}
