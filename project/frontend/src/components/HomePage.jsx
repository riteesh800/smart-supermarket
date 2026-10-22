import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import AuthModal from './AuthModal';

const FEATURES = [
  {
    id: 'datasetup',
    title: 'Data Setup & Pipeline',
    section: 'Data',
    icon: '📁',
    tag: 'Universal CSV Ingestion',
    color: '#00d4ff',
    desc: 'Ingest any supermarket CSV dataset with automated header detection, fuzzy column mapping, schema verification, and 1-click built-in demo data generation.',
    bullets: [
      'Auto-detects Sales, Products, Customers, Inventory, and Supplier files',
      'Intelligent fuzzy column mapping matching schema to database',
      'Instant built-in demo data generation with 40,000+ retail rows',
      'Downloadable sample datasets for instant demonstration'
    ],
    previewType: 'datasetup',
  },
  {
    id: 'dashboard',
    title: 'Executive AI Dashboard',
    section: 'Overview',
    icon: '📊',
    tag: 'Store Health Overview',
    color: '#10b981',
    desc: 'Comprehensive real-time command center delivering sales velocity, total revenue, average basket size, transaction velocity, and overall supermarket operational score.',
    bullets: [
      'Live KPI cards with gross revenue, transaction counts, and inventory health',
      'Interactive 60-day daily and monthly revenue trend charts',
      'Instant low-stock alerts and category-level sales rankings',
      'Audit traceability buttons to verify raw source data fields'
    ],
    previewType: 'dashboard',
  },
  {
    id: 'inventory',
    title: 'Smart Inventory & Stock Control',
    section: 'Management',
    icon: '📦',
    tag: 'Stock Level Optimization',
    color: '#f59e0b',
    desc: 'Real-time warehouse and shelf inventory tracking with automated safety stock thresholds, low-stock warnings, 1-click restocking, and perishable shelf-life alerts.',
    bullets: [
      'Real-time stock level progress bars by SKU and category',
      'Automated reorder point warnings before stockout occurs',
      '1-click restocking simulation with warehouse bin locations',
      'Shelf-life expiration monitoring for perishable items'
    ],
    previewType: 'inventory',
  },
  {
    id: 'sales',
    title: 'Sales Insights & Transaction Analytics',
    section: 'Management',
    icon: '🛍️',
    tag: 'Revenue Intelligence',
    color: '#ec4899',
    desc: 'Deep-dive financial analytics across all checkout registers, breakdown by payment method, best-selling product rankings, and category profit margins.',
    bullets: [
      'Breakdown across Credit Card, UPI, Digital Wallets, and Cash',
      'Top revenue-generating products and high-volume movers',
      'Category gross profit margin benchmarking and cost variance',
      'Basket size distribution and peak transaction analysis'
    ],
    previewType: 'sales',
  },
  {
    id: 'customers',
    title: 'Customer Intelligence & RFM Segmentation',
    section: 'Management',
    icon: '👥',
    tag: 'Behavioral Clustering',
    color: '#7c3aed',
    desc: 'Automated RFM (Recency, Frequency, Monetary) clustering segmenting customers into Champions, Loyalists, At-Risk, and Hibernating tiers with lifetime value metrics.',
    bullets: [
      'Automated RFM algorithmic scoring and demographic profiling',
      'Loyalty tier breakdown (Platinum, Gold, Silver, Bronze)',
      'Customer churn risk identification and retention indicators',
      '1-click export of customer demographic datasets to CSV'
    ],
    previewType: 'customers',
  },
  {
    id: 'suppliers',
    title: 'Supplier & Logistics Hub',
    section: 'Management',
    icon: '🚚',
    tag: 'Supply Chain Analytics',
    color: '#3b82f6',
    desc: 'Vendor scorecard tracking supplier delivery lead times, reliability performance indices, active product linkages, and contact logistics.',
    bullets: [
      'Vendor reliability scoring from 0 to 100% based on history',
      'Average replenishment lead time days per supplier',
      'Foreign-key product linkage between catalog and vendors',
      'Direct contact directory for rapid procurement reordering'
    ],
    previewType: 'suppliers',
  },
  {
    id: 'forecast',
    title: 'Machine Learning Demand Forecasting',
    section: 'Intelligence',
    icon: '📈',
    tag: 'Predictive ML Models',
    color: '#00d4ff',
    desc: 'Trained time-series machine learning models predicting 7-day and 30-day product demand curves with 95% confidence intervals and seasonal uplift adjustments.',
    bullets: [
      'Statistical time-series forecasting (ARIMA / Holt-Winters)',
      'Category-level demand projection with upper & lower confidence bands',
      'Seasonal trend analysis to prevent holiday and weekend stockouts',
      'Autonomous retraining triggers upon new CSV data upload'
    ],
    previewType: 'forecast',
  },
  {
    id: 'recommendations',
    title: 'AI Product Recommendations (MBA)',
    section: 'Intelligence',
    icon: '🤖',
    tag: 'Market Basket Analysis',
    color: '#a855f7',
    desc: 'Association rule mining using the Apriori algorithm on customer shopping baskets to discover frequently co-purchased items, cross-selling, and upselling pairings.',
    bullets: [
      'Apriori association rule discovery on 40,000+ transaction baskets',
      'Mathematical Lift, Support, and Confidence scoring per pair',
      'Smart cross-sell suggestions (e.g. Milk ➔ Cereal 94% confidence)',
      'End-cap shelf placement recommendations to maximize basket size'
    ],
    previewType: 'recommendations',
  },
  {
    id: 'pricing',
    title: 'Dynamic AI Pricing Engine',
    section: 'Intelligence',
    icon: '💲',
    tag: 'Price Elasticity Modeling',
    color: '#10b981',
    desc: 'Machine learning price elasticity analysis calculating optimal retail price points to maximize store margin while preserving customer price sensitivity.',
    bullets: [
      'Price elasticity coefficient calculations per category',
      'Algorithmically suggested promotional markdowns (-10%, -15%)',
      'Margin guardrails ensuring retail prices never dip below wholesale cost',
      'Simulation of projected revenue impact before applying price changes'
    ],
    previewType: 'pricing',
  },
  {
    id: 'heatmap',
    title: '24x7 Peak Hours Sales Heatmap',
    section: 'Intelligence',
    icon: '🔥',
    tag: 'Footfall & Peak Traffic',
    color: '#f97316',
    desc: 'Interactive 7-day by 24-hour visual intensity matrix identifying highest footfall hours, checkout register traffic, and optimal staffing schedules.',
    bullets: [
      'Full 168-hour weekly matrix of shopping intensity',
      'Visual glowing color scale identifying peak revenue windows',
      'Optimization insights for cashier and restocking shift schedules',
      'Weekend vs weekday shopping volume comparisons'
    ],
    previewType: 'heatmap',
  },
  {
    id: 'anomalies',
    title: 'Anomaly & Fraud Detection',
    section: 'Intelligence',
    icon: '⚠️',
    tag: 'Isolation Forest ML',
    color: '#ef4444',
    desc: 'Unsupervised Machine Learning Isolation Forest model continuously scanning transactions for price glitches, quantity spikes, and unusual basket totals.',
    bullets: [
      'Scikit-learn Isolation Forest unsupervised outlier detection',
      'High, Medium, and Low risk severity flags per transaction',
      'Detection of cashier scanning errors, quantity spikes, or refund anomalies',
      'Deep transaction inspection with basket item decomposition'
    ],
    previewType: 'anomalies',
  },
  {
    id: 'chatbot',
    title: 'AI Supermarket Copilot',
    section: 'Intelligence',
    icon: '💬',
    tag: 'Conversational Store Assistant',
    color: '#06b6d4',
    desc: 'Natural language conversational AI assistant capable of answering questions about store revenue, low-stock items, top customers, and supplier delays in real time.',
    bullets: [
      'Natural language database query interpretation',
      'Answers questions like "Which items need restocking today?"',
      'Instant financial summaries and profit margin comparisons',
      'Interactive floating assistant accessible across all dashboard pages'
    ],
    previewType: 'chatbot',
  },
];

export default function HomePage({ onNavigate, flags, onRefreshFlags }) {
  const { user, isLoggedIn, logout, updateUserState, oauthNotice } = useAuth();
  const [activeFeatureIndex, setActiveFeatureIndex] = useState(0);
  const [isAutoPlaying, setIsAutoPlaying] = useState(true);
  const [status, setStatus] = useState(null);
  const [loadingDemo, setLoadingDemo] = useState(false);
  const [demoMessage, setDemoMessage] = useState(null);

  // Auth Modal State
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authInitialTab, setAuthInitialTab] = useState('login');

  const activeFeature = FEATURES[activeFeatureIndex];

  // Auto-open AuthModal if redirected from Google OAuth with an alert/action notice
  useEffect(() => {
    if (oauthNotice) {
      setAuthModalOpen(true);
    }
  }, [oauthNotice]);

  // Fetch current live data stats
  const fetchStatus = () => {
    api.getUploadStatus().then(s => setStatus(s)).catch(() => {});
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  // Autoplay carousel timer
  useEffect(() => {
    if (!isAutoPlaying) return;
    const interval = setInterval(() => {
      setActiveFeatureIndex(prev => (prev + 1) % FEATURES.length);
    }, 5000);
    return () => clearInterval(interval);
  }, [isAutoPlaying]);

  const handleNextFeature = () => {
    setActiveFeatureIndex(prev => (prev + 1) % FEATURES.length);
  };

  const handlePrevFeature = () => {
    setActiveFeatureIndex(prev => (prev - 1 + FEATURES.length) % FEATURES.length);
  };

  const handleLoadDemoData = async () => {
    setLoadingDemo(true);
    setDemoMessage(null);
    try {
      const res = await api.loadDemoData();
      setDemoMessage({ type: 'success', text: '✅ Demo data successfully loaded with 40,000+ records! All features are now active.' });
      fetchStatus();
      if (onRefreshFlags) onRefreshFlags();
      if (isLoggedIn && updateUserState) updateUserState({ has_data: true });
    } catch (err) {
      setDemoMessage({ type: 'error', text: 'Failed to load demo data: ' + err.message });
    } finally {
      setLoadingDemo(false);
    }
  };

  const handleFeatureClick = (featId) => {
    if (featId === 'datasetup' || featId === 'home') {
      onNavigate(featId);
      return;
    }
    const dataActive = Boolean(flags?.has_data || status?.feature_flags?.has_data);
    if (!dataActive) {
      onNavigate('datasetup');
    } else {
      onNavigate(featId);
    }
  };

  const openAuth = (tab) => {
    setAuthInitialTab(tab);
    setAuthModalOpen(true);
  };

  const hasData = Boolean(flags?.has_data || status?.feature_flags?.has_data);
  const counts = status?.table_counts || { products: 0, customers: 0, sales: 0, inventory: 0 };

  return (
    <div className="home-container">
      {/* ──────────── TOP-RIGHT HEADER AUTH BAR (Home Page Only) ──────────── */}
      <header className="home-top-header">
        <div className="home-top-left">
          <span className="home-portal-tag">Retail Decision Intelligence Portal</span>
        </div>

        <div className="home-auth-bar">
          {!isLoggedIn ? (
            <div className="auth-btn-group">
              <button
                type="button"
                className="btn-auth-login"
                onClick={() => openAuth('login')}
              >
                <span className="auth-btn-icon">🔐</span>
                <span>Login</span>
              </button>
              <button
                type="button"
                className="btn-auth-register"
                onClick={() => openAuth('register')}
              >
                <span className="auth-btn-icon">✨</span>
                <span>Register</span>
              </button>
            </div>
          ) : (
            <div className="logged-in-profile">
              <div className="user-avatar-chip">
                {user?.avatar_url ? (
                  <img src={user.avatar_url} alt={user.name} className="user-avatar-img" />
                ) : (
                  <div className="user-avatar-fallback">
                    {(user?.name || user?.email || 'U').charAt(0).toUpperCase()}
                  </div>
                )}
                <div className="user-profile-meta">
                  <span className="user-profile-name">{user?.name || 'Account'}</span>
                  <span className="user-profile-email">{user?.email}</span>
                </div>
              </div>
              <button
                type="button"
                className="btn-auth-logout"
                onClick={logout}
                title="Sign out of your account"
              >
                <span>Logout</span>
                <span className="logout-icon">➔</span>
              </button>
            </div>
          )}
        </div>
      </header>

      {/* ──────────── HERO BANNER ──────────── */}
      <section className="home-hero-section">
        <div className="home-hero-badge">
          <span className="hero-pulse-dot" />
          <span>SmartMart AI Intelligence v3 — Autonomous Retail Engine</span>
        </div>

        <h1 className="home-hero-title">
          Intelligent Supermarket Operations, <br />
          <span className="gradient-highlight">Driven by Machine Learning</span>
        </h1>


        {/* Action CTAs */}
        <div className="home-hero-actions">
          <button
            type="button"
            className="hero-btn primary"
            onClick={handleLoadDemoData}
            disabled={loadingDemo}
          >
            {loadingDemo ? (
              <>
                <span className="btn-spinner" />
                <span>Generating Demo Dataset...</span>
              </>
            ) : (
              <>
                <span>🚀</span>
                <span>{hasData ? 'Reload Demo Dataset' : 'Generate Demo Data'}</span>
              </>
            )}
          </button>

          <button
            type="button"
            className="hero-btn secondary"
            onClick={() => onNavigate('datasetup')}
          >
            <span>📁</span>
            <span>Upload Your CSV</span>
          </button>

          <button
            type="button"
            className="hero-btn outline"
            onClick={() => onNavigate(hasData ? 'dashboard' : 'datasetup')}
          >
            <span>📊</span>
            <span>Open Executive Dashboard</span>
          </button>
        </div>

        {demoMessage && (
          <div className={`home-demo-alert ${demoMessage.type}`}>
            {demoMessage.text}
          </div>
        )}

        {/* Live Data Status Strip */}
        <div className="home-data-status-card">
          <div className="status-header">
            <span className="status-label">CURRENT DATA STATUS</span>
            <span className={`status-pill ${hasData ? 'active' : 'empty'}`}>
              {hasData ? '● Live Data Active' : '○ Clean State — No Data Loaded'}
            </span>
          </div>

          <div className="status-metrics-row">
            <div className="status-metric">
              <span className="metric-val">{counts.products || 0}</span>
              <span className="metric-lbl">Products</span>
            </div>
            <div className="status-metric">
              <span className="metric-val">{counts.customers || 0}</span>
              <span className="metric-lbl">Customers</span>
            </div>
            <div className="status-metric">
              <span className="metric-val">{counts.sales || 0}</span>
              <span className="metric-lbl">Sales Records</span>
            </div>
            <div className="status-metric">
              <span className="metric-val">{counts.inventory || 0}</span>
              <span className="metric-lbl">Inventory SKUs</span>
            </div>
          </div>

        </div>
      </section>

      {/* ──────────── INTERACTIVE FEATURE SHOWCASE (Box by box below dots [. . . . . . . . .]) ──────────── */}
      <section className="home-showcase-section">
        <div className="showcase-header">
          <div className="showcase-badge">FEATURE SPOTLIGHT & DEEP-DIVE</div>
          <h2>Explore Every Capability Box by Box</h2>
          <p>
            Browse all 12 platform features below. Click any dot in the navigation bar to jump directly
            to that feature.
          </p>
        </div>

        {/* The Feature Box */}
        <div
          className="feature-spotlight-box"
          onMouseEnter={() => setIsAutoPlaying(false)}
          onMouseLeave={() => setIsAutoPlaying(true)}
          style={{ borderColor: `${activeFeature.color}40` }}
        >
          {/* Arrow Navigation */}
          <button
            type="button"
            className="carousel-arrow prev"
            onClick={handlePrevFeature}
            aria-label="Previous feature"
          >
            ‹
          </button>
          <button
            type="button"
            className="carousel-arrow next"
            onClick={handleNextFeature}
            aria-label="Next feature"
          >
            ›
          </button>

          <div className="spotlight-content-grid">
            {/* Left: Feature Details */}
            <div className="spotlight-info">
              <div className="spotlight-meta-tags">
                <span className="spotlight-section-pill" style={{ background: `${activeFeature.color}20`, color: activeFeature.color }}>
                  {activeFeature.section}
                </span>
                <span className="spotlight-counter">
                  Feature {String(activeFeatureIndex + 1).padStart(2, '0')} / {String(FEATURES.length).padStart(2, '0')}
                </span>
              </div>

              <div className="spotlight-title-group">
                <span className="spotlight-icon">{activeFeature.icon}</span>
                <div>
                  <h3>{activeFeature.title}</h3>
                  <span className="spotlight-tag">{activeFeature.tag}</span>
                </div>
              </div>

              <p className="spotlight-desc">{activeFeature.desc}</p>

              <ul className="spotlight-bullets">
                {activeFeature.bullets.map((b, idx) => (
                  <li key={idx}>
                    <span className="bullet-check" style={{ color: activeFeature.color }}>✓</span>
                    <span>{b}</span>
                  </li>
                ))}
              </ul>

              <div className="spotlight-actions">
                <button
                  type="button"
                  className="spotlight-launch-btn"
                  style={{ background: `linear-gradient(135deg, ${activeFeature.color}, #7c3aed)` }}
                  onClick={() => handleFeatureClick(activeFeature.id)}
                >
                  <span>Launch {activeFeature.title}</span>
                  <span className="launch-arrow">➔</span>
                </button>
                <span className="spotlight-status-tag">
                  {hasData ? '🟢 Active & Ready' : '🔒 Requires Demo Data'}
                </span>
              </div>
            </div>

            {/* Right: Rich Graphical Mockup Widget */}
            <div className="spotlight-graphic-preview">
              <FeatureGraphicPreview type={activeFeature.previewType} color={activeFeature.color} hasData={hasData} counts={counts} />
            </div>
          </div>
        </div>

        {/* ──────────── THE INTERACTIVE DOTS [. . . . . . . . .] ──────────── */}
        <div className="showcase-dots-bar">
          <div className="dots-bracket-wrapper">
            <span className="dots-bracket">[</span>
            <div className="dots-container">
              {FEATURES.map((feat, idx) => {
                const isActive = idx === activeFeatureIndex;
                return (
                  <button
                    key={feat.id}
                    type="button"
                    className={`showcase-dot ${isActive ? 'active' : ''}`}
                    onClick={() => setActiveFeatureIndex(idx)}
                    title={`${feat.icon} ${feat.title}`}
                    style={isActive ? { background: feat.color, boxShadow: `0 0 12px ${feat.color}` } : {}}
                    aria-label={`Jump to ${feat.title}`}
                  >
                    {isActive && <span className="active-dot-icon">{feat.icon}</span>}
                  </button>
                );
              })}
            </div>
            <span className="dots-bracket">]</span>
          </div>

          <div className="dots-caption">
            <span>Viewing: </span>
            <strong style={{ color: activeFeature.color }}>
              {activeFeature.icon} {activeFeature.title}
            </strong>
            <span className="dots-subtext"> (Click any dot above or use arrows to switch)</span>
          </div>
        </div>
      </section>

      {/* ──────────── COMPLETE 12-FEATURE VISUAL GRID (Do each feature) ──────────── */}
      <section className="home-grid-section">
        <div className="section-title-wrap">
          <span className="section-eyebrow">ALL-IN-ONE RETAIL ECOSYSTEM</span>
          <h2>All 12 Platform Features at a Glance</h2>
          <p>Every feature is fully integrated with shared state, AI pipelines, and instant interactivity.</p>
        </div>

        <div className="features-grid">
          {FEATURES.map((feat, idx) => (
            <div
              key={feat.id}
              className={`feature-card ${activeFeatureIndex === idx ? 'highlighted' : ''}`}
              onClick={() => handleFeatureClick(feat.id)}
            >
              <div className="feature-card-header">
                <span className="card-icon">{feat.icon}</span>
                <span className="card-section-tag">{feat.section}</span>
              </div>

              <h4>{feat.title}</h4>
              <p className="card-desc">{feat.desc}</p>

              <div className="card-footer">
                <span className="card-tag" style={{ color: feat.color }}>{feat.tag}</span>
                <span className="card-open-link">
                  Open ➔
                </span>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ──────────── ARCHITECTURE / HOW IT WORKS ──────────── */}
      <section className="home-workflow-section">
        <div className="section-title-wrap">
          <span className="section-eyebrow">SEAMLESS INTEGRATION PIPELINE</span>
          <h2>How SmartMart AI Operates</h2>
        </div>

        <div className="workflow-steps">
          <div className="workflow-step">
            <div className="step-num">01</div>
            <div className="step-icon">📁</div>
            <h3>Ingest or Load Data</h3>
            <p>Upload your own CSV files or generate the comprehensive 40,000-row demo retail dataset with 1 click.</p>
          </div>

          <div className="workflow-connector">➔</div>

          <div className="workflow-step">
            <div className="step-num">02</div>
            <div className="step-icon">🤖</div>
            <h3>Automated ML Modeling</h3>
            <p>Background algorithms compute demand time-series, Apriori basket rules, RFM segments, and Isolation Forest outliers.</p>
          </div>

          <div className="workflow-connector">➔</div>

          <div className="workflow-step">
            <div className="step-num">03</div>
            <div className="step-icon">🚀</div>
            <h3>Autonomous Decisions</h3>
            <p>Apply dynamic pricing adjustments, restock low inventory before runouts, and target at-risk customer tiers.</p>
          </div>
        </div>
      </section>

      {/* Auth Modal */}
      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        initialTab={authInitialTab}
        onSuccess={() => {
          fetchStatus();
          if (onRefreshFlags) onRefreshFlags();
        }}
      />
    </div>
  );
}

/**
 * Visually rich graphical mockup widgets for each feature preview box.
 * When hasData is false, displays clean blueprint placeholders so visitors don't mistake it for live loaded demo data.
 */
function FeatureGraphicPreview({ type, color, hasData = false, counts = {} }) {
  switch (type) {
    case 'datasetup':
      return (
        <div className="graphic-card-mockup">
          <div className="mockup-header">
            <span className="mockup-title">CSV Schema Auto-Detector</span>
            <span className={`mockup-badge ${hasData ? 'green' : 'gray'}`}>
              {hasData ? 'Auto-Mapped' : 'Blueprint'}
            </span>
          </div>
          <div className="schema-chips-list">
            <div className={`schema-chip ${hasData ? 'valid' : 'pending'}`}>
              <span>{hasData ? '✓' : '○'} sales.csv</span>
              <small>{hasData ? `${counts?.sales?.toLocaleString() || 40148} rows` : 'Ready for ingestion'}</small>
            </div>
            <div className={`schema-chip ${hasData ? 'valid' : 'pending'}`}>
              <span>{hasData ? '✓' : '○'} products.csv</span>
              <small>{hasData ? `${counts?.products?.toLocaleString() || 224} SKUs` : 'Ready for ingestion'}</small>
            </div>
            <div className={`schema-chip ${hasData ? 'valid' : 'pending'}`}>
              <span>{hasData ? '✓' : '○'} customers.csv</span>
              <small>{hasData ? `${counts?.customers?.toLocaleString() || 2000} profiles` : 'Ready for ingestion'}</small>
            </div>
            <div className={`schema-chip ${hasData ? 'valid' : 'pending'}`}>
              <span>{hasData ? '✓' : '○'} inventory.csv</span>
              <small>{hasData ? `${counts?.inventory?.toLocaleString() || 224} rows` : 'Ready for ingestion'}</small>
            </div>
            <div className={`schema-chip ${hasData ? 'valid' : 'pending'}`}>
              <span>{hasData ? '✓' : '○'} suppliers.csv</span>
              <small>{hasData ? `${counts?.suppliers?.toLocaleString() || 20} vendors` : 'Ready for ingestion'}</small>
            </div>
          </div>
          <div className="mockup-progress-bar">
            <div className="progress-fill" style={{ width: hasData ? '100%' : '15%', background: color }} />
          </div>
          <div className="mockup-note">
            {hasData ? 'Schema validated with 100% column precision' : 'Awaiting data: Click "Generate Demo Data" or "Upload Your CSV"'}
          </div>
        </div>
      );

    case 'dashboard':
      return (
        <div className="graphic-card-mockup">
          <div className="mockup-header">
            <span className="mockup-title">Executive Sales Velocity</span>
            <span className={`mockup-badge ${hasData ? 'blue' : 'gray'}`}>
              {hasData ? 'Real-Time' : 'Blueprint'}
            </span>
          </div>
          <div className="mini-kpi-grid">
            <div className="mini-kpi">
              <span className="mini-kpi-val">{hasData ? '₹1,248,390' : '₹ --'}</span>
              <span className="mini-kpi-lbl">Total Gross Revenue</span>
            </div>
            <div className="mini-kpi">
              <span className="mini-kpi-val">{hasData ? (counts?.sales?.toLocaleString() || '40,148') : '--'}</span>
              <span className="mini-kpi-lbl">Total Transactions</span>
            </div>
            <div className="mini-kpi">
              <span className="mini-kpi-val">{hasData ? '₹31.09' : '--'}</span>
              <span className="mini-kpi-lbl">Avg Basket Value</span>
            </div>
            <div className="mini-kpi">
              <span className="mini-kpi-val">{hasData ? '99.4%' : 'Standby'}</span>
              <span className="mini-kpi-lbl">System Health</span>
            </div>
          </div>
          <div className="mini-sparkline" style={{ opacity: hasData ? 1 : 0.35 }}>
            <div className="spark-bar" style={{ height: '40%' }} />
            <div className="spark-bar" style={{ height: '65%' }} />
            <div className="spark-bar" style={{ height: '50%' }} />
            <div className="spark-bar" style={{ height: '85%' }} />
            <div className="spark-bar" style={{ height: '70%' }} />
            <div className="spark-bar active" style={{ height: '100%', background: color }} />
          </div>
          {!hasData && (
            <div className="mockup-note" style={{ textAlign: 'center', marginTop: 10 }}>
              Live KPI calculations activate upon data load or demo generation
            </div>
          )}
        </div>
      );

    case 'inventory':
      return (
        <div className="graphic-card-mockup">
          <div className="mockup-header">
            <span className="mockup-title">Warehouse Safety Thresholds</span>
            <span className={`mockup-badge ${hasData ? 'orange' : 'gray'}`}>
              {hasData ? 'Stock Monitor' : 'Blueprint'}
            </span>
          </div>
          <div className="inventory-bars-list" style={{ opacity: hasData ? 1 : 0.45 }}>
            <div className="inv-item">
              <div className="inv-meta">
                <span>{hasData ? 'Organic Bananas' : 'SKU Slot A'}</span>
                <small className={hasData ? 'text-green' : ''}>{hasData ? 'In Stock (142)' : 'Threshold Ready'}</small>
              </div>
              <div className="inv-bar"><div className="inv-fill green" style={{ width: hasData ? '85%' : '0%' }} /></div>
            </div>
            <div className="inv-item">
              <div className="inv-meta">
                <span>{hasData ? 'Whole Milk 1L' : 'SKU Slot B'}</span>
                <small className={hasData ? 'text-orange' : ''}>{hasData ? 'Reorder Soon (28)' : 'Reorder Trigger Ready'}</small>
              </div>
              <div className="inv-bar"><div className="inv-fill orange" style={{ width: hasData ? '32%' : '0%' }} /></div>
            </div>
            <div className="inv-item">
              <div className="inv-meta">
                <span>{hasData ? 'Fresh Sourdough' : 'SKU Slot C'}</span>
                <small className={hasData ? 'text-red' : ''}>{hasData ? 'Critical Stock (8)' : 'Safety Point Ready'}</small>
              </div>
              <div className="inv-bar"><div className="inv-fill red" style={{ width: hasData ? '12%' : '0%' }} /></div>
            </div>
          </div>
          <div className="mockup-reorder-btn">
            {hasData ? '⚡ Automated Safety Stock Trigger Active' : '⚡ Safety Stock Engine Ready for Ingestion'}
          </div>
        </div>
      );

    case 'sales':
      return (
        <div className="graphic-card-mockup">
          <div className="mockup-header">
            <span className="mockup-title">Payment Mode Distribution</span>
            <span className={`mockup-badge ${hasData ? 'pink' : 'gray'}`}>
              {hasData ? 'Financial' : 'Blueprint'}
            </span>
          </div>
          <div className="payment-pills-list">
            <div className="pay-row"><span>Credit / Debit Card</span> <strong>{hasData ? '52.4%' : '--'}</strong></div>
            <div className="pay-row"><span>UPI / Instant Pay</span> <strong>{hasData ? '28.1%' : '--'}</strong></div>
            <div className="pay-row"><span>Digital Wallets</span> <strong>{hasData ? '12.5%' : '--'}</strong></div>
            <div className="pay-row"><span>Cash at Counter</span> <strong>{hasData ? '7.0%' : '--'}</strong></div>
          </div>
          <div className="profit-margin-badge">
            {hasData ? <>Gross Margin: <strong>34.8% Average</strong></> : 'Financial breakdowns calculate upon data load'}
          </div>
        </div>
      );

    case 'customers':
      return (
        <div className="graphic-card-mockup">
          <div className="mockup-header">
            <span className="mockup-title">RFM Algorithmic Clusters</span>
            <span className={`mockup-badge ${hasData ? 'purple' : 'gray'}`}>
              {hasData ? '2,000 Profiles' : 'Blueprint'}
            </span>
          </div>
          <div className="rfm-clusters-grid" style={{ opacity: hasData ? 1 : 0.65 }}>
            <div className="rfm-card gold">
              <span className="rfm-emoji">🏆</span>
              <strong>Champions</strong>
              <small>{hasData ? 'Top 18% spenders' : 'Auto-segmentation'}</small>
            </div>
            <div className="rfm-card blue">
              <span className="rfm-emoji">⭐</span>
              <strong>Loyalists</strong>
              <small>{hasData ? 'High frequency' : 'Auto-segmentation'}</small>
            </div>
            <div className="rfm-card orange">
              <span className="rfm-emoji">⚠️</span>
              <strong>At-Risk</strong>
              <small>{hasData ? 'Dormant 45+ days' : 'Churn risk modeling'}</small>
            </div>
            <div className="rfm-card gray">
              <span className="rfm-emoji">💤</span>
              <strong>Hibernating</strong>
              <small>{hasData ? 'Re-engage promo' : 'Re-engagement triggers'}</small>
            </div>
          </div>
        </div>
      );

    case 'suppliers':
      return (
        <div className="graphic-card-mockup">
          <div className="mockup-header">
            <span className="mockup-title">Vendor Scorecard Matrix</span>
            <span className={`mockup-badge ${hasData ? 'blue' : 'gray'}`}>
              {hasData ? 'Logistics' : 'Blueprint'}
            </span>
          </div>
          <div className="vendor-row" style={{ opacity: hasData ? 1 : 0.5 }}>
            <div className="vendor-info">
              <strong>{hasData ? 'FarmFresh Organic Co.' : 'Vendor Partner 1'}</strong>
              <small>{hasData ? 'Lead Time: 2 days • 48 SKUs' : 'Replenishment lead times'}</small>
            </div>
            <div className="vendor-score green">{hasData ? '98.5%' : '--'}</div>
          </div>
          <div className="vendor-row" style={{ opacity: hasData ? 1 : 0.5 }}>
            <div className="vendor-info">
              <strong>{hasData ? 'Metro Bakery Distribution' : 'Vendor Partner 2'}</strong>
              <small>{hasData ? 'Lead Time: 1 day • 16 SKUs' : 'Replenishment lead times'}</small>
            </div>
            <div className="vendor-score green">{hasData ? '96.2%' : '--'}</div>
          </div>
          <div className="vendor-row" style={{ opacity: hasData ? 1 : 0.5 }}>
            <div className="vendor-info">
              <strong>{hasData ? 'Global Beverages Ltd.' : 'Vendor Partner 3'}</strong>
              <small>{hasData ? 'Lead Time: 4 days • 35 SKUs' : 'Replenishment lead times'}</small>
            </div>
            <div className="vendor-score orange">{hasData ? '91.0%' : '--'}</div>
          </div>
        </div>
      );

    case 'forecast':
      return (
        <div className="graphic-card-mockup">
          <div className="mockup-header">
            <span className="mockup-title">7-Day Predictive ML Curve</span>
            <span className={`mockup-badge ${hasData ? 'cyan' : 'gray'}`}>
              {hasData ? '95% Confidence' : 'Predictive ML Model'}
            </span>
          </div>
          <div className="forecast-curve-visual" style={{ opacity: hasData ? 1 : 0.4 }}>
            <svg viewBox="0 0 300 120" className="forecast-svg">
              <defs>
                <linearGradient id="curveGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#00d4ff" stopOpacity="0.4" />
                  <stop offset="100%" stopColor="#00d4ff" stopOpacity="0" />
                </linearGradient>
              </defs>
              <path d="M 10 90 Q 75 40 150 60 T 290 20 L 290 55 Q 225 85 150 85 T 10 110 Z" fill="#00d4ff" opacity="0.15" />
              <path d="M 10 100 Q 75 50 150 70 T 290 35" fill="none" stroke="#00d4ff" strokeWidth="3" />
              <circle cx="290" cy="35" r="5" fill="#00d4ff" />
            </svg>
          </div>
          <div className="forecast-stat-row">
            <span>
              {hasData ? <>Expected Uplift: <strong>+18.4% this weekend</strong></> : 'Time-series ARIMA/Holt-Winters models train upon data load'}
            </span>
          </div>
        </div>
      );

    case 'recommendations':
      return (
        <div className="graphic-card-mockup">
          <div className="mockup-header">
            <span className="mockup-title">Apriori Market Basket Pair</span>
            <span className={`mockup-badge ${hasData ? 'purple' : 'gray'}`}>
              {hasData ? 'Association Lift 3.8x' : 'Apriori Algorithm'}
            </span>
          </div>
          <div className="paired-items-visual" style={{ opacity: hasData ? 1 : 0.5 }}>
            <div className="paired-box">
              <span className="paired-icon">🍌</span>
              <span>{hasData ? 'Organic Bananas' : 'Item Antecedent'}</span>
            </div>
            <div className="paired-arrow">➔ {hasData ? '94%' : '--'}</div>
            <div className="paired-box">
              <span className="paired-icon">🥣</span>
              <span>{hasData ? 'Greek Yogurt' : 'Item Consequent'}</span>
            </div>
          </div>
          <div className="recommendation-pill">
            {hasData ? 'Recommendation: Place Yogurt display adjacent to Fresh Fruit aisle.' : 'Association rules and cross-sell affinities compute upon ingestion.'}
          </div>
        </div>
      );

    case 'pricing':
      return (
        <div className="graphic-card-mockup">
          <div className="mockup-header">
            <span className="mockup-title">Price Elasticity Simulation</span>
            <span className={`mockup-badge ${hasData ? 'green' : 'gray'}`}>
              {hasData ? 'Optimal Margin' : 'Dynamic Elasticity'}
            </span>
          </div>
          <div className="pricing-calc-box">
            <div className="calc-row">
              <span>Current Price:</span> <strong>{hasData ? '$4.99' : '--'}</strong>
            </div>
            <div className="calc-row">
              <span>Optimized Point:</span> <strong className="text-green">{hasData ? '$4.49 (-10%)' : 'Awaiting Data'}</strong>
            </div>
            <div className="calc-row">
              <span>Projected Volume:</span> <strong>{hasData ? '+28% unit sales' : '--'}</strong>
            </div>
            <div className="calc-row">
              <span>Net Gross Margin:</span> <strong className="text-green">{hasData ? '+$1,420 / week' : '--'}</strong>
            </div>
          </div>
        </div>
      );

    case 'heatmap':
      return (
        <div className="graphic-card-mockup">
          <div className="mockup-header">
            <span className="mockup-title">24x7 Peak Register Traffic</span>
            <span className={`mockup-badge ${hasData ? 'orange' : 'gray'}`}>
              {hasData ? 'Peak: Fri 6 PM' : 'Traffic Matrix'}
            </span>
          </div>
          <div className="mini-heatmap-grid" style={{ opacity: hasData ? 1 : 0.3 }}>
            {Array.from({ length: 28 }).map((_, i) => {
              const intensity = (i * 17) % 100;
              const alpha = hasData ? Math.max(0.1, intensity / 100) : 0.15;
              return (
                <div
                  key={i}
                  className="heat-cell"
                  style={{ background: `rgba(249, 115, 22, ${alpha})` }}
                  title={hasData ? `Hour ${i % 24}: Traffic index ${intensity}` : 'Awaiting data'}
                />
              );
            })}
          </div>
          <div className="heatmap-legend">
            <span>Quiet (Morning)</span>
            <span className="legend-gradient" />
            <span>Rush Hour (Evening)</span>
          </div>
        </div>
      );

    case 'anomalies':
      return (
        <div className="graphic-card-mockup">
          <div className="mockup-header">
            <span className="mockup-title">Isolation Forest ML Detection</span>
            <span className={`mockup-badge ${hasData ? 'red' : 'gray'}`}>
              {hasData ? 'Alert Triggered' : 'Isolation Forest'}
            </span>
          </div>
          <div className="anomaly-alert-card" style={{ opacity: hasData ? 1 : 0.6 }}>
            <div className={`anomaly-badge ${hasData ? 'high' : 'gray'}`}>{hasData ? 'HIGH RISK OUTLIER' : 'SCANNER STANDBY'}</div>
            <div className="anomaly-detail">
              <span>{hasData ? <>Basket #48291 • Total: <strong>$849.50</strong></> : 'Unsupervised Outlier Detection'}</span>
              <small>{hasData ? 'Quantity: 45 units of single SKU (4.8 standard deviations above norm)' : 'Scans transactions for spikes, bulk sweeps, and anomalies upon data load'}</small>
            </div>
          </div>
          <div className="anomaly-stat">{hasData ? 'Status: Flagged for cashier terminal verification' : 'Status: Ready to analyze checkout registers'}</div>
        </div>
      );

    case 'chatbot':
    default:
      return (
        <div className="graphic-card-mockup">
          <div className="mockup-header">
            <span className="mockup-title">Interactive Store Copilot</span>
            <span className={`mockup-badge ${hasData ? 'cyan' : 'gray'}`}>
              {hasData ? 'AI Assistant' : 'Standby'}
            </span>
          </div>
          <div className="chat-bubbles-preview">
            <div className="chat-bubble user">
              "Which dairy items have low stock today?"
            </div>
            <div className="chat-bubble bot">
              {hasData
                ? "Whole Milk 1L (28 units left) and Cheddar Cheese (12 units) are below safety thresholds. Supplier FarmFresh has a 2-day lead time."
                : "SmartBot is ready! Ask questions about inventory, revenue, or customer trends once store data is loaded."}
            </div>
          </div>
          <div className="chat-input-mock">Ask Copilot anything about your store...</div>
        </div>
      );
  }
}
