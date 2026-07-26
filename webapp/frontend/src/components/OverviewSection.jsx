import { useApiData } from '../hooks/useApiData';
import StatCard from './StatCard';
import InfoTag from './InfoTag';
import LoadingState from './LoadingState';
import ErrorState from './ErrorState';
import {
  BarChart, Bar, AreaChart, Area, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import { DollarSign, UserX, TrendingUp, ShoppingCart, BarChart3, PieChart as PieChartIcon, Users, Trophy, Crown } from 'lucide-react';
import { COLORS, AXIS_STYLE, GRID_STYLE, TOOLTIP_PROPS, fmtMoney, initials } from '../chartTheme';

export default function OverviewSection() {
  const ltv = useApiData('/kpi/ltv-rfm/');
  const churn = useApiData('/kpi/churn-risk/');
  const marketing = useApiData('/kpi/marketing-roi/');
  const funnel = useApiData('/kpi/funnel-conversion/');
  const inventory = useApiData('/kpi/inventory-risk/');

  const loading = ltv.loading || churn.loading || marketing.loading || funnel.loading || inventory.loading;
  const anyError = ltv.error || churn.error || marketing.error || funnel.error || inventory.error;

  if (loading) return <LoadingState label="Loading platform overview..." />;
  if (anyError) return <ErrorState message="Error loading one or more KPI endpoints." />;

  const totalLtv = ltv.data.segments.reduce((sum, s) => sum + s.total_ltv, 0);
  const totalCustomers = ltv.data.segments.reduce((sum, s) => sum + s.customer_count, 0);
  const atRiskCount = churn.data.at_risk_summary.reduce((sum, s) => sum + s.customer_count, 0);
  const totalSpend = marketing.data.by_channel.reduce((sum, c) => sum + c.total_spend, 0);
  const totalRevenue = marketing.data.by_channel.reduce((sum, c) => sum + c.total_revenue, 0);
  const overallRoas = totalSpend ? (totalRevenue / totalSpend).toFixed(2) : '-';
  const conversionPct = funnel.data.overall.checkout_to_purchase_pct;

  const monthlyTotals = {};
  marketing.data.monthly_trend.forEach((row) => {
    const key = row.month;
    if (!monthlyTotals[key]) monthlyTotals[key] = { month: key, spend: 0, revenue: 0 };
    monthlyTotals[key].spend += row.spend;
    monthlyTotals[key].revenue += row.revenue;
  });
  const monthlySeries = Object.values(monthlyTotals).sort((a, b) => a.month.localeCompare(b.month));
  const lastMonth = monthlySeries[monthlySeries.length - 1];
  const prevMonth = monthlySeries[monthlySeries.length - 2];
  let revenueTrend = null;
  if (lastMonth && prevMonth && prevMonth.revenue > 0) {
    const pct = (((lastMonth.revenue - prevMonth.revenue) / prevMonth.revenue) * 100).toFixed(1);
    revenueTrend = { direction: pct >= 0 ? 'up' : 'down', value: `${Math.abs(pct)}% MoM` };
  }

  const channelShare = marketing.data.by_channel
    .map((c) => ({ ...c, pct: totalSpend ? Math.round((c.total_spend / totalSpend) * 100) : 0 }))
    .sort((a, b) => b.total_spend - a.total_spend);

  const bestChannel = [...marketing.data.by_channel].sort((a, b) => b.roas - a.roas)[0];

  return (
    <div>
      <h2>Platform Overview</h2>
      <p className="section-desc">
        A single, at-a-glance snapshot combining customer value, marketing performance, checkout drop-off, and inventory
        health — the same certified numbers used by every other page on this dashboard.
      </p>

      <div className="stat-grid">
        <StatCard icon={DollarSign} label="Total Customer LTV" value={fmtMoney(totalLtv)} sublabel={`${totalCustomers.toLocaleString()} customers`} accent="#7c3aed" trend={revenueTrend} />
        <StatCard icon={UserX} label="At-Risk / Lost Customers" value={atRiskCount.toLocaleString()} sublabel="haven't ordered recently" accent="#ef4444" />
        <StatCard icon={TrendingUp} label="Marketing ROAS" value={`${overallRoas}x`} sublabel={`$${overallRoas} earned per $1 spent`} accent="#10b981" />
        <StatCard icon={ShoppingCart} label="Checkout Conversion" value={`${conversionPct}%`} sublabel="of checkouts become orders" accent="#06b6d4" />
      </div>

      <div className="chart-row">
        <div className="chart-box" style={{ flex: 1.4 }}>
          <h4 className="chart-title"><TrendingUp size={14} /> Revenue &amp; Spend Trend (monthly)</h4>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={monthlySeries}>
              <defs>
                <linearGradient id="rev" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#7c3aed" stopOpacity={0.35} />
                  <stop offset="95%" stopColor="#7c3aed" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid {...GRID_STYLE} />
              <XAxis dataKey="month" {...AXIS_STYLE} tickFormatter={(m) => m?.slice(0, 7)} />
              <YAxis {...AXIS_STYLE} label={{ value: 'Revenue ($)', angle: -90, position: 'insideLeft', style: { fill: '#9ca3af', fontSize: 11 } }} />
              <Tooltip {...TOOLTIP_PROPS} formatter={(v) => fmtMoney(v)} />
              <Area type="monotone" dataKey="revenue" name="Revenue" stroke="#7c3aed" fill="url(#rev)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
        <div className="chart-box">
          <h4 className="chart-title"><BarChart3 size={14} /> Revenue vs. Spend by Channel</h4>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={marketing.data.by_channel}>
              <CartesianGrid {...GRID_STYLE} />
              <XAxis dataKey="channel_code" {...AXIS_STYLE} />
              <YAxis {...AXIS_STYLE} />
              <Tooltip {...TOOLTIP_PROPS} formatter={(v) => fmtMoney(v)} />
              <Legend wrapperStyle={{ color: '#8c88a3', fontSize: 12 }} />
              <Bar dataKey="total_spend" fill="#ef4444" name="Ad Spend" radius={[4, 4, 0, 0]} />
              <Bar dataKey="total_revenue" fill="#10b981" name="Revenue Earned" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="chart-row">
        <div className="chart-box">
          <h4 className="chart-title"><PieChartIcon size={14} /> Ad Spend Share by Channel</h4>
          <div className="progress-list">
            {channelShare.map((c, i) => (
              <div className="progress-row" key={c.channel_code}>
                <div className="progress-label">
                  <span>{c.channel_code}</span>
                  <span>{c.pct}% of total spend</span>
                </div>
                <div className="progress-track">
                  <div className="progress-fill" style={{ width: `${c.pct}%`, background: COLORS[i % COLORS.length] }} />
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="chart-box">
          <h4 className="chart-title"><Users size={14} /> Customers by RFM Segment</h4>
          <ResponsiveContainer width="100%" height={190}>
            <PieChart>
              <Pie data={ltv.data.segments} dataKey="customer_count" nameKey="rfm_segment" innerRadius={45} outerRadius={72} paddingAngle={2} stroke="none">
                {ltv.data.segments.map((entry, i) => <Cell key={entry.rfm_segment} fill={COLORS[i % COLORS.length]} />)}
              </Pie>
              <Tooltip {...TOOLTIP_PROPS} />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="chart-box highlight-box">
          <h4 className="chart-title"><Trophy size={14} /> Best Performing Channel</h4>
          <div className="highlight-value">{bestChannel?.channel_code}</div>
          <div className="highlight-sub">{bestChannel?.roas}x ROAS — highest return per ad dollar</div>
        </div>
      </div>

      <h3><Crown size={13} style={{ verticalAlign: 'middle', marginRight: 4 }} />Top Customers by Lifetime Value</h3>
      <table className="data-table">
        <thead><tr><th>Customer</th><th>Region</th><th>Lifetime Value</th><th>Segment</th></tr></thead>
        <tbody>
          {ltv.data.top_customers.map((c) => (
            <tr key={c.customer_id}>
              <td>
                <div className="customer-cell">
                  <span className="avatar-sm">{initials(c.first_name, c.last_name)}</span>
                  {c.first_name} {c.last_name}
                </div>
              </td>
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
