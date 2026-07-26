import { LayoutDashboard, Users, AlertTriangle, Megaphone, Filter, Package, Bot } from 'lucide-react';

const ICONS = {
  overview: LayoutDashboard,
  ltv: Users,
  churn: AlertTriangle,
  marketing: Megaphone,
  funnel: Filter,
  inventory: Package,
  assistant: Bot,
};

export default function Sidebar({ routes, activeKey, onSelect }) {
  const kpiRoutes = routes.filter((r) => r.key !== 'assistant');
  const assistantRoute = routes.find((r) => r.key === 'assistant');

  const renderItem = (r) => {
    const Icon = ICONS[r.key];
    return (
      <button
        key={r.key}
        className={r.key === activeKey ? 'nav-item active' : 'nav-item'}
        onClick={() => onSelect(r.path)}
      >
        <Icon size={17} strokeWidth={2} />
        <span>{r.label}</span>
      </button>
    );
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <span className="logo-dot" />
        Helios
      </div>
      <div className="sidebar-section-label">Analytics</div>
      <nav className="sidebar-nav">
        {kpiRoutes.map(renderItem)}
      </nav>
      <div className="sidebar-section-label">AI</div>
      <nav className="sidebar-nav">
        {assistantRoute && renderItem(assistantRoute)}
      </nav>
    </aside>
  );
}
