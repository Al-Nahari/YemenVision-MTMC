import { useDashboardData } from '../useDashboardData';
import { EmptyState, formatDateTime, Panel, PageHeading } from '../components/ui';

export default function AnalyticsPage() {
  const { traffic, loading } = useDashboardData();

  return (
    <Panel>
      <PageHeading
        title="التحليلات والتجميعات المرورية"
        subtitle="البيانات الإحصائية الواردة من التجميعات الزمنية في قاعدة البيانات"
      />
      <div className="space-y-4">
        {traffic.map((aggregate) => (
          <div key={aggregate.id} className="rounded-2xl border border-slate-800 bg-slate-950 p-5">
            <div className="mb-2 flex items-center justify-between">
              <span className="font-mono text-xs font-bold text-blue-400">
                الكاميرا: {aggregate.camera_id}
              </span>
              <span className="text-xs text-slate-400">{formatDateTime(aggregate.bucket_start)}</span>
            </div>
            <p className="text-sm text-white">
              إجمالي المركبات في الفترة:{' '}
              <span className="font-bold text-emerald-400">{aggregate.payload?.total_vehicles || 0}</span>
            </p>
          </div>
        ))}
        {traffic.length === 0 && (
          <EmptyState>
            {loading ? 'جاري جلب التجميعات من الخادم...' : 'لا توجد تجميعات مرورية مسجلة بعد.'}
          </EmptyState>
        )}
      </div>
    </Panel>
  );
}
