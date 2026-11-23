import { Link } from 'react-router-dom';
import { Panel } from '../components/ui';

export default function PlaceholderPage({ title }: { title: string }) {
  return (
    <Panel className="space-y-4 py-10 text-center">
      <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl border border-blue-500/20 bg-blue-600/10 text-2xl font-bold text-blue-400">
        ⚡
      </div>
      <h2 className="text-2xl font-bold text-white">قسم {title}</h2>
      <p className="mx-auto max-w-md text-sm text-slate-400">
        هذا القسم يعرض البيانات الحية والمسجلة من خادم منظومة اليمن فيجن.
      </p>
      <Link to="/" className="primary-btn inline-block">
        العودة للرئيسية
      </Link>
    </Panel>
  );
}
