import { Link } from 'react-router-dom';
import { useDashboardData } from '../useDashboardData';
import { EmptyState, formatTime, Panel, StatCard } from '../components/ui';

export default function OverviewPage() {
  const { cameras, tracklets, events, loading } = useDashboardData();

  return (
    <div className="animate-fadeIn space-y-6">
      <div className="relative overflow-hidden rounded-2xl border border-blue-800/40 bg-gradient-to-l from-blue-900/50 via-indigo-950/50 to-slate-900/80 p-8 shadow-2xl">
        <div className="pointer-events-none absolute -bottom-10 -left-10 h-64 w-64 rounded-full bg-blue-600/10 blur-3xl" />
        <div className="relative z-10 flex flex-col items-start justify-between gap-4 md:flex-row md:items-center">
          <div>
            <span className="mb-3 inline-block rounded-full border border-blue-500/30 bg-blue-500/10 px-3 py-1 text-xs font-bold tracking-wider text-blue-400">
              غرفة العمليات المركزية
            </span>
            <h2 className="mb-2 text-3xl font-extrabold text-white">
              لوحة التحكم في الذكاء المروري (MTMC)
            </h2>
            <p className="max-w-2xl text-sm leading-relaxed text-slate-300">
              متابعة حية من قاعدة البيانات، رصد المخالفات، وتقاطع البيانات الصادرة من نماذج YOLOv11
              و OSNet ReID عبر الخادم الحقيقي.
            </p>
          </div>
          <Link to="/live" className="primary-btn flex items-center gap-2">
            فتح المراقبة الحية والرفع
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-4">
        <StatCard label="الكاميرات المتصلة" value={cameras.length} hint="نشطة" accent="emerald" />
        <StatCard label="أحداث الكشف المرصودة" value={events.length} hint="سجل حقيقي" />
        <StatCard label="المسارات النشطة (Tracklets)" value={tracklets.length} hint="مع ReID" accent="cyan" />
        <StatCard label="حالة الخادم والنماذج" value="متصل" hint="YOLOv11m" accent="emerald" />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Panel>
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-lg font-bold text-white">أحدث مسارات المركبات</h3>
            <span className="rounded-lg bg-blue-500/10 px-2.5 py-1 text-xs text-blue-400">
              من السيرفر مباشرة
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-right text-sm">
              <thead className="bg-slate-800/50 text-xs uppercase text-slate-400">
                <tr>
                  <th className="rounded-r-lg p-3">معرف المسار</th>
                  <th className="p-3">الكاميرا</th>
                  <th className="p-3">نوع المركبة</th>
                  <th className="rounded-l-lg p-3">الوقت</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {tracklets.map((track) => (
                  <tr key={track.id} className="transition hover:bg-slate-800/30">
                    <td className="p-3 font-mono font-medium text-white">{track.id}</td>
                    <td className="p-3 font-mono text-xs">{track.camera_id}</td>
                    <td className="p-3">
                      <span className="rounded-lg border border-blue-500/20 bg-blue-500/10 px-2.5 py-1 text-xs font-semibold text-blue-400">
                        {track.payload?.vehicle_type || 'مركبة'}
                      </span>
                    </td>
                    <td className="p-3 text-xs text-slate-400">{formatTime(track.start_time)}</td>
                  </tr>
                ))}
                {tracklets.length === 0 && (
                  <tr>
                    <td colSpan={4}>
                      <EmptyState>
                        {loading
                          ? 'جاري جلب المسارات من الخادم...'
                          : 'لا توجد مسارات مسجلة بعد. قم بتشغيل فحص فيديو لتحليل البيانات.'}
                      </EmptyState>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </Panel>

        <Panel>
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-lg font-bold text-white">سجل أحداث الكشف</h3>
            <span className="rounded bg-emerald-500/10 px-2 py-0.5 text-xs text-emerald-400">
              مباشر من DB
            </span>
          </div>
          <div className="max-h-72 space-y-3 overflow-y-auto">
            {events.map((event) => (
              <div
                key={event.id}
                className="flex items-center justify-between rounded-xl border border-slate-800/80 bg-slate-950/70 p-3.5 transition hover:border-slate-700"
              >
                <div className="flex items-center gap-3">
                  <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" />
                  <div>
                    <p className="text-sm font-semibold text-white">
                      رصد: {event.payload?.class_name || 'مركبة'} (ثقة:{' '}
                      {event.payload?.confidence ?? 0.9})
                    </p>
                    <p className="text-xs text-slate-400">
                      الكاميرا: {event.camera_id} | المعرف: {event.id}
                    </p>
                    {(event.plate_text || event.payload?.plate_text) && (
                      <p className="mt-1 text-xs" dir="ltr">
                        <span className="rounded-lg bg-emerald-500/10 px-2 py-1 font-mono font-bold text-emerald-300">
                          {event.plate_text || String(event.payload?.plate_text)}
                        </span>
                      </p>
                    )}
                  </div>
                </div>
                <span className="font-mono text-xs text-slate-400">{formatTime(event.occurred_at)}</span>
              </div>
            ))}
            {events.length === 0 && (
              <EmptyState>
                {loading ? 'جاري جلب الأحداث من الخادم...' : 'لا توجد أحداث كشف مسجلة حالياً.'}
              </EmptyState>
            )}
          </div>
        </Panel>
      </div>
    </div>
  );
}
