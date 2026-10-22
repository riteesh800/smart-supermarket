import React, { useState, useEffect } from 'react';
import { api } from './services/api';
import Sidebar from './components/Sidebar';
import HomePage from './components/HomePage';
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
import ThemeDialog from './components/ThemeDialog';
import { ErrorBoundary } from './components/ErrorBoundary';
import { ColumnMappingProvider } from './context/ColumnMappingContext';
import { AuthProvider } from './context/AuthContext';

const PANELS = {
  home: HomePage,
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
  // Always default to 'home' whenever anyone opens the link
  const [active, setActive] = useState('home');
  const [flags, setFlags] = useState(null);

  const refreshFlags = () => {
    api.getUploadStatus().then(s => {
      setFlags(s.feature_flags || {});
    }).catch(() => {
      setFlags({});
    });
  };

  useEffect(() => {
    refreshFlags();
  }, []);

  function handleFlagsUpdate(newFlags) {
    setFlags(newFlags);
  }

  function handleNavigateAfterImport() {
    setActive('dashboard');
    refreshFlags();
  }

  const handleAuthStateChange = (action, user) => {
    refreshFlags();
    if (action === 'login' && user?.state_data?.active_panel && user.state_data.active_panel !== 'home') {
      // If user had an active panel previously, they can continue or stay on home
      // We respect user's previous active state if they wish, while defaulting to home on link open
    }
  };

  const mainRef = React.useRef(null);

  useEffect(() => {
    if (mainRef.current) {
      mainRef.current.scrollTo({ top: 0, behavior: 'instant' });
    }
  }, [active]);

  const Panel = PANELS[active] || HomePage;

  let panelProps = {};
  if (active === 'home') {
    panelProps = { onNavigate: setActive, flags, onRefreshFlags: refreshFlags };
  } else if (active === 'datasetup') {
    panelProps = { onFlagsUpdate: handleFlagsUpdate, onNavigateToDashboard: handleNavigateAfterImport };
  }

  return (
    <AuthProvider onAuthStateChange={handleAuthStateChange}>
      <ColumnMappingProvider>
        <Sidebar active={active} onNavigate={setActive} flags={flags} />
        <main ref={mainRef} className="main-content">
          <ErrorBoundary key={active}>
            <Panel {...panelProps} />
          </ErrorBoundary>
        </main>
        <ChatBot />
        <ThemeDialog />
      </ColumnMappingProvider>
    </AuthProvider>
  );
}
