import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useApiData } from '../hooks/useApiData';
import StatCard from './StatCard';
import InfoTag from './InfoTag';
import LoadingState from './LoadingState';
import ErrorState from './ErrorState';
import { Users, Crown } from 'lucide-react';
import { COLORS, TOOLTIP_PROPS, fmtMoney } from '../chartTheme';

const SEGMENT_DEFS = {
  Champions: 'Bought recently, buy often, and spend the most — your best customers.',
  'Loyal Customers': 'Regular, reliable buyers with solid spend — not quite top-tier yet.',
  'At Risk': 'Used to order often but haven\u2019t purchased in a while — worth a win-back offer.',
  Lost: 'Haven\u2019t purchased in a long time — likely churned.',
  'New Customers': 'Recent first-time buyers still building purchase history.',
  'Needs Attention': 'Below-average recency and frequency — a light nudge could re-engage them.',
};

export default function LtvRfmSection() {
  const { data, loading, error } = useApiData('/kpi/ltv-rfm/');
  if (loading) return <LoadingState label="Loading LTV & RFM data..." />;
  if (error) return <ErrorState message="Error loading LTV/RFM data." />;

  const totalLtv = data.segments.reduce((s, x) => s + x.total_ltv, 0);
  const totalCustomers = data.segments.reduce((s, x) => s + x.customer_count, 0);
  const topSegment = [...data.segments].sort((a, b) => b.total_ltv - a.total_ltv)[0];

  return (
    <div>
      <h2>Customer Lifetime Value &amp; RFM Segmentation</h2>
      <p className="section-desc">
        Every customer is scored on <strong>R</strong>ecency (days since last order), <strong>F</strong>requency (how
        often they buy), and <strong>M</strong>onetary value (how much they spend) — then grouped into segments so you
        know exactly who to reward and who's slipping away.
      </p>

      <div className="stat-grid">
        <StatCard label={<>Total Lifetime Value<InfoTag text="Sum of all-time revenue from every customer in this dataset." /></>} value={fmtMoney(totalLtv)} sublabel={`${totalCustomers.toLocaleString()} customers`} accent="#7c3aed" />
        <StatCard label="Largest Segment" value={topSegment.rfm_segment} sublabel={`${fmtMoney(topSegment.total_ltv)} total LTV`} accent="#10b981" />
        <StatCard label="Avg LTV — Champions" value={fmtMoney(data.segments.find((s) => s.rfm_segment === 'Champions')?.avg_ltv)} sublabel="per customer, your top tier" accent="#f59e0b" />
      </div>

      <h3><Users size={13} style={{ verticalAlign: 'middle', marginRight: 4 }} />What each segment means</h3>
      <div className="segment-legend">
        {data.segments.map((s) => (
          <div className="segment-legend-item" key={s.rfm_segment}>
            <strong>{s.rfm_segment} — {s.customer_count.toLocaleString()} customers</strong>
            {SEGMENT_DEFS[s.rfm_segment]}
          </div>
        ))}
      </div>

      <div className="chart-row">
        <div className="chart-box">
          <ResponsiveContainer width="100%" height={230}>
            <PieChart>
              <Pie data={data.segments} dataKey="customer_count" nameKey="rfm_segment" innerRadius={55} outerRadius={85} paddingAngle={2} stroke="none">
                {data.segments.map((entry, i) => <Cell key={entry.rfm_segment} fill={COLORS[i % COLORS.length]} />)}
              </Pie>
              <Tooltip {...TOOLTIP_PROPS} />
              <Legend wrapperStyle={{ color: '#8c88a3', fontSize: 12 }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <table className="data-table">
          <thead><tr><th>Segment</th><th>Customers</th><th>Avg LTV</th><th>Total LTV</th></tr></thead>
          <tbody>
            {data.segments.map((s) => (
              <tr key={s.rfm_segment}>
                <td>{s.rfm_segment}</td>
                <td>{s.customer_count.toLocaleString()}</td>
                <td>{fmtMoney(s.avg_ltv)}</td>
                <td>{fmtMoney(s.total_ltv)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <h3><Crown size={13} style={{ verticalAlign: 'middle', marginRight: 4 }} />Top 10 Customers by Lifetime Value</h3>
      <table className="data-table">
        <thead><tr><th>Name</th><th>Region</th><th>LTV</th><th>Segment</th></tr></thead>
        <tbody>
          {data.top_customers.map((c) => (
            <tr key={c.customer_id}>
              <td>{c.first_name} {c.last_name}</td>
              <td>{c.region}</td>
              <td>{fmtMoney(c.lifetime_value)}</td>
              <td><span className="pill">{c.rfm_segment}</span></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
