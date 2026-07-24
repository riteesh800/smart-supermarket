import React from 'react';

const navItems = [
  { section: 'Data', items: [
    { id: 'datasetup', icon: '📁', label: 'Data Setup', flag: null },
  ]},
  { section: 'Overview', items: [
    { id: 'dashboard', icon: '📊', label: 'Dashboard', flag: 'enable_dashboard' },
  ]},
  { section: 'Management', items: [
    { id: 'inventory', icon: '📦', label: 'Inventory', flag: 'enable_inventory' },
    { id: 'sales', icon: '🛍️', label: 'Sales Insights', flag: 'enable_sales' },
    { id: 'customers', icon: '👥', label: 'Customers', flag: 'enable_customers' },
    { id: 'suppliers', icon: '🚚', label: 'Suppliers', flag: 'enable_suppliers' },
  ]},
  { section: 'Intelligence', items: [
    { id: 'forecast', icon: '📈', label: 'Demand Forecast', flag: 'enable_forecast' },
    { id: 'recommendations', icon: '🤖', label: 'Recommendations', flag: 'enable_recommendations' },
    { id: 'pricing', icon: '💲', label: 'Dynamic Pricing', flag: 'enable_pricing' },
    { id: 'heatmap', icon: '🔥', label: 'Sales Heatmap', flag: 'enable_heatmap' },
    { id: 'anomalies', icon: '⚠️', label: 'Anomalies', flag: 'enable_anomalies' },
  ]},
];

export default function Sidebar({ active, onNavigate, flags }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="logo-icon">🏪</div>
        <div>
          <h1>SmartMart</h1>
          <span>AI Intelligence v3</span>
        </div>
      </div>

      {navItems.map(section => (
        <div className="nav-section" key={section.section}>
          <div className="nav-section-title">{section.section}</div>
          {section.items.map(item => {
            const enabled = item.flag === null || !flags || (flags.has_data !== false && flags[item.flag] !== false);
            return (
              <div
                key={item.id}
                className={`nav-item ${active === item.id ? 'active' : ''} ${!enabled ? 'disabled' : ''}`}
                onClick={() => enabled && onNavigate(item.id)}
                title={!enabled ? 'Upload data to enable this feature' : ''}
              >
                <span className="nav-icon">{item.icon}</span>
                <span>{item.label}</span>
                {!enabled && <span className="nav-lock">🔒</span>}
              </div>
            );
          })}
        </div>
      ))}
    </aside>
  );
}
