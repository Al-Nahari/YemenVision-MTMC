import { useCallback, useEffect, useState } from 'react';
import { api, type Camera, type PlateReading } from '../api';
import { EmptyState, PageHeading, Panel, formatDateTime } from '../components/ui';

const PAGE_SIZE = 100;

export default function PlatesPage() {
  const [plates, setPlates] = useState<PlateReading[]>([]);
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [loading, setLoading] = useState(true);
  const [plateInput, setPlateInput] = useState('');
  const [plate, setPlate] = useState('');
  const [cameraId, setCameraId] = useState('');
  const [offset, setOffset] = useState(0);

  const load = useCallback(async () => {
    setLoading(true);
    const [rows, cameraRows] = await Promise.all([
      api.plates({ plate, camera_id: cameraId, limit: PAGE_SIZE, offset }),
      api.cameras(),
    ]);
    setPlates(rows);
    setCameras(cameraRows);
    setLoading(false);
  }, [plate, cameraId, offset]);

  useEffect(() => { void load(); }, [load]);

  return (
    <div className="space-y-6 animate-fadeIn">
      <PageHeading
        title="سجل لوحات المركبات"
        subtitle="أرقام اللوحات المستخرجة من الفيديوهات المعالجة، مرتبطة بالكاميرا ورقم الإطار والمركبة."
        badge={`${plates.length} قراءة`}
      />

      <Panel>
        <form
          className="grid grid-cols-1 gap-3 md:grid-cols-[1fr_220px_auto]"
          onSubmit={(event) => {
            event.preventDefault();
            setOffset(0);
            setPlate(plateInput.trim());
          }}
        >
          <input
            className="field"
            value={plateInput}
            onChange={(event) => setPlateInput(event.target.value)}
            placeholder="ابحث برقم اللوحة"
            aria-label="بحث برقم اللوحة"
          />
          <select
            className="field"
            value={cameraId}
            onChange={(event) => { setCameraId(event.target.value); setOffset(0); }}
            aria-label="تصفية حسب الكاميرا"
          >
            <option value="">كل الكاميرات</option>
            {cameras.map((camera) => (
              <option key={camera.id} value={camera.id}>{camera.zone || camera.id}</option>
            ))}
          </select>
          <button className="primary-btn" type="submit">بحث</button>
        </form>
      </Panel>

      <Panel className="overflow-x-auto p-0">
        <table className="w-full text-right text-sm">
          <thead className="bg-slate-950/60 text-xs text-slate-400">
            <tr>
              <th className="px-4 py-3 font-medium">اللوحة</th>
              <th className="px-4 py-3 font-medium">الكاميرا</th>
              <th className="px-4 py-3 font-medium">الوقت</th>
              <th className="px-4 py-3 font-medium">الفيديو / الإطار</th>
              <th className="px-4 py-3 font-medium">الثقة</th>
              <th className="px-4 py-3 font-medium">الحالة</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {!loading && plates.length === 0 ? (
              <tr><td colSpan={6}><EmptyState>لا توجد قراءات لوحات بعد. سيظهر الرقم هنا بعد معالجة فيديو يحتوي على لوحات واضحة.</EmptyState></td></tr>
            ) : plates.map((item) => (
              <tr key={item.id} className="hover:bg-slate-800/40">
                <td className="px-4 py-3" dir="ltr"><span className="rounded-lg bg-emerald-500/10 px-2 py-1 font-mono font-bold text-emerald-300">{item.plate_text}</span></td>
                <td className="px-4 py-3 text-slate-300">{item.camera_id}</td>
                <td className="px-4 py-3 text-slate-400">{formatDateTime(item.occurred_at)}</td>
                <td className="px-4 py-3 text-xs text-slate-400" dir="ltr">
                  {item.video_id || '—'} {item.frame_index !== null && item.frame_index !== undefined ? `#${item.frame_index}` : ''}
                </td>
                <td className="px-4 py-3 text-slate-300">{item.confidence ? `${Math.round(item.confidence * 100)}%` : '—'}</td>
                <td className="px-4 py-3 text-xs text-slate-500">{item.status || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>

      <div className="flex items-center justify-between gap-3">
        <button
          className="rounded-xl border border-slate-700 px-4 py-2 text-sm disabled:opacity-40"
          disabled={offset === 0}
          onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
        >
          السابق
        </button>
        <span className="text-xs text-slate-500">الصفحة {Math.floor(offset / PAGE_SIZE) + 1}</span>
        <button
          className="rounded-xl border border-slate-700 px-4 py-2 text-sm disabled:opacity-40"
          disabled={plates.length < PAGE_SIZE}
          onClick={() => setOffset(offset + PAGE_SIZE)}
        >
          التالي
        </button>
      </div>
    </div>
  );
}
