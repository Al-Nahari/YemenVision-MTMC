import { Panel, PageHeading } from '../components/ui';

const models = [
  {
    name: 'YOLOv11m (الكشف والتتبع)',
    status: 'نشط (GPU/CPU)',
    description: 'نموذج الكشف عن المركبات واستخراج الإحداثيات والصناديق المحيطية.',
  },
  {
    name: 'OSNet ReID (إعادة التعرف)',
    status: 'نشط (512-dim)',
    description:
      'نموذج استخراج المتجهات البصرية لمطابقة المركبات عبر عدة كاميرات وتقاطع البيانات.',
  },
];

export default function ModelsPage() {
  return (
    <Panel>
      <PageHeading
        title="إدارة النماذج الذكية"
        subtitle="أوزان نماذج YOLOv11 و OSNet المفعّلة في النظام"
      />
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        {models.map((model) => (
          <div key={model.name} className="space-y-4 rounded-2xl border border-slate-800 bg-slate-950 p-6">
            <div className="flex items-center justify-between gap-4">
              <h3 className="text-lg font-bold text-white">{model.name}</h3>
              <span className="whitespace-nowrap rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs font-bold text-emerald-400">
                {model.status}
              </span>
            </div>
            <p className="text-xs leading-relaxed text-slate-400">{model.description}</p>
          </div>
        ))}
      </div>
    </Panel>
  );
}
