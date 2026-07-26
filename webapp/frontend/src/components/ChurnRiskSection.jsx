import { BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer } from 'recharts';
import { useApiData } from '../hooks/useApiData';
import StatCard from './StatCard';
import LoadingState from './LoadingState';
import ErrorState from './ErrorState';
import { AlertTriangle, Clock, Cpu } from 'lucide-react';
import { AXIS_STYLE, GRID_STYLE, TOOLTIP_PROPS, fmtNumber, fmtAxisNumber } from '../chartTheme';

const PILL_CLASS = { High: 'pill pill-high', Medium: 'pill pill-medium', Low: 'pill pill-low' };

export default function ChurnRiskSection() {
  const { data, loading, error } = useApiData('/kpi/churn-risk/');
  const { data: modelData, loading: modelLoading } = useApiData('/churn/top-risk/?limit=10');

  if (loading) return <LoadingState label="Loading churn risk data..." />;
  if (error) return <ErrorState message="Error loading churn risk data." />;

  const totalAtRisk = data.at_risk_summary.reduce((s, x) => s + x.customer_count, 0);
  const oldestBucket = data.recency_buckets[data.recency_buckets.length - 1];
  const modelSummary = modelData?.summary || [];
  const highRiskCount = modelSummary.find((s) => s.risk_band === 'High')?.customer_count;

  return (
    <div>
      <h2>Churn Risk</h2>
      <p className="section-desc">
        The longer it's been since a customer's last order (their "recency"), the more likely they are to have
        churned. This page flags customers who've gone quiet so re-engagement campaigns can reach them before
        they're gone for good.
      </p>
      <div className="stat-grid">
        <StatCard icon={AlertTriangle} label="Customers Needing Attention" value={fmtNumber(totalAtRisk)} sublabel="At Risk + Lost + Needs Attention segments"accent="#ef4444" />
        <StatCard icon={Clock} label={`Longest Inactive: ${oldestBucket?.recency_bucket}`} value={fmtNumber(oldestBucket?.customer_count)} sublabel="customershaven't ordered in this window" accent="#f59e0b" />
      </div>
      <div className="chart-row">
        <div className="chart-box">
          <h4 className="chart-title"><AlertTriangle size={14} /> Customers by Risk Segment</h4>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={data.at_risk_summary}>
              <CartesianGrid {...GRID_STYLE} />
              <XAxis dataKey="rfm_segment" {...AXIS_STYLE} />
              <YAxis {...AXIS_STYLE} width={44} tickFormatter={fmtAxisNumber} />
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
              <YAxis {...AXIS_STYLE} width={44} tickFormatter={fmtAxisNumber} />
              <Tooltip {...TOOLTIP_PROPS} />
              <Bar dataKey="customer_count" name="Customers" fill="#f59e0b" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <h3><Cpu size={13} style={{ verticalAlign: 'middle', marginRight: 4 }} />Model-Predicted Churn Risk</h3>
      <p className="section-desc">
        The segments above are a fixed business rule (recency/frequency/monetary thresholds). This section is a
        trained logistic regression model instead: it's scored against every customer, served live from the Feast
        feature store, and predictions are written back into <code>gold.mart_churn_predictions</code> so the RAG
        assistant can reference the same number. Trained on a 90-day forward holdout — features from a customer's
        history before a cutoff, label from whether they ordered again after it — to avoid the model just
        rediscovering the rule that built the RFM segments above.
      </p>
      {modelLoading || !modelData ? (
        <LoadingState label="Loading model predictions..." />
      ) : (
        <>
          <div className="stat-grid">
            <StatCard icon={Cpu} label="High Risk (Model Score \u2265 0.6)" value={fmtNumber(highRiskCount)} sublabel="customers, live model score" accent="#ef4444" />
          </div>
          <table className="data-table">
            <thead><tr><th>Name</th><th>Region</th><th>RFM Segment</th><th>Churn Probability</th><th>Risk Band</th></tr></thead>
            <tbody>
              {modelData.top_risk.map((c) => (
                <tr key={c.customer_id}>
                  <td>{c.first_name} {c.last_name}</td>
                  <td>{c.region}</td>
                  <td>{c.rfm_segment}</td>
                  <td>{(c.churn_probability * 100).toFixed(1)}%</td>
                  <td><span className={PILL_CLASS[c.risk_band] || 'pill'}>{c.risk_band}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </div>
  );
}
