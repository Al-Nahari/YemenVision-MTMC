import { useCallback, useEffect, useState } from 'react';
import { api, ApiError, type Camera, type ProcessedVideo } from '../api';
import { EmptyState, PageHeading, Panel, formatDateTime } from '../components/ui';

const PAGE_SIZE = 24;

function formatSize(bytes: number): string {
  if (!bytes) return '—';
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function VideosPage() {
  const [videos, setVideos] = useState<ProcessedVideo[]>([]);
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [search, setSearch] = useState('');
  const [cameraId, setCameraId] = useState('');
  const [offset, setOffset] = useState(0);
  const [selected, setSelected] = useState<ProcessedVideo | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    const [videoRows, cameraRows] = await Promise.all([
      api.videos({ search, camera_id: cameraId, limit: PAGE_SIZE, offset }),
      api.cameras(),
    ]);
    setVideos(videoRows);
    setCameras(cameraRows);
    setLoading(false);
  }, [search, cameraId, offset]);

  useEffect(() => { void load(); }, [load]);

  const removeVideo = async (video: ProcessedVideo) => {
    if (!window.confirm(`حذف الفيديو "${video.original_name}" نهائياً من الأرشيف؟`)) return;
    setBusy(true);
    setError('');
    try {
      await api.deleteVideo(video.id);
      setSelected(null);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'تعذّر حذف الفيديو.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      <PageHeading
        title="أرشيف الفيديو المعالج"
        subtitle="تصفّح جميع الفيديوهات التي تم رفعها ومعالجتها، وافتحها أو نزّلها في أي وقت."
        badge={`${videos.length} في هذه الصفحة`}
      />

      <Panel>
        <form
          className="grid grid-cols-1 gap-3 md:grid-cols-[1fr_220px_auto]"
          onSubmit={(event) => {
            event.preventDefault();
            setOffset(0);
            setSearch(searchInput.trim());
          }}
        >
          <input
            className="field"
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
            placeholder="ابحث باسم الفيديو أو معرّفه"
            aria-label="بحث في الفيديوهات"
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
        {error && <p className="mt-3 rounded-lg bg-rose-500/10 p-3 text-sm text-rose-300">{error}</p>}
      </Panel>

      {!loading && videos.length === 0 ? (
        <Panel><EmptyState>لا توجد فيديوهات مطابقة. ارفع فيديو من صفحة المراقبة الحية أولاً.</EmptyState></Panel>
      ) : (
        <div className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-3">
          {videos.map((video) => (
            <Panel key={video.id} className="overflow-hidden p-0">
              <button
                type="button"
                onClick={() => setSelected(video)}
                className="group relative block h-44 w-full bg-gradient-to-br from-slate-800 to-slate-950"
                aria-label={`فتح ${video.original_name}`}
              >
                <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 text-slate-400 transition group-hover:text-blue-300">
                  <span className="flex h-14 w-14 items-center justify-center rounded-full border border-slate-600 bg-slate-900/80 text-2xl">▶</span>
                  <span className="text-xs">{video.source === 'legacy' ? 'أرشيف قديم' : 'فيديو معالج'}</span>
                </div>
                <span className="absolute bottom-2 left-2 rounded-lg bg-slate-950/80 px-2 py-1 text-xs text-slate-300">
                  {video.frames_processed ? `${video.frames_processed} إطار` : '—'}
                </span>
              </button>
              <div className="space-y-3 p-4">
                <div className="truncate text-sm font-semibold text-white" title={video.original_name}>{video.original_name}</div>
                <div className="flex flex-wrap gap-2 text-xs text-slate-400">
                  <span className="rounded-lg bg-blue-500/10 px-2 py-1 text-blue-300">{video.camera_id || 'بدون كاميرا'}</span>
                  <span className="rounded-lg bg-emerald-500/10 px-2 py-1 text-emerald-300">{video.plate_count} لوحة</span>
                  <span className="rounded-lg bg-slate-800 px-2 py-1">{formatSize(video.file_size)}</span>
                </div>
                <div className="text-xs text-slate-500">{formatDateTime(video.created_at)}</div>
                <div className="flex gap-2">
                  <button type="button" className="primary-btn flex-1 py-2" onClick={() => setSelected(video)}>فتح الفيديو</button>
                  <a
                    className="rounded-xl border border-slate-700 px-4 py-2 text-sm text-slate-200 hover:bg-slate-800"
                    href={api.mediaUrl(video.video_url)}
                    download={video.original_name}
                    target="_blank"
                    rel="noreferrer"
                  >
                    تنزيل
                  </a>
                </div>
              </div>
            </Panel>
          ))}
        </div>
      )}

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
          disabled={videos.length < PAGE_SIZE}
          onClick={() => setOffset(offset + PAGE_SIZE)}
        >
          التالي
        </button>
      </div>

      {selected && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/80 p-4" onClick={() => setSelected(null)}>
          <div className="w-full max-w-4xl rounded-2xl border border-slate-700 bg-slate-900 p-4 shadow-2xl" onClick={(event) => event.stopPropagation()}>
            <div className="mb-3 flex items-center justify-between gap-3">
              <div className="min-w-0">
                <h3 className="truncate text-lg font-bold text-white">{selected.original_name}</h3>
                <p className="text-xs text-slate-400" dir="ltr">{selected.camera_id} · {selected.video_id}</p>
              </div>
              <button className="rounded-lg bg-slate-800 px-3 py-2 text-sm hover:bg-slate-700" onClick={() => setSelected(null)}>إغلاق</button>
            </div>
            <video
              key={selected.id}
              className="max-h-[65vh] w-full rounded-xl bg-black"
              src={api.mediaUrl(selected.video_url)}
              controls
              autoPlay
              playsInline
            >
              متصفحك لا يدعم تشغيل الفيديو.
            </video>
            <div className="mt-3 flex flex-wrap items-center justify-between gap-3 text-xs text-slate-400">
              <span>{formatDateTime(selected.created_at)} · {formatSize(selected.file_size)}</span>
              <div className="flex gap-2">
                <a className="rounded-lg bg-blue-600 px-3 py-2 text-white hover:bg-blue-500" href={api.mediaUrl(selected.video_url)} download target="_blank" rel="noreferrer">تنزيل</a>
                <button
                  className="rounded-lg bg-rose-600 px-3 py-2 text-white hover:bg-rose-500 disabled:opacity-50"
                  disabled={busy}
                  onClick={() => void removeVideo(selected)}
                >
                  {busy ? 'جارٍ الحذف...' : 'حذف الفيديو'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
