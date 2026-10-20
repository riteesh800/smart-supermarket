import React, { useState, useRef } from 'react';
import { getFeatureRequirement } from '../constants/featureRequirements';
import LockedFeaturePopover from './LockedFeaturePopover';

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
  const [activeTooltip, setActiveTooltip] = useState(null);
  const leaveTimerRef = useRef(null);

  const handleMouseEnterItem = (e, item) => {
    if (leaveTimerRef.current) {
      clearTimeout(leaveTimerRef.current);
      leaveTimerRef.current = null;
    }

    const requirement = getFeatureRequirement(item.id);
    if (!requirement) return;

    const rect = e.currentTarget.getBoundingClientRect();
    setActiveTooltip({
      requirement,
      rect,
      itemId: item.id,
    });
  };

  const handleMouseLeaveItem = () => {
    leaveTimerRef.current = setTimeout(() => {
      setActiveTooltip(null);
    }, 180);
  };

  const handleMouseEnterPopover = () => {
    if (leaveTimerRef.current) {
      clearTimeout(leaveTimerRef.current);
      leaveTimerRef.current = null;
    }
  };

  const handleMouseLeavePopover = () => {
    setActiveTooltip(null);
  };

  const handleItemClick = (enabled, itemId) => {
    if (enabled) {
      onNavigate(itemId);
    } else {
      // If clicked while locked, direct user to Data Setup page
      onNavigate('datasetup');
      setActiveTooltip(null);
    }
  };

  return (
    <>
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
              const enabled = item.flag === null || (flags && flags.has_data && flags[item.flag] !== false);
              return (
                <div
                  key={item.id}
                  className={`nav-item ${active === item.id ? 'active' : ''} ${!enabled ? 'disabled' : ''}`}
                  onClick={() => handleItemClick(enabled, item.id)}
                  onMouseEnter={(e) => !enabled && handleMouseEnterItem(e, item)}
                  onMouseLeave={() => !enabled && handleMouseLeaveItem()}
                  aria-label={`${item.label} ${!enabled ? '(Locked - click to view setup)' : ''}`}
                >
                  <span className="nav-icon">{item.icon}</span>
                  <span>{item.label}</span>
                  {!enabled && <span className="nav-lock" title="">🔒</span>}
                </div>
              );
            })}
          </div>
        ))}
      </aside>

      {/* Floating feature unlock requirement popover */}
      {activeTooltip && (
        <LockedFeaturePopover
          requirement={activeTooltip.requirement}
          targetRect={activeTooltip.rect}
          isOpen={Boolean(activeTooltip)}
          onMouseEnterPopover={handleMouseEnterPopover}
          onMouseLeavePopover={handleMouseLeavePopover}
          onNavigate={(target) => {
            onNavigate(target);
            setActiveTooltip(null);
          }}
          placement="right"
        />
      )}
    </>
  );
}
