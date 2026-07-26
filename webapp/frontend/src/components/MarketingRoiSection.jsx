import { BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Legend, ResponsiveContainer } from 'recharts';
import { useApiData } from '../hooks/useApiData';
import StatCard from './StatCard';
import InfoTag from './InfoTag';
import LoadingState from './LoadingState';
import ErrorState from './ErrorState';
import { Megaphone, TrendingUp, Award } from 'lucide-react';
import { AXIS_STYLE, GRID_STYLE, TOOLTIP_PROPS, fmtMoney, fmtAxisNumber } from '../chartTheme';

export default function MarketingRoiSection() {
  const { data, loading, error } = useApiData('/kpi/marketing-roi/');
  if (loading) return <LoadingState label="Loading marketing ROI data..." />;
  if (error) return <ErrorState message="Error loading marketing ROI data." />;

  const totalSpend = data.by_channel.reduce((s, c) => s + c.total_spend, 0);
  const totalRevenue = data.by_channel.reduce((s, c) => s + c.total_revenue, 0);
  const bestChannel = [...data.by_channel].sort((a, b) => b.roas - a.roas)[0];

  return (
    <div>
      <h2>Marketing ROI &amp; CAC by Channel</h2>
      <p className="section-desc">
        Compares what each marketing channel costs against the revenue and new orders it actually drives, so ad
        budget can shift toward what's working and away from what isn't.
      </p>

      <div className="stat-grid">
        <StatCard icon={Megaphone} label="Total Ad Spend" value={fmtMoney(totalSpend)} accent="#ef4444" />
        <StatCard icon={TrendingUp} label="Total Revenue Attributed" value={fmtMoney(totalRevenue)} accent="#10b981" />
        <StatCard icon={Award} label="Best ROAS Channel" value={bestChannel.channel_code} sublabel={`${bestChannel.roas}x return per $1 spent`} accent="#06b6d4" />
      </div>

      <div className="chart-box">
        <h4 className="chart-title"><Megaphone size={14} /> Ad Spend vs. Revenue Earned, by Channel</h4>
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={data.by_channel}>
            <CartesianGrid {...GRID_STYLE} />
            <XAxis dataKey="channel_code" {...AXIS_STYLE} />
            <YAxis {...AXIS_STYLE} width={44} tickFormatter={fmtAxisNumber} />
            <Tooltip {...TOOLTIP_PROPS} formatter={(v) => fmtMoney(v)} />
            <Legend wrapperStyle={{ color: '#8c88a3', fontSize: 12 }} />
            <Bar dataKey="total_spend" fill="#ef4444" name="Ad Spend" radius={[4, 4, 0, 0]} />
            <Bar dataKey="total_revenue" fill="#10b981" name="Revenue Earned" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <table className="data-table">
        <thead>
          <tr>
            <th>Channel</th>
            <th>Spend</th>
            <th>Revenue</th>
            <th>Orders</th>
            <th>ROAS <InfoTag text="Return on Ad Spend: revenue earned per $1 of ad spend. Above 1x means the channel is profitable." /></th>
            <th>CAC <InfoTag text="Customer Acquisition Cost: average ad spend to win one paying customer through this channel." /></th>
          </tr>
        </thead>
        <tbody>
          {data.by_channel.map((c) => (
            <tr key={c.channel_code}>
              <td>{c.channel_code}</td>
              <td>{fmtMoney(c.total_spend)}</td>
              <td>{fmtMoney(c.total_revenue)}</td>
              <td>{c.total_orders.toLocaleString()}</td>
              <td>{c.roas}x</td>
              <td>{fmtMoney(c.cac)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
