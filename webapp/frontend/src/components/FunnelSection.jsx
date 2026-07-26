import { BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer, Cell } from 'recharts';
import { useApiData } from '../hooks/useApiData';
import StatCard from './StatCard';
import LoadingState from './LoadingState';
import ErrorState from './ErrorState';
import { Eye, ShoppingCart, CreditCard, CheckCircle, Filter } from 'lucide-react';
import { COLORS, AXIS_STYLE, GRID_STYLE, TOOLTIP_PROPS, fmtNumber, fmtAxisNumber } from '../chartTheme';

export default function FunnelSection() {
  const { data, loading, error } = useApiData('/kpi/funnel-conversion/');
  if (loading) return <LoadingState label="Loading funnel data..." />;
  if (error) return <ErrorState message="Error loading funnel data." />;

  const funnelSteps = [
    { stage: 'Viewed Product', count: data.overall.viewed_sessions },
    { stage: 'Added to Cart', count: data.overall.carted_sessions },
    { stage: 'Started Checkout', count: data.overall.checkout_sessions },
    { stage: 'Completed Purchase', count: data.overall.purchase_sessions },
  ];

  return (
    <div>
      <h2>Funnel Conversion</h2>
      <p className="section-desc">
        Every shopping session moves through four stages — viewing a product, adding it to cart, starting checkout,
        and completing the purchase. The percentage between each stage shows exactly where shoppers drop off.
      </p>

      <div className="stat-grid">
        <StatCard icon={Eye} label="View → Cart" value={`${data.overall.view_to_cart_pct}%`} sublabel="of viewers add to cart" accent="#7c3aed" />
        <StatCard icon={ShoppingCart} label="Cart → Checkout" value={`${data.overall.cart_to_checkout_pct}%`} sublabel="of carts reach checkout" accent="#06b6d4" />
        <StatCard icon={CreditCard} label="Checkout → Purchase" value={`${data.overall.checkout_to_purchase_pct}%`} sublabel="of checkouts convert" accent="#10b981" />
        <StatCard icon={CheckCircle} label="Total Sessions" value={fmtNumber(data.overall.sessions)} sublabel="shopping sessions tracked" accent="#f59e0b" />
      </div>

      <div className="chart-row">
        <div className="chart-box">
          <h4 className="chart-title"><Filter size={14} /> Overall Funnel (sessions per stage)</h4>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={funnelSteps} layout="vertical" margin={{ left: 20 }}>
              <CartesianGrid {...GRID_STYLE} />
              <XAxis type="number" {...AXIS_STYLE} tickFormatter={fmtAxisNumber} />
              <YAxis type="category" dataKey="stage" {...AXIS_STYLE} width={110} />
              <Tooltip {...TOOLTIP_PROPS} />
              <Bar dataKey="count" name="Sessions" radius={[0, 4, 4, 0]}>
                {funnelSteps.map((entry, i) => <Cell key={entry.stage} fill={COLORS[i % COLORS.length]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="chart-box">
          <h4 className="chart-title"><ShoppingCart size={14} /> Checkout Conversion Rate by Channel</h4>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={data.by_channel}>
              <CartesianGrid {...GRID_STYLE} />
              <XAxis dataKey="channel_code" {...AXIS_STYLE} />
              <YAxis {...AXIS_STYLE} unit="%" />
              <Tooltip {...TOOLTIP_PROPS} />
              <Bar dataKey="overall_conversion_pct" name="Conversion rate" fill="#06b6d4" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
