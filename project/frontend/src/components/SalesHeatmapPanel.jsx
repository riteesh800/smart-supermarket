import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { CHART_COLORS, getChartColor } from '../constants/colors';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell
} from 'recharts';
const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

function getHeatColor(value, max) {
  if (max === 0) return 'rgba(255,255,255,0.03)';
  const intensity = value / max;
  if (intensity > 0.8) return '#10b981';
  if (intensity > 0.6) return '#34d399';
  if (intensity > 0.4) return '#00d4ff';
  if (intensity > 0.2) return '#6366f1';
  if (intensity > 0.05) return '#7c3aed44';
  return 'rgba(255,255,255,0.03)';
}

export default function SalesHeatmapPanel() {
  const [heatmap, setHeatmap] = useState([]);
  const [payments, setPayments] = useState([]);
  const [margins, setMargins] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.allSettled([
      api.getHourlyHeatmap(),
      api.getPaymentBreakdown(),
      api.getProfitMargins()
    ]).then(([h, p, m]) => {
      if (h.status === 'fulfilled') setHeatmap(h.value);
      if (p.status === 'fulfilled') setPayments(p.value);
      if (m.status === 'fulfilled') setMargins(m.value);
      setLoading(false);
    });
  }, []);

  if (loading) return <div className="loading">Loading analytics data...</div>;

  // Build heatmap grid: hours dynamically based on data, defaulting to 8-21
  const allHours = heatmap.length ? [...new Set(heatmap.map(h => h.hour))].sort((a, b) => a - b) : [];
  const minHour = allHours.length ? Math.min(8, allHours[0]) : 8;
  const maxHour = allHours.length ? Math.max(21, allHours[allHours.length - 1]) : 21;
  const hours = Array.from({ length: maxHour - minHour + 1 }, (_, i) => i + minHour);
  const heatGrid = {};
  let maxCount = 0;
  heatmap.forEach(h => {
    const key = `${h.day_of_week}-${h.hour}`;
    heatGrid[key] = h.sales_count;
    if (h.sales_count > maxCount) maxCount = h.sales_count;
  });

  const totalProfit = margins.reduce((s, m) => s + (m.total_profit || 0), 0);
  const totalRevenue = margins.reduce((s, m) => s + (m.total_revenue || 0), 0);
  const overallMargin = totalRevenue > 0 ? (totalProfit / totalRevenue * 100).toFixed(1) : '0.0';

  // Compute real peak hours from heatmap data
  const hourlySales = {};
  heatmap.forEach(h => {
    hourlySales[h.hour] = (hourlySales[h.hour] || 0) + h.sales_count;
  });
  let peakLabel = 'N/A';
  const hourEntries = Object.entries(hourlySales);
  if (hourEntries.length > 0) {
    hourEntries.sort((a, b) => b[1] - a[1]);
    const peakHour = parseInt(hourEntries[0][0]);
    const startH = Math.max(peakHour - 1, 0);
    const endH = Math.min(peakHour + 1, 23);
    const fmtH = (h) => h === 0 ? '12am' : h === 12 ? '12pm' : h < 12 ? `${h}am` : `${h - 12}pm`;
    peakLabel = `${fmtH(startH)}-${fmtH(endH)}`;
  }

  return (
    <div>
      <div className="page-header">
        <h2>🔥 Sales Heatmap & Analytics</h2>
        <p>Hourly patterns, payment methods, and profit margin analysis</p>
      </div>

      <div className="kpi-grid">
        <div className="kpi-card green">
          <div className="kpi-icon">💰</div>
          <div className="kpi-label">Total Profit</div>
          <div className="kpi-value">₹{Math.round(totalProfit).toLocaleString()}</div>
        </div>
        <div className="kpi-card blue">
          <div className="kpi-icon">📊</div>
          <div className="kpi-label">Overall Margin</div>
          <div className="kpi-value">{overallMargin}%</div>
        </div>
        <div className="kpi-card purple">
          <div className="kpi-icon">💳</div>
          <div className="kpi-label">Payment Methods</div>
          <div className="kpi-value">{payments.length}</div>
        </div>
        <div className="kpi-card orange">
          <div className="kpi-icon">🕐</div>
          <div className="kpi-label">Peak Hours</div>
          <div className="kpi-value">{peakLabel}</div>
        </div>
      </div>

      {/* Heatmap */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-title">Sales Volume — Hour × Day of Week</div>
        <div style={{ overflowX: 'auto' }}>
          <div className="heatmap-grid">
            <div className="heatmap-row">
              <div className="heatmap-label"></div>
              {hours.map(h => (
                <div key={h} className="heatmap-header">{h}:00</div>
              ))}
            </div>
            {DAYS.map((day, di) => (
              <div key={day} className="heatmap-row">
                <div className="heatmap-label">{day}</div>
                {hours.map(h => {
                  const count = heatGrid[`${di}-${h}`] || 0;
                  return (
                    <div key={h} className="heatmap-cell"
                      style={{ background: getHeatColor(count, maxCount) }}
                      title={`${day} ${h}:00 — ${count} sales`}>
                      {count > 0 ? count : ''}
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
          <div style={{ display: 'flex', gap: 12, marginTop: 12, justifyContent: 'center', fontSize: 11, color: 'var(--text-muted)' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <span style={{ width: 12, height: 12, background: 'rgba(255,255,255,0.03)', borderRadius: 2, display: 'inline-block', border: '1px solid rgba(255,255,255,0.1)' }}></span> Low
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <span style={{ width: 12, height: 12, background: '#6366f1', borderRadius: 2, display: 'inline-block' }}></span> Medium
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <span style={{ width: 12, height: 12, background: '#00d4ff', borderRadius: 2, display: 'inline-block' }}></span> High
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <span style={{ width: 12, height: 12, background: '#10b981', borderRadius: 2, display: 'inline-block' }}></span> Peak
            </span>
          </div>
        </div>
      </div>

      <div className="grid-2">
        {/* Payment Methods */}
        <div className="card">
          <div className="card-title">Payment Method Distribution</div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={payments} dataKey="total_revenue" nameKey="payment_method" cx="50%" cy="50%"
                  outerRadius={100} innerRadius={50} paddingAngle={3}
                  label={({ payment_method, total_revenue }) => `${payment_method}: ₹${Math.round(total_revenue).toLocaleString()}`}
                  labelLine={{ stroke: '#6868a0' }}>
                  {payments.map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
                </Pie>
                <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid rgba(100,100,255,0.2)', borderRadius: 10, color: '#e8e8f0' }}
                  formatter={(val) => `₹${Math.round(val).toLocaleString()}`} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Profit Margins */}
        <div className="card">
          <div className="card-title">Profit Margin by Category</div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={margins} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis type="number" tick={{ fill: '#9898b8', fontSize: 11 }}
                  tickFormatter={v => `${v}%`} />
                <YAxis type="category" dataKey="category" tick={{ fill: '#9898b8', fontSize: 10 }} width={110} />
                <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid rgba(100,100,255,0.2)', borderRadius: 10, color: '#e8e8f0' }}
                  formatter={(val, name) => [name === 'margin_pct' ? `${val}%` : `₹${Math.round(val).toLocaleString()}`, name === 'margin_pct' ? 'Margin' : 'Profit']} />
                <Bar dataKey="margin_pct" fill="url(#marginGrad)" radius={[0, 6, 6, 0]} />
                <defs>
                  <linearGradient id="marginGrad" x1="0" y1="0" x2="1" y2="0">
                    <stop offset="0%" stopColor="#10b981" />
                    <stop offset="100%" stopColor="#00d4ff" />
                  </linearGradient>
                </defs>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Profit Detail Table */}
      <div className="card">
        <div className="card-title">Category Profit Breakdown</div>
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Category</th><th>Revenue</th><th>Cost</th><th>Profit</th><th>Margin</th>
              </tr>
            </thead>
            <tbody>
              {margins.map((m, i) => (
                <tr key={i}>
                  <td style={{ fontWeight: 600 }}>{m.category}</td>
                  <td>₹{Math.round(m.total_revenue).toLocaleString()}</td>
                  <td style={{ color: 'var(--text-secondary)' }}>₹{Math.round(m.total_cost).toLocaleString()}</td>
                  <td style={{ fontWeight: 600, color: 'var(--accent-green)' }}>₹{Math.round(m.total_profit).toLocaleString()}</td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <div style={{ width: 60, height: 5, background: 'rgba(255,255,255,0.1)', borderRadius: 3 }}>
                        <div style={{ width: `${Math.max(0, Math.min(m.margin_pct || 0, 100))}%`, height: '100%', borderRadius: 3,
                          background: m.margin_pct >= 40 ? '#10b981' : m.margin_pct >= 30 ? '#f59e0b' : '#ef4444' }} />
                      </div>
                      <span style={{ fontSize: 12, fontWeight: 600 }}>{m.margin_pct}%</span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
