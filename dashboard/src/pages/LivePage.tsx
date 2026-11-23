import { useEffect, useState, type ChangeEvent } from 'react';
import { api, ApiError, type InferenceResult } from '../api';
import { useDashboardData } from '../useDashboardData';
import { EmptyState, Panel } from '../components/ui';

const MAX_VIDEO_BYTES = 500 * 1024 * 1024;
const DEFAULT_MAX_FRAMES = 300;
const MAX_FRAMES_LIMIT = 3600;

/** The backend creates a camera row on demand; derive a safe ID from the file. */
function cameraIdForVideo(file: File): string {
  const stem = file.name.replace(/\.[^.]+$/, '');
  const safe = stem
    .replace(/[^A-Za-z0-9_]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .slice(0, 48);
  return `video_${safe || 'upload'}`;
}

export default function LivePage() {
  const { cameras, loading, refresh } = useDashboardData();
  const [selectedCamera, setSelectedCamera] = useState('');
  const [selectedVideo, setSelectedVideo] = useState<File | null>(null);
  const [maxFrames, setMaxFrames] = useState(DEFAULT_MAX_FRAMES);
  const [isInferencing, setIsInferencing] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [result, setResult] = useState<InferenceResult | null>(null);
  const [processedVideoUrl, setProcessedVideoUrl] = useState('');
  const [videoError, setVideoError] = useState(false);
  const [error, setError] = useState('');

  // البث الحي يعتمد حصراً على روابط الكاميرات المحفوظة في قاعدة البيانات.
  const [streamError, setStreamError] = useState('');
  const [streamBusy, setStreamBusy] = useState<string | null>(null);
  type LiveStream = { id: string; cameraId: string; url: string };
  const [liveStreams, setLiveStreams] = useState<LiveStream[]>([]);

  useEffect(() => {
    if (selectedCamera && cameras.length > 0 && !cameras.some((camera) => camera.id === selectedCamera)) {
      setSelectedCamera('');
    }
  }, [cameras, selectedCamera]);

  const onVideoSelected = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] ?? null;
    setError('');
    if (file && file.size > MAX_VIDEO_BYTES) {
      setError('حجم الفيديو أكبر من الحد المسموح (500MB).');
      event.target.value = '';
      setSelectedVideo(null);
      return;
    }
    setSelectedVideo(file);
  };

  const updateMaxFrames = (value: number) => {
    if (Number.isNaN(value)) return;
    setMaxFrames(Math.min(MAX_FRAMES_LIMIT, Math.max(1, Math.round(value))));
  };

  const runInference = async () => {
    if (!selectedVideo) return;
    const cameraId = selectedCamera || cameraIdForVideo(selectedVideo);
    setIsInferencing(true);
    setError('');
    setResult(null);
    setProcessedVideoUrl('');
    setVideoError(false);
    setUploadProgress(0);

    try {
      const response = await api.uploadVideo(selectedVideo, cameraId, setUploadProgress, maxFrames);
      setResult(response);
      setProcessedVideoUrl(response.video_url ? api.mediaUrl(response.video_url) : '');
      await refresh();
    } catch (err) {
      const message = err instanceof ApiError ? err.message : '';
      setError(message || 'فشل رفع/معالجة الفيديو. تحقق من تشغيل الخادم ومفتاح API.');
    } finally {
      setIsInferencing(false);
    }
  };

  const startStream = async (cameraId: string) => {
    setError('');
    setStreamError('');
    const camera = cameras.find((item) => item.id === cameraId);
    if (!camera?.stream_url) {
      setStreamError('لا يوجد رابط بث محفوظ لهذه الكاميرا. أضف الرابط من إدارة الكاميرات أولاً.');
      return;
    }
    if (liveStreams.some((stream) => stream.cameraId === cameraId)) return;
    setStreamBusy(cameraId);
    try {
      const url = api.liveStreamUrl(camera.stream_url, camera.id, 5, 640, true);
      setLiveStreams((current) => [...current, { id: `${camera.id}-${Date.now()}`, cameraId: camera.id, url }]);
    } catch (err) {
      setStreamError(err instanceof ApiError ? err.message : 'تعذّر إنشاء رابط البث. تحقق من تشغيل الخادم.');
    } finally {
      setStreamBusy(null);
    }
  };

  const stopStream = () => {
    setLiveStreams([]);
    setStreamError('');
  };

  const removeStream = (cameraId: string) => {
    setLiveStreams((current) => current.filter((stream) => stream.cameraId !== cameraId));
  };

  const streaming = liveStreams.length > 0;

  const effectiveCameraId = selectedCamera || (selectedVideo ? cameraIdForVideo(selectedVideo) : '');

  return (
    <div className="animate-fadeIn space-y-6">
      <Panel className="space-y-6">
        <div className="flex flex-col justify-between gap-4 border-b border-slate-800 pb-4 md:flex-row md:items-center">
          <div>
            <h2 className="text-2xl font-bold text-white">
              المراقبة الحية وفحص الفيديوهات بنماذج الذكاء الاصطناعي
            </h2>
            <p className="mt-1 text-sm text-slate-400">
              ارفع ملف فيديو MP4 وشغّل استدلال YOLOv11m + OSNet ReID على الخادم الحقيقي — لا تحتاج إلى كاميرا مسجلة مسبقاً.
            </p>
          </div>
          <div className="space-y-1">
            <label htmlFor="linked-camera" className="block text-xs text-slate-400">
              كاميرا مرتبطة بالفيديو (اختياري)
            </label>
            <select
              id="linked-camera"
              aria-label="اختر كاميرا"
              className="field w-auto min-w-56"
              value={selectedCamera}
              onChange={(event) => setSelectedCamera(event.target.value)}
            >
              <option value="">إنشاء معرّف تلقائي من اسم الفيديو</option>
              {cameras.map((camera) => (
                <option key={camera.id} value={camera.id}>
                  {camera.zone || camera.id} ({camera.id})
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="space-y-6 rounded-2xl border border-slate-800 bg-slate-950 p-6 shadow-xl">
          <h3 className="text-lg font-bold text-white">
            رفع فيديو وفحصه عبر نماذج YOLOv11 و ReID في الباكاند
          </h3>

          <div className="grid grid-cols-1 items-center gap-4 md:grid-cols-3">
            <div className="space-y-2 md:col-span-2">
              <label htmlFor="video-file" className="text-xs font-semibold text-slate-400">
                اختر ملف فيديو من جهازك (MP4, AVI, MOV, MKV — حتى 500MB):
              </label>
              <input
                id="video-file"
                type="file"
                accept="video/*,.avi,.mkv"
                onChange={onVideoSelected}
                className="block w-full text-sm text-slate-300 file:ml-4 file:rounded-lg file:border-0 file:bg-blue-600 file:px-4 file:py-2.5 file:font-bold file:text-white hover:file:bg-blue-500"
              />
              {selectedVideo && (
                <p className="text-xs text-slate-400">
                  الملف المختار: {selectedVideo.name} (
                  {(selectedVideo.size / 1048576).toFixed(1)} MB)
                </p>
              )}
              {error && <p className="text-xs text-rose-400">{error}</p>}
            </div>
            <div className="pt-5">
              <button
                type="button"
                onClick={() => void runInference()}
                disabled={isInferencing || !selectedVideo}
                title={!selectedVideo ? 'اختر ملف فيديو MP4 أولاً' : ''}
                className="w-full rounded-xl bg-emerald-600 px-6 py-3 text-sm font-bold text-white shadow-lg shadow-emerald-600/30 transition hover:bg-emerald-500 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isInferencing ? 'جاري المعالجة عبر النماذج...' : 'بدء الفحص والاستدلال الحقيقي'}
              </button>
              {!selectedVideo && (
                <p className="mt-2 text-center text-xs text-slate-500">اختر ملف فيديو MP4 لتفعيل زر المعالجة.</p>
              )}
              {selectedVideo && !selectedCamera && (
                <p className="mt-2 text-center text-xs text-slate-500">
                  سيُنشأ معرّف كاميرا تلقائياً من اسم الملف: <span dir="ltr" className="font-mono text-blue-400">{effectiveCameraId}</span>
                </p>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 items-center gap-4 rounded-xl border border-slate-800 bg-slate-900/60 p-4 md:grid-cols-[1fr_8rem]">
            <div>
              <div className="flex items-center justify-between gap-4">
                <label htmlFor="max-frames" className="text-xs font-semibold text-slate-300">
                  عدد الإطارات المراد معالجتها
                </label>
                <span className="font-mono text-sm font-bold text-blue-400">{maxFrames}</span>
              </div>
              <input
                id="max-frames"
                type="range"
                min={1}
                max={MAX_FRAMES_LIMIT}
                step={1}
                value={maxFrames}
                onChange={(event) => updateMaxFrames(Number(event.target.value))}
                className="mt-3 w-full accent-blue-500"
              />
              <p className="mt-1 text-xs text-slate-500">
                تُعالج أول {maxFrames} إطار من الفيديو. الافتراضي {DEFAULT_MAX_FRAMES}، الأقصى{' '}
                {MAX_FRAMES_LIMIT}.
              </p>
            </div>
            <input
              type="number"
              aria-label="ضبط عدد الإطارات"
              dir="ltr"
              min={1}
              max={MAX_FRAMES_LIMIT}
              step={1}
              value={maxFrames}
              onChange={(event) => updateMaxFrames(Number(event.target.value))}
              className="field w-full text-center md:w-32"
            />
          </div>

          {isInferencing && (
            <div role="status" aria-live="polite" className="space-y-3 rounded-xl border border-blue-500/40 bg-blue-950/70 p-5">
              <div className="flex items-center gap-3">
                <span className="h-5 w-5 animate-spin rounded-full border-2 border-blue-300 border-t-transparent" />
                <span className="font-bold text-blue-200">
                  {uploadProgress < 100 ? 'جاري رفع الفيديو...' : 'اكتمل الرفع، جاري تحليل الإطارات...'}{' '}
                  {uploadProgress}%
                </span>
              </div>
              <div className="h-2 overflow-hidden rounded bg-slate-800">
                <div className="h-full bg-blue-400 transition-all" style={{ width: `${uploadProgress}%` }} />
              </div>
            </div>
          )}

          {result && (
            <div className="animate-fadeIn space-y-3 rounded-xl border border-emerald-500/40 bg-slate-900 p-5">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="text-sm font-bold text-emerald-400">
                  تم اكتمال الفحص بنجاح بواسطة النموذج: {result.model_version}
                </span>
                <span className="font-mono text-xs text-slate-400">
                  المدة: {result.duration_seconds} ثانية
                </span>
              </div>
              {processedVideoUrl && (
                <p className="text-xs text-emerald-300">
                  الفيديو المعالج جاهز للمشاهدة في المشغّل أدناه مباشرة.
                </p>
              )}
              <div className="grid grid-cols-2 gap-4 font-mono text-xs md:grid-cols-4">
                <div className="rounded-lg border border-slate-800 bg-slate-950 p-3">
                  <p className="text-slate-400">الإطارات المعالجة</p>
                  <p className="text-lg font-bold text-white">{result.frames_processed}</p>
                </div>
                <div className="rounded-lg border border-slate-800 bg-slate-950 p-3">
                  <p className="text-slate-400">المسارات المتولدة</p>
                  <p className="text-lg font-bold text-blue-400">{result.tracklets_count}</p>
                </div>
                <div className="rounded-lg border border-slate-800 bg-slate-950 p-3">
                  <p className="text-slate-400">أحداث الكشف</p>
                  <p className="text-lg font-bold text-emerald-400">{result.events_count}</p>
                </div>
                <div className="rounded-lg border border-slate-800 bg-slate-950 p-3">
                  <p className="text-slate-400">معرف الفيديو</p>
                  <p className="truncate font-bold text-cyan-400">{result.video_id}</p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* البث الحي من الكاميرات المسجلة */}
        <div className="space-y-6 rounded-3xl border border-cyan-400/10 bg-slate-950/70 p-5 shadow-xl md:p-6">
          <div className="flex flex-col justify-between gap-4 border-b border-slate-800 pb-4 md:flex-row md:items-center">
            <div>
              <h3 className="text-lg font-bold text-white">المراقبة الحية</h3>
              <p className="mt-1 text-sm text-slate-400">
                اختر الكاميرا واضغط بث. كل كاميرا جديدة تظهر بجانب البث الحالي، وتُحفظ نتائج الكشف فقط.
              </p>
            </div>
            {streaming && (
              <button type="button" onClick={stopStream} className="rounded-xl border border-rose-400/30 bg-rose-500/10 px-4 py-2 text-sm font-bold text-rose-300 transition hover:bg-rose-500/20">
                إيقاف جميع البثوث ({liveStreams.length})
              </button>
            )}
          </div>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {cameras.map((camera) => {
              const active = liveStreams.some((stream) => stream.cameraId === camera.id);
              return (
                <div key={camera.id} className={`flex items-center justify-between gap-3 rounded-2xl border p-4 transition ${active ? 'border-emerald-400/30 bg-emerald-400/[.06]' : 'border-white/[.08] bg-slate-900/70 hover:border-cyan-400/30'}`}>
                  <div className="min-w-0">
                    <p className="truncate font-bold text-white">{camera.zone || camera.id}</p>
                    <p dir="ltr" className="mt-1 truncate font-mono text-[11px] text-slate-500">{camera.id}</p>
                    <p className={`mt-2 text-[11px] ${camera.stream_url ? 'text-emerald-300' : 'text-amber-300'}`}>
                      {camera.stream_url ? (active ? 'البث يعمل' : 'جاهزة للبث') : 'لا يوجد رابط بث'}
                    </p>
                  </div>
                  <button type="button" disabled={!camera.stream_url || active || streamBusy === camera.id} onClick={() => void startStream(camera.id)} className="shrink-0 rounded-xl bg-gradient-to-l from-blue-600 to-cyan-600 px-4 py-2 text-xs font-bold text-white shadow-lg shadow-blue-900/30 transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-35">
                    {streamBusy === camera.id ? 'جاري...' : active ? 'يعمل' : 'بث'}
                  </button>
                </div>
              );
            })}
          </div>
          {streamError && <p className="text-xs text-rose-400">{streamError}</p>}

           {streaming ? (
             <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
               {liveStreams.map((stream) => (
                 <div key={stream.id} className="relative h-[300px] overflow-hidden rounded-2xl border border-slate-800 bg-black shadow-xl">
                   <div className="absolute inset-x-3 top-3 z-20 flex items-center justify-between rounded-lg border border-emerald-500/40 bg-emerald-900/80 px-3 py-1 text-xs font-bold text-white backdrop-blur-md">
                     <span><span className="mr-2 inline-block h-2 w-2 animate-pulse rounded-full bg-emerald-400" />{stream.cameraId}</span>
                     <button type="button" onClick={() => removeStream(stream.cameraId)} className="text-rose-200 hover:text-white">إيقاف</button>
                   </div>
                   <img src={stream.url} alt={`البث ${stream.cameraId}`} className="h-full w-full object-contain" onError={() => setStreamError(`تعذّر عرض بث الكاميرا ${stream.cameraId}.`)} />
                 </div>
               ))}
               {streamError && <p className="text-xs text-rose-400 md:col-span-2">{streamError}</p>}
             </div>
          ) : (
            <div className="flex h-[360px] items-center justify-center bg-gradient-to-bl from-slate-900 via-slate-950 to-blue-950 rounded-2xl border border-slate-800">
              <p className="text-xs font-mono text-slate-400 text-center p-6">
                لا يوجد بث مباشر فعّال — أدخل رابط RTSP واضغط "تشغيل البث المباشر".
              </p>
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          <div className="relative overflow-hidden rounded-2xl border border-slate-800 bg-slate-950 shadow-2xl">
            <div className="absolute right-3 top-3 z-20 flex items-center gap-2 rounded-lg border border-slate-700/50 bg-slate-900/80 px-3 py-1 backdrop-blur-md">
              <span className={`h-2 w-2 rounded-full ${processedVideoUrl ? 'bg-emerald-400' : 'bg-amber-400'}`} />
              <span className="text-xs font-bold text-white">
                {processedVideoUrl ? 'الفيديو المعالج' : `${effectiveCameraId || '—'} [معرّف الربط]`}
              </span>
            </div>
            {processedVideoUrl ? (
              <div className="bg-black">
                <video
                  key={processedVideoUrl}
                  controls
                  playsInline
                  preload="metadata"
                  src={processedVideoUrl}
                  onLoadedData={() => setVideoError(false)}
                  onError={() => setVideoError(true)}
                  className="max-h-[520px] min-h-[280px] w-full"
                >
                  متصفحك لا يدعم تشغيل الفيديو.
                </video>
                {videoError && (
                  <p className="border-t border-rose-500/30 bg-rose-500/10 p-3 text-xs text-rose-300">
                    تعذّر تحميل الفيديو المعالج. قد تكون انتهت صلاحية الرابط؛ أعد تشغيل الفحص للحصول على رابط جديد.
                  </p>
                )}
                <div className="flex items-center justify-between gap-3 border-t border-slate-800 bg-slate-900/90 p-3">
                  <span className="text-xs text-slate-400">الفيديو الناتج بعد إضافة مربعات الكشف</span>
                  <a
                    href={processedVideoUrl}
                    download
                    target="_blank"
                    rel="noreferrer"
                    className="rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-bold text-white hover:bg-blue-500"
                  >
                    تنزيل الفيديو
                  </a>
                </div>
              </div>
            ) : (
              <div className="flex h-72 items-center justify-center bg-gradient-to-bl from-slate-900 via-slate-950 to-blue-950">
                <div className="space-y-2 p-6 text-center">
                  <p className="text-xs font-mono text-slate-400">
                    لا يوجد بث مباشر حالياً — ارفع فيديو وسيعرض الفيديو المعالج هنا في نفس الصفحة.
                  </p>
                </div>
              </div>
            )}
            <div className="flex items-center justify-between border-t border-slate-800 bg-slate-900/90 p-4 text-xs text-slate-300">
              <span>النموذج النشط: YOLOv11m + OSNet ReID</span>
              <span className={`font-bold ${processedVideoUrl ? 'text-emerald-400' : 'text-amber-400'}`}>
                {processedVideoUrl ? 'تم عرض الفيديو المعالج' : 'البث المباشر غير متاح بعد'}
              </span>
            </div>
          </div>

          <div className="flex flex-col justify-between rounded-2xl border border-slate-800 bg-slate-950 p-6 shadow-2xl">
            <div>
              <h3 className="mb-2 text-lg font-bold text-white">سجل الكشف الفوري وإحصاءات النماذج</h3>
              <p className="mb-4 text-xs leading-relaxed text-slate-400">
                عند تشغيل فحص الفيديو، يقوم النظام بتحليل المتجهات البصرية (Embeddings) عبر 512 بعد
                وتخزينها في قاعدة البيانات لاستخراج التقارير والمسارات المرورية.
              </p>
            </div>
            <div className="space-y-3 font-mono text-xs">
              <div className="flex justify-between rounded-xl border border-slate-800 bg-slate-900 p-3">
                <span className="text-slate-400">حالة الخادم:</span>
                <span className="font-bold text-slate-300">تُحدّث عبر طلبات API</span>
              </div>
              <div className="flex justify-between rounded-xl border border-slate-800 bg-slate-900 p-3">
                <span className="text-slate-400">إجمالي الكاميرات:</span>
                <span className="font-bold text-blue-400">{cameras.length}</span>
              </div>
            </div>
          </div>
        </div>
      </Panel>
      {cameras.length === 0 && (
        <EmptyState>
          {loading
            ? 'جاري جلب الكاميرات من الخادم...'
            : 'لا توجد كاميرات مسجلة بعد — يمكنك رفع فيديو وسيُنشأ معرّف كاميرا تلقائياً.'}
        </EmptyState>
      )}
    </div>
  );
}
