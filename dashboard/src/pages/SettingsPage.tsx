import { useState } from 'react';
import { apiBase } from '../api';
import { Panel, PageHeading } from '../components/ui';

export default function SettingsPage() {
  const [apiUrl, setApiUrl] = useState(apiBase());
  const [apiKey, setApiKey] = useState(localStorage.getItem('yv_api_key') || '');

  const save = () => {
    localStorage.setItem('yv_api_key', apiKey.trim());
    localStorage.setItem('yv_api_url', apiUrl.trim().replace(/\/$/, ''));
    window.location.reload();
  };

  return (
    <Panel className="mx-auto max-w-2xl">
      <PageHeading title="إعدادات الاتصال بالخادم" />
      <div className="space-y-5 text-sm">
        <p className="text-slate-400">
          أدخل عنوان API ومفتاحاً صالحاً من إعدادات الخادم. المفتاح يُحفظ في هذا المتصفح فقط.
        </p>
        {import.meta.env.DEV && (
          <p className="rounded-lg border border-blue-500/20 bg-blue-500/10 p-3 text-xs text-blue-300">
            في وضع التطوير يضيف Vite مفتاح الخادم المحلي تلقائياً، لذا يمكن ترك حقل المفتاح فارغاً.
          </p>
        )}
        <label className="block text-slate-300">
          عنوان API
          <input
            dir="ltr"
            className="field mt-2"
            placeholder="http://127.0.0.1:8000/api/v1"
            value={apiUrl}
            onChange={(event) => setApiUrl(event.target.value)}
          />
        </label>
        <label className="block text-slate-300">
          مفتاح API
          <input
            dir="ltr"
            type="password"
            autoComplete="new-password"
            className="field mt-2"
            placeholder="أدخل المفتاح الذي ضبطته في API_KEYS_JSON"
            value={apiKey}
            onChange={(event) => setApiKey(event.target.value)}
          />
        </label>
        <button type="button" onClick={save} className="primary-btn">
          حفظ وإعادة تحميل الواجهة
        </button>
      </div>
    </Panel>
  );
}
