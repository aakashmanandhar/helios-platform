import { BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer } from 'recharts';
import { useApiData } from '../hooks/useApiData';
import StatCard from './StatCard';
import LoadingState from './LoadingState';
import ErrorState from './ErrorState';
import { AlertTriangle, Clock } from 'lucide-react';
import { AXIS_STYLE, GRID_STYLE, TOOLTIP_PROPS, fmtNumber } from '../chartTheme';

export default function ChurnRiskSection() {
  const { data, loading, error } = useApiData('/kpi/churn-risk/');
  if (loading) return <LoadingState label="Loading churn risk data..." />;
  if (error) return <ErrorState message="Error loading churn risk data." />;

  const totalAtRisk = data.at_risk_summary.reduce((s, x) => s + x.customer_count, 0);
  const oldestBucket = data.recency_buckets[data.recency_buckets.length - 1];

  return (
    <div>
      <h2>Churn Risk</h2>
      <p className="section-desc">
        The longer it's been since a customer's last order (their "recency"), the more likely they are to have
        churned. This page flags customers who've gone quiet so re-engagement campaigns can reach them before
        they're gone for good.
      </p>

      <div className="stat-grid">
        <StatCard icon={AlertTriangle} label="Customers Needing Attention" value={fmtNumber(totalAtRisk)} sublabel="At Risk + Lost + Needs Attention segments" accent="#ef4444" />
        <StatCard icon={Clock} label={`Longest Inactive: ${oldestBucket?.recency_bucket}`} value={fmtNumber(oldestBucket?.customer_count)} sublabel="customers haven't ordered in this window" accent="#f59e0b" />
      </div>

      <div className="chart-row">
        <div className="chart-box">
          <h4 className="chart-title"><AlertTriangle size={14} /> Customers by Risk Segment</h4>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={data.at_risk_summary}>
              <CartesianGrid {...GRID_STYLE} />
              <XAxis dataKey="rfm_segment" {...AXIS_STYLE} />
              <YAxis {...AXIS_STYLE} label={{ value: 'Customers', angle: -90, position: 'insideLeft', style: { fill: '#9ca3af', fontSize: 11 } }} />
              <Tooltip {...TOOLTIP_PROPS} />
              <Bar dataKey="customer_count" name="Customers" fill="#ef4444" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="chart-box">
          <h4 className="chart-title"><Clock size={14} /> Days Since Last Order</h4>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={data.recency_buckets}>
              <CartesianGrid {...GRID_STYLE} />
              <XAxis dataKey="recency_bucket" {...AXIS_STYLE} label={{ value: 'Days since last order', position: 'insideBottom', offset: -2, style: { fill: '#9ca3af', fontSize: 11 } }} />
              <YAxis {...AXIS_STYLE} label={{ value: 'Customers', angle: -90, position: 'insideLeft', style: { fill: '#9ca3af', fontSize: 11 } }} />
              <Tooltip {...TOOLTIP_PROPS} />
              <Bar dataKey="customer_count" name="Customers" fill="#f59e0b" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
