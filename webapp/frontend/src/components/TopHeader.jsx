import { Search } from 'lucide-react';

export default function TopHeader({ title }) {
  return (
    <header className="top-header">
      <h1>{title}</h1>
      <div className="top-header-right">
        <div className="search-box">
          <Search size={15} />
          <input placeholder="Search customers, orders, products..." />
        </div>
        <div className="avatar">HA</div>
      </div>
    </header>
  );
}
