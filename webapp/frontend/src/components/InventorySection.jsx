import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Legend, ResponsiveContainer } from 'recharts';
import { useApiData } from '../hooks/useApiData';
import StatCard from './StatCard';
import InfoTag from './InfoTag';
import LoadingState from './LoadingState';
import ErrorState from './ErrorState';
import { PackageX, PackagePlus, DollarSign, Warehouse } from 'lucide-react';
import { TOOLTIP_PROPS, AXIS_STYLE, GRID_STYLE, fmtMoney, fmtNumber, fmtAxisNumber } from '../chartTheme';

const STATUS_COLORS = { Healthy: '#10b981', Overstocked: '#f59e0b', 'Reorder Needed': '#ec4899', Stockout: '#ef4444' };
const STATUS_DEFS = {
  Healthy: 'Stock level is within the normal target range.',
  Overstocked: 'More units on hand than needed — ties up cash and warehouse space.',
  'Reorder Needed': 'Approaching the reorder point — order soon to avoid running out.',
  Stockout: 'Out of stock right now — actively losing sales until restocked.',
};

export default function InventorySection() {
  const { data, loading, error } = useApiData('/kpi/inventory-risk/');
  if (loading) return <LoadingState label="Loading inventory data..." />;
  if (error) return <ErrorState message="Error loading inventory data." />;

  const totalStockouts = data.by_warehouse.reduce((s, w) => s + w.stockout_count, 0);
  const totalOverstocks = data.by_warehouse.reduce((s, w) => s + w.overstock_count, 0);
  const atRiskValue = data.status_summary
    .filter((s) => s.inventory_status !== 'Healthy')
    .reduce((s, x) => s + x.total_value, 0);

  return (
    <div>
      <h2>Inventory Risk</h2>
      <p className="section-desc">
        Every product is either healthy, at risk of running out (stockout), or sitting in excess (overstock) —
        both extremes cost money, either in lost sales or tied-up cash.
      </p>

      <div className="stat-grid">
        <StatCard icon={PackageX} label="Stockout SKUs" value={fmtNumber(totalStockouts)} sublabel="products currently out of stock" accent="#ef4444" />
        <StatCard icon={PackagePlus} label="Overstocked SKUs" value={fmtNumber(totalOverstocks)} sublabel="products with excess inventory" accent="#f59e0b" />
        <StatCard icon={DollarSign} label="At-Risk Inventory Value" value={fmtMoney(atRiskValue)} sublabel="tied up in stockout + overstock" accent="#ec4899" />
      </div>

      <div className="segment-legend">
        {data.status_summary.map((s) => (
          <div className="segment-legend-item" key={s.inventory_status}>
            <strong style={{ color: STATUS_COLORS[s.inventory_status] }}>
              {s.inventory_status} — {s.product_count.toLocaleString()} products
            </strong>
            {STATUS_DEFS[s.inventory_status]}
          </div>
        ))}
      </div>

      <div className="chart-row">
        <div className="chart-box">
          <h4 className="chart-title">Products by Status</h4>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={data.status_summary} dataKey="product_count" nameKey="inventory_status" innerRadius={50} outerRadius={80} paddingAngle={2} stroke="none">
                {data.status_summary.map((entry) => (
                  <Cell key={entry.inventory_status} fill={STATUS_COLORS[entry.inventory_status] || '#9ca3af'} />
                ))}
              </Pie>
              <Tooltip {...TOOLTIP_PROPS} />
              <Legend wrapperStyle={{ color: '#8c88a3', fontSize: 12 }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="chart-box">
          <h4 className="chart-title"><Warehouse size={14} /> Stockouts / Overstocks by Warehouse</h4>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={data.by_warehouse}>
              <CartesianGrid {...GRID_STYLE} />
              <XAxis dataKey="warehouse_code" {...AXIS_STYLE} />
              <YAxis {...AXIS_STYLE} width={44} tickFormatter={fmtAxisNumber} />
              <Tooltip {...TOOLTIP_PROPS} />
              <Legend wrapperStyle={{ color: '#8c88a3', fontSize: 12 }} />
              <Bar dataKey="stockout_count" fill="#ef4444" name="Stockouts" radius={[4, 4, 0, 0]} />
              <Bar dataKey="overstock_count" fill="#f59e0b" name="Overstocks" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
