import type { ReactNode } from 'react';

export function Panel({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <section className={`panel ${className}`}>{children}</section>;
}

export function PageHeading({
  title,
  subtitle,
  badge,
}: {
  title: string;
  subtitle?: string;
  badge?: string;
}) {
  return (
    <div className="mb-6 flex flex-wrap items-start justify-between gap-4 border-b border-slate-800 pb-4">
      <div>
        <h2 className="text-2xl font-bold text-white">{title}</h2>
        {subtitle && <p className="mt-1 text-sm text-slate-400">{subtitle}</p>}
      </div>
      {badge && (
        <span className="rounded-lg bg-blue-500/10 px-3 py-1.5 text-xs font-bold text-blue-400">
          {badge}
        </span>
      )}
    </div>
  );
}

export function StatCard({
  label,
  value,
  hint,
  accent = 'blue',
}: {
  label: string;
  value: ReactNode;
  hint: string;
  accent?: 'blue' | 'cyan' | 'emerald' | 'indigo';
}) {
  const accents: Record<string, string> = {
    blue: 'text-blue-400 bg-blue-500/10',
    cyan: 'text-cyan-400 bg-cyan-500/10',
    emerald: 'text-emerald-400 bg-emerald-500/10',
    indigo: 'text-indigo-400 bg-indigo-500/10',
  };

  return (
    <div className="panel relative overflow-hidden">
      <p className="mb-1 text-xs font-semibold text-slate-400">{label}</p>
      <div className="flex items-baseline justify-between gap-2">
        <h3 className="text-3xl font-extrabold text-white">{value}</h3>
        <span className={`rounded-full px-2.5 py-0.5 text-xs font-bold ${accents[accent]}`}>
          {hint}
        </span>
      </div>
    </div>
  );
}

export function EmptyState({ children }: { children: ReactNode }) {
  return <div className="p-8 text-center text-sm text-slate-500">{children}</div>;
}

export function formatTime(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? '—'
    : date.toLocaleTimeString('ar', { hour: '2-digit', minute: '2-digit' });
}

export function formatDateTime(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? '—' : date.toLocaleString('ar');
}
