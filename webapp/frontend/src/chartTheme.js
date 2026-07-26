export const COLORS = ['#7c3aed', '#06b6d4', '#10b981', '#f59e0b', '#ec4899', '#ef4444', '#6366f1'];

export const AXIS_STYLE = { stroke: '#b3aec9', fontSize: 12 };
export const GRID_STYLE = { stroke: '#ebe8f7', strokeDasharray: '3 3' };

export const TOOLTIP_PROPS = {
  contentStyle: {
    background: '#ffffff',
    border: '1px solid #ebe8f7',
    borderRadius: 10,
    color: '#1f1b3a',
    fontSize: 13,
    boxShadow: '0 4px 16px rgba(31,27,58,0.08)',
  },
  labelStyle: { color: '#1f1b3a', fontWeight: 600, marginBottom: 4 },
  itemStyle: { color: '#4b4767' },
  cursor: { fill: 'rgba(124,58,237,0.05)' },
};

export function fmtMoney(n) {
  if (n === null || n === undefined) return '-';
  const abs = Math.abs(n);
  if (abs >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
  if (abs >= 1_000) return `$${(n / 1_000).toFixed(1)}K`;
  return `$${n.toLocaleString()}`;
}

export function fmtNumber(n) {
  if (n === null || n === undefined) return '-';
  return n.toLocaleString();
}

export function initials(first, last) {
  return `${(first || '?')[0]}${(last || '?')[0]}`.toUpperCase();
}

export function fmtAxisNumber(n) {
  if (n === null || n === undefined) return '';
  const abs = Math.abs(n);
  if (abs >= 1_000_000) return `${(n / 1_000_000).toFixed(0)}M`;
  if (abs >= 1_000) return `${(n / 1_000).toFixed(0)}K`;
  return `${n}`;
}
