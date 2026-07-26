import { BrowserRouter, Routes, Route } from 'react-router-dom';
import AppLayout from './layouts/AppLayout';
import OverviewSection from './components/OverviewSection';
import LtvRfmSection from './components/LtvRfmSection';
import ChurnRiskSection from './components/ChurnRiskSection';
import MarketingRoiSection from './components/MarketingRoiSection';
import FunnelSection from './components/FunnelSection';
import InventorySection from './components/InventorySection';
import AssistantPage from './pages/AssistantPage';
import './App.css';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<OverviewSection />} />
          <Route path="/ltv-rfm" element={<LtvRfmSection />} />
          <Route path="/churn-risk" element={<ChurnRiskSection />} />
          <Route path="/marketing-roi" element={<MarketingRoiSection />} />
          <Route path="/funnel-conversion" element={<FunnelSection />} />
          <Route path="/inventory-risk" element={<InventorySection />} />
          <Route path="/assistant" element={<AssistantPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
