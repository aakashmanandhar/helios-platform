export default function StatCard({ icon: Icon, label, value, sublabel, trend, accent = '#7c3aed' }) {
  return (
    <div className="stat-card">
      <div className="stat-top">
        {Icon && (
          <div className="stat-icon" style={{ background: `${accent}1a`, color: accent }}>
            <Icon size={18} />
          </div>
        )}
        {trend && (
          <span className={`trend-badge ${trend.direction}`}>
            {trend.direction === 'up' ? '▲' : '▼'} {trend.value}
          </span>
        )}
      </div>
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
      {sublabel && <div className="stat-sublabel">{sublabel}</div>}
    </div>
  );
}
