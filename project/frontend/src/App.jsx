import React, { useState, useEffect, useRef } from 'react';
import './index.css';
import { api } from './services/api';
import Sidebar from './components/Sidebar';
import DashboardOverview from './components/DashboardOverview';
import InventoryPanel from './components/InventoryPanel';
import SalesInsightsPanel from './components/SalesInsightsPanel';
import CustomerAnalyticsPanel from './components/CustomerAnalyticsPanel';
import DemandForecastPanel from './components/DemandForecastPanel';
import RecommendationsPanel from './components/RecommendationsPanel';
import AnomaliesPanel from './components/AnomaliesPanel';
import DynamicPricingPanel from './components/DynamicPricingPanel';
import SupplierPanel from './components/SupplierPanel';
import SalesHeatmapPanel from './components/SalesHeatmapPanel';
import DataSetupPanel from './components/DataSetupPanel';
import ChatBot from './components/ChatBot';

const PANELS = {
  dashboard: DashboardOverview,
  inventory: InventoryPanel,
  sales: SalesInsightsPanel,
  customers: CustomerAnalyticsPanel,
  forecast: DemandForecastPanel,
  recommendations: RecommendationsPanel,
  anomalies: AnomaliesPanel,
  pricing: DynamicPricingPanel,
  suppliers: SupplierPanel,
  heatmap: SalesHeatmapPanel,
  datasetup: DataSetupPanel,
};

export default function App() {
  const [active, setActive] = useState('dashboard');
  const [flags, setFlags] = useState(null);
  const didInitialRedirect = useRef(false);

  useEffect(() => {
    api.getUploadStatus().then(s => {
      setFlags(s.feature_flags || {});
      // Only redirect to data setup on first load if no data
      if (!didInitialRedirect.current && !s.feature_flags?.has_data) {
        setActive('datasetup');
      }
      didInitialRedirect.current = true;
    }).catch(() => {
      setFlags({});
      didInitialRedirect.current = true;
    });
  }, []);

  function handleFlagsUpdate(newFlags) {
    setFlags(newFlags);
    // Only auto-navigate to dashboard after a fresh import
    // (user was on datasetup and data just became available)
  }

  function handleNavigateAfterImport() {
    setActive('dashboard');
    // Refresh flags
    api.getUploadStatus().then(s => setFlags(s.feature_flags || {})).catch(() => {});
  }

  const Panel = PANELS[active] || DashboardOverview;

  const panelProps = active === 'datasetup'
    ? { onFlagsUpdate: handleFlagsUpdate, onNavigateToDashboard: handleNavigateAfterImport }
    : {};

  return (
    <>
      <Sidebar active={active} onNavigate={setActive} flags={flags} />
      <main className="main-content">
        <Panel key={active} {...panelProps} />
      </main>
      <ChatBot />
    </>
  );
}
