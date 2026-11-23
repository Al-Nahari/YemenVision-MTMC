import { useState, type FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { api, ApiError, type Camera } from '../api';
import { useDashboardData } from '../useDashboardData';
import { EmptyState, Panel, PageHeading } from '../components/ui';

const EMPTY_FORM = {
  id: '',
  zone: '',
  direction: 'ثنائي',
  active: true,
  stream_url: '',
};

export default function CamerasPage() {
  const { cameras, refresh } = useDashboardData();
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState('');
  const [authIssue, setAuthIssue] = useState(false);
  const [message, setMessage] = useState('');
  const [saving, setSaving] = useState(false);
  const [editing, setEditing] = useState<Camera | null>(null);
  const [editForm, setEditForm] = useState({ zone: '', direction: '', active: true, stream_url: '' });
  const [actionError, setActionError] = useState('');
  const [actionBusy, setActionBusy] = useState(false);

  const update = (key: keyof typeof EMPTY_FORM, value: string | boolean) => {
    setForm((current) => ({ ...current, [key]: value }));
  };

  const addCamera = async (event: FormEvent) => {
    event.preventDefault();
    setError('');
    setAuthIssue(false);
    setMessage('');
    setSaving(true);
    try {
      await api.createCamera({
        ...form,
        stream_url: form.stream_url || null,
      });
      setMessage('تم حفظ الكاميرا في الباكاند.');
      setForm(EMPTY_FORM);
      await refresh();
    } catch (err) {
      const status = err instanceof ApiError ? err.status : 0;
      setAuthIssue(status === 401);
      setError(
        status === 409
          ? 'معرّف الكاميرا موجود مسبقاً.'
          : status === 401
            ? 'مفتاح API مفقود أو غير صالح.'
            : `تعذّر حفظ الكاميرا (HTTP ${status || 'اتصال'}). تحقق من تشغيل الباكاند ومفتاح API.`,
      );
    } finally {
      setSaving(false);
    }
  };

  const openEditor = (camera: Camera) => {
    setActionError('');
    setEditing(camera);
    setEditForm({
      zone: camera.zone || '',
      direction: camera.direction || '',
      active: camera.active,
      stream_url: camera.stream_url || '',
    });
  };

  const saveEdit = async (event: FormEvent) => {
    event.preventDefault();
    if (!editing) return;
    setActionBusy(true);
    setActionError('');
    try {
      await api.updateCamera(editing.id, {
        zone: editForm.zone || null,
        direction: editForm.direction || null,
        active: editForm.active,
        stream_url: editForm.stream_url || null,
      });
      setMessage('تم تحديث بيانات الكاميرا.');
      setEditing(null);
      await refresh();
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : 'تعذّر تحديث الكاميرا.');
    } finally {
      setActionBusy(false);
    }
  };

  const removeCamera = async (camera: Camera) => {
    if (!window.confirm(`حذف الكاميرا "${camera.id}"؟ ستبقى السجلات التاريخية المرتبطة بها.`)) return;
    setActionBusy(true);
    setActionError('');
    try {
      const result = await api.deleteCamera(camera.id);
      setMessage(`تم حذف الكاميرا. السجلات التاريخية محفوظة: ${result.historical_rows_kept.events} حدث، ${result.historical_rows_kept.tracklets} تتبّع.`);
      setEditing(null);
      await refresh();
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : 'تعذّر حذف الكاميرا.');
    } finally {
      setActionBusy(false);
    }
  };

  return (
    <Panel>
      <PageHeading
        title="إدارة الكاميرات الحقيقية"
        subtitle="الكاميرات المسجلة والمفعّلة في قاعدة البيانات المركزية"
      />

      <form onSubmit={(event) => void addCamera(event)} className="mb-8 grid grid-cols-1 gap-4 rounded-2xl border border-slate-800 bg-slate-950 p-5 md:grid-cols-2">
        <label className="space-y-2 text-xs text-slate-300">
          معرّف الكاميرا
          <input
            name="cameraId"
            required
            pattern="[A-Za-z0-9_-]{1,64}"
            placeholder="cam_sana_01"
            className="field"
            value={form.id}
            onChange={(event) => update('id', event.target.value)}
          />
        </label>
        <label className="space-y-2 text-xs text-slate-300">
          المنطقة
          <input
            name="cameraZone"
            placeholder="شارع صنعاء"
            className="field"
            value={form.zone}
            onChange={(event) => update('zone', event.target.value)}
          />
        </label>
        <label className="space-y-2 text-xs text-slate-300">
          رابط البث RTSP/HTTP
          <input
            name="cameraStream"
            dir="ltr"
            placeholder="rtsp://user:password@host:554/stream"
            className="field"
            value={form.stream_url}
            onChange={(event) => update('stream_url', event.target.value)}
          />
        </label>
        <label className="space-y-2 text-xs text-slate-300">
          اتجاه الحركة
          <input
            name="cameraDirection"
            placeholder="ثنائي"
            className="field"
            value={form.direction}
            onChange={(event) => update('direction', event.target.value)}
          />
        </label>
        {error && (
          <div className="space-y-2 md:col-span-2">
            <p className="text-sm text-rose-400">{error}</p>
            {authIssue && (
              <Link to="/settings" className="inline-block rounded-lg bg-amber-500 px-3 py-1.5 text-sm font-bold text-slate-950">
                اضبط مفتاح API من الإعدادات
              </Link>
            )}
          </div>
        )}
        {message && <p className="text-sm text-emerald-400 md:col-span-2">{message}</p>}
        <button type="submit" disabled={saving} className="primary-btn md:col-span-2">
          {saving ? 'جارٍ الحفظ...' : 'إضافة الكاميرا'}
        </button>
      </form>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
        {cameras.map((camera) => (
          <div key={camera.id} className="space-y-4 rounded-2xl border border-slate-800 bg-slate-950/80 p-5 shadow-lg">
            <div className="flex items-center justify-between">
              <span className="font-mono text-sm font-bold text-white">{camera.id}</span>
              <span className="rounded-full border border-emerald-500/20 bg-emerald-500/10 px-2.5 py-1 text-xs font-semibold text-emerald-400">
                {camera.active ? 'مفعلة' : 'متوقفة'}
              </span>
            </div>
            <div className="space-y-1 text-xs text-slate-400">
              <p>المنطقة: <span className="text-slate-200">{camera.zone || 'غير محددة'}</span></p>
              <p>الاتجاه: <span className="text-slate-200">{camera.direction || 'ثنائي'}</span></p>
              <p>البث: <span className="text-slate-200">{camera.stream_url ? 'مُعرّف' : 'غير مُعرّف'}</span></p>
            </div>
            <div className="flex gap-2 border-t border-slate-800 pt-3">
              <button
                type="button"
                className="flex-1 rounded-lg bg-blue-600 px-3 py-2 text-xs font-bold text-white hover:bg-blue-500"
                onClick={() => openEditor(camera)}
              >
                تعديل
              </button>
              <button
                type="button"
                className="flex-1 rounded-lg bg-rose-600 px-3 py-2 text-xs font-bold text-white hover:bg-rose-500"
                onClick={() => void removeCamera(camera)}
              >
                حذف
              </button>
            </div>
          </div>
        ))}
        {cameras.length === 0 && (
          <div className="col-span-full">
            <EmptyState>لا توجد كاميرات مسجلة بعد. أضف كاميرا من النموذج أعلاه، أو قُم برفع فيديو وسيُنشأ معرّف تلقائي عند الرفع.</EmptyState>
          </div>
        )}
      </div>

      {editing && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/80 p-4" onClick={() => setEditing(null)}>
          <form
            className="w-full max-w-lg space-y-4 rounded-2xl border border-slate-700 bg-slate-900 p-6 shadow-2xl"
            onClick={(event) => event.stopPropagation()}
            onSubmit={(event) => void saveEdit(event)}
          >
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-white">تعديل الكاميرا</h3>
              <span className="font-mono text-xs text-blue-400" dir="ltr">{editing.id}</span>
            </div>
            <label className="block space-y-2 text-xs text-slate-300">
              المنطقة
              <input
                className="field"
                value={editForm.zone}
                onChange={(event) => setEditForm((current) => ({ ...current, zone: event.target.value }))}
              />
            </label>
            <label className="block space-y-2 text-xs text-slate-300">
              الاتجاه
              <input
                className="field"
                value={editForm.direction}
                onChange={(event) => setEditForm((current) => ({ ...current, direction: event.target.value }))}
              />
            </label>
            <label className="block space-y-2 text-xs text-slate-300">
              رابط البث RTSP/HTTP
              <input
                className="field"
                dir="ltr"
                value={editForm.stream_url}
                onChange={(event) => setEditForm((current) => ({ ...current, stream_url: event.target.value }))}
              />
            </label>
            <label className="flex items-center gap-2 text-sm text-slate-300">
              <input
                type="checkbox"
                checked={editForm.active}
                onChange={(event) => setEditForm((current) => ({ ...current, active: event.target.checked }))}
              />
              الكاميرا مفعّلة
            </label>
            {actionError && <p className="rounded-lg bg-rose-500/10 p-3 text-sm text-rose-300">{actionError}</p>}
            <div className="flex gap-2 pt-2">
              <button type="submit" disabled={actionBusy} className="primary-btn flex-1">
                {actionBusy ? 'جارٍ الحفظ...' : 'حفظ التعديلات'}
              </button>
              <button type="button" className="rounded-xl border border-slate-700 px-4 py-2 text-sm" onClick={() => setEditing(null)}>
                إلغاء
              </button>
            </div>
          </form>
        </div>
      )}
    </Panel>
  );
}
