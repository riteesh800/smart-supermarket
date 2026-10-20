import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import SourceButton from './SourceButton';
import { SOURCES } from '../constants/sources';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, AreaChart, Area
} from 'recharts';

export default function DashboardOverview() {
  const [summary, setSummary] = useState(null);
  const [revenue, setRevenue] = useState(null);
  const [lowStock, setLowStock] = useState([]);
  const [bestSellers, setBestSellers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.allSettled([
      api.getDashboardSummary(),
      api.getRevenue(),
      api.getLowStock(),
      api.getBestSellers()
    ]).then(([sum, rev, low, best]) => {
      if (sum.status === 'fulfilled') setSummary(sum.value);
      if (rev.status === 'fulfilled') setRevenue(rev.value);
      if (low.status === 'fulfilled') setLowStock(low.value);
      if (best.status === 'fulfilled') setBestSellers(best.value);
      setLoading(false);
    });
  }, []);

  if (loading) return <div className="loading">Loading dashboard...</div>;

  const monthlyData = (revenue?.monthly || []).map(d => ({
    month: d.month,
    revenue: Math.round(d.revenue)
  }));

  // Daily sparkline (last 60 days)
  const dailyData = (revenue?.daily || []).slice(-60).map(d => ({
    date: d.date?.slice(5),
    revenue: Math.round(d.revenue)
  }));

  return (
    <div>
      <div className="page-header">
        <h2>📊 Dashboard Overview</h2>
        <p>Real-time supermarket intelligence — {summary?.total_categories} categories, {summary?.total_products} products</p>
      </div>

      {/* KPI Cards */}
      <div className="kpi-grid">
        <div className="kpi-card green">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
            <SourceButton sources={SOURCES.dashboard.kpiTotalRevenue} />
            <div className="kpi-icon" style={{ marginBottom: 0 }}>💰</div>
          </div>
          <div className="kpi-label">Total Revenue</div>
          <div className="kpi-value">₹{summary?.total_revenue?.toLocaleString(undefined, { maximumFractionDigits: 0 })}</div>
          <div className="kpi-sub">All time</div>
        </div>
        <div className="kpi-card blue">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
            <SourceButton sources={SOURCES.dashboard.kpiTotalProfit} />
            <div className="kpi-icon" style={{ marginBottom: 0 }}>📈</div>
          </div>
          <div className="kpi-label">Total Profit</div>
          <div className="kpi-value">₹{summary?.total_profit?.toLocaleString(undefined, { maximumFractionDigits: 0 })}</div>
          <div className="kpi-sub">{summary?.profit_margin}% margin</div>
        </div>
        <div className="kpi-card purple">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
            <SourceButton sources={SOURCES.dashboard.kpiCustomers} />
            <div className="kpi-icon" style={{ marginBottom: 0 }}>👥</div>
          </div>
          <div className="kpi-label">Customers</div>
          <div className="kpi-value">{summary?.total_customers?.toLocaleString()}</div>
          <div className="kpi-sub">Registered</div>
        </div>
        <div className="kpi-card orange">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
            <SourceButton sources={SOURCES.dashboard.kpiTransactions} />
            <div className="kpi-icon" style={{ marginBottom: 0 }}>🧾</div>
          </div>
          <div className="kpi-label">Transactions</div>
          <div className="kpi-value">{summary?.total_transactions?.toLocaleString()}</div>
          <div className="kpi-sub">{summary?.total_baskets?.toLocaleString()} baskets{summary?.avg_basket_value ? ` • avg ₹${Math.round(summary.avg_basket_value)}` : ''}</div>
        </div>
        <div className="kpi-card red">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
            <SourceButton sources={SOURCES.dashboard.kpiLowStock} />
            <div className="kpi-icon" style={{ marginBottom: 0 }}>🚨</div>
          </div>
          <div className="kpi-label">Low Stock Alerts</div>
          <div className="kpi-value">{summary?.low_stock_alerts}</div>
          <div className="kpi-sub">Need attention</div>
        </div>
        <div className="kpi-card pink">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
            <SourceButton sources={SOURCES.dashboard.kpiTopCategory} />
            <div className="kpi-icon" style={{ marginBottom: 0 }}>🏆</div>
          </div>
          <div className="kpi-label">Top Category</div>
          <div className="kpi-value" style={{ fontSize: 18 }}>{summary?.top_category}</div>
          <div className="kpi-sub">₹{summary?.top_category_revenue?.toLocaleString(undefined, { maximumFractionDigits: 0 })}</div>
        </div>
      </div>

      {/* Daily Revenue Sparkline */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-header-with-source">
          <SourceButton sources={SOURCES.dashboard.dailyRevenueTrend} />
          <div className="card-title">Daily Revenue Trend (Last 60 Days)</div>
        </div>
        <div className="chart-container">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={dailyData}>
              <defs>
                <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#00d4ff" stopOpacity={0.3} />
                  <stop offset="100%" stopColor="#00d4ff" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="date" tick={{ fill: '#9898b8', fontSize: 10 }} interval="preserveStartEnd" />
              <YAxis tick={{ fill: '#9898b8', fontSize: 11 }} />
              <Tooltip
                contentStyle={{ background: '#1a1a2e', border: '1px solid rgba(100,100,255,0.2)', borderRadius: 10, color: '#e8e8f0' }}
                formatter={(val) => [`₹${val.toLocaleString()}`, 'Revenue']}
              />
              <Area type="monotone" dataKey="revenue" stroke="#00d4ff" strokeWidth={2} fill="url(#areaGrad)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid-2">
        {/* Monthly Revenue Chart */}
        <div className="card">
          <div className="card-header-with-source">
            <SourceButton sources={SOURCES.dashboard.monthlyRevenue} />
            <div className="card-title">Monthly Revenue</div>
          </div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={monthlyData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="month" tick={{ fill: '#9898b8', fontSize: 11 }} />
                <YAxis tick={{ fill: '#9898b8', fontSize: 11 }} />
                <Tooltip
                  cursor={false}
                  contentStyle={{ background: '#1a1a2e', border: '1px solid rgba(100,100,255,0.2)', borderRadius: 10, color: '#e8e8f0' }}
                  formatter={(val) => [`₹${val.toLocaleString()}`, 'Revenue']}
                />
                <Bar dataKey="revenue" fill="url(#blueGrad)" radius={[6, 6, 0, 0]} />
                <defs>
                  <linearGradient id="blueGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#00d4ff" />
                    <stop offset="100%" stopColor="#0084ff" />
                  </linearGradient>
                </defs>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Top Products */}
        <div className="card">
          <div className="card-header-with-source">
            <SourceButton sources={SOURCES.dashboard.topProducts} />
            <div className="card-title">🏆 Top 10 Products</div>
          </div>
          <div className="table-wrapper" style={{ maxHeight: 300 }}>
            <table>
              <thead><tr><th>#</th><th>Product</th><th>Revenue</th></tr></thead>
              <tbody>
                {bestSellers.slice(0, 10).map((p, i) => (
                  <tr key={p.product_id}>
                    <td style={{ color: 'var(--text-muted)' }}>{i + 1}</td>
                    <td style={{ fontWeight: 600 }}>{p.name}</td>
                    <td style={{ color: 'var(--accent-green)', fontWeight: 600 }}>₹{Math.round(p.total_revenue || 0).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Low Stock Alerts */}
      {lowStock.length > 0 && (
        <div className="card">
          <div className="card-header-with-source">
            <SourceButton sources={SOURCES.dashboard.lowStockAlerts} />
            <div className="card-title">⚠️ Low Stock Alerts ({lowStock.length})</div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 12 }}>
            {lowStock.slice(0, 12).map(item => (
              <div key={item.product_id} className="alert-row">
                <div className="alert-icon">🔴</div>
                <div className="alert-info">
                  <div className="alert-name">{item.name}</div>
                  <div className="alert-detail">Stock: {item.current_stock} / Reorder: {item.reorder_point}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
