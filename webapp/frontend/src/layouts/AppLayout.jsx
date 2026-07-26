import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import TopHeader from '../components/TopHeader';

export const ROUTES = [
  { key: 'overview', label: 'Overview', path: '/' },
  { key: 'ltv', label: 'LTV & RFM', path: '/ltv-rfm' },
  { key: 'churn', label: 'Churn Risk', path: '/churn-risk' },
  { key: 'marketing', label: 'Marketing ROI', path: '/marketing-roi' },
  { key: 'funnel', label: 'Funnel Conversion', path: '/funnel-conversion' },
  { key: 'inventory', label: 'Inventory Risk', path: '/inventory-risk' },
  { key: 'assistant', label: 'AI Assistant', path: '/assistant' },
];

export default function AppLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const active = ROUTES.find((r) => r.path === location.pathname) || ROUTES[0];

  return (
    <div className="app-shell">
      <Sidebar routes={ROUTES} activeKey={active.key} onSelect={(path) => navigate(path)} />
      <div className="main-area">
        <TopHeader title={active.label} />
        <div className="main-content">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
