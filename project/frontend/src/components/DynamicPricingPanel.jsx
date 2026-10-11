import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell
} from 'recharts';

const ACTION_COLORS = { Increase: '#10b981', Decrease: '#f59e0b', Hold: '#6366f1' };

export default function DynamicPricingPanel() {
  const [pricing, setPricing] = useState(null);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getPricing().then(d => { setPricing(d); setLoading(false); })
      .catch(e => { console.error(e); setLoading(false); });
  }, []);

  if (loading) return <div className="loading">Loading pricing data...</div>;
  if (!pricing) return <div className="loading">No pricing data available</div>;

  const suggestions = pricing.suggestions || [];
  const actionSummary = pricing.action_summary || {};
  const filtered = filter === 'all' ? suggestions : suggestions.filter(s => s.action === filter);

  // Chart: price change distribution
  const changeData = [
    { range: '< -10%', count: suggestions.filter(s => s.price_change_pct < -10).length, color: '#ef4444' },
    { range: '-10% to -5%', count: suggestions.filter(s => s.price_change_pct >= -10 && s.price_change_pct <= -5).length, color: '#f59e0b' },
    { range: '-5% to 0%', count: suggestions.filter(s => s.price_change_pct > -5 && s.price_change_pct < 0).length, color: '#fbbf24' },
    { range: '0% (Hold)', count: suggestions.filter(s => s.price_change_pct === 0).length, color: '#6366f1' },
    { range: '0% to +5%', count: suggestions.filter(s => s.price_change_pct > 0 && s.price_change_pct <= 5).length, color: '#34d399' },
    { range: '+5% to +10%', count: suggestions.filter(s => s.price_change_pct > 5 && s.price_change_pct <= 10).length, color: '#10b981' },
    { range: '> +10%', count: suggestions.filter(s => s.price_change_pct > 10).length, color: '#059669' },
  ].filter(d => d.count > 0);

  return (
    <div>
      <div className="page-header">
        <h2>💲 Dynamic Pricing Intelligence</h2>
        <p>AI-powered price optimization based on demand, stock, and shelf life analysis</p>
      </div>

      <div className="kpi-grid">
        <div className="kpi-card green">
          <div className="kpi-icon">📈</div>
          <div className="kpi-label">Price Increases</div>
          <div className="kpi-value">{actionSummary.Increase || 0}</div>
          <div className="kpi-sub">High demand / low stock</div>
        </div>
        <div className="kpi-card orange">
          <div className="kpi-icon">📉</div>
          <div className="kpi-label">Price Decreases</div>
          <div className="kpi-value">{actionSummary.Decrease || 0}</div>
          <div className="kpi-sub">Overstocked / low demand</div>
        </div>
        <div className="kpi-card purple">
          <div className="kpi-icon">⏸️</div>
          <div className="kpi-label">Hold / No Change</div>
          <div className="kpi-value">{actionSummary.Hold || 0}</div>
          <div className="kpi-sub">Balanced</div>
        </div>
        <div className="kpi-card blue">
          <div className="kpi-icon">📊</div>
          <div className="kpi-label">Avg Change</div>
          <div className="kpi-value">{pricing.avg_change_pct > 0 ? '+' : ''}{pricing.avg_change_pct}%</div>
          <div className="kpi-sub">Across all products</div>
        </div>
      </div>

      {/* Price Change Distribution Chart */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-title">Price Change Distribution</div>
        <div className="chart-container">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={changeData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="range" tick={{ fill: '#9898b8', fontSize: 11 }} />
              <YAxis tick={{ fill: '#9898b8', fontSize: 11 }} />
              <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid rgba(100,100,255,0.2)', borderRadius: 10, color: '#e8e8f0' }} />
              <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                {changeData.map((d, i) => <Cell key={i} fill={d.color} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Filter Tabs + Table */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div className="card-title" style={{ marginBottom: 0 }}>Pricing Suggestions</div>
          <div className="tabs" style={{ marginBottom: 0 }}>
            {['all', 'Increase', 'Decrease', 'Hold'].map(f => (
              <button key={f} className={`tab ${filter === f ? 'active' : ''}`}
                onClick={() => setFilter(f)}
                style={filter === f && f !== 'all' ? { background: ACTION_COLORS[f] } : {}}>
                {f === 'all' ? `All (${suggestions.length})` : `${f} (${actionSummary[f] || 0})`}
              </button>
            ))}
          </div>
        </div>
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Product</th><th>Category</th><th>Current</th>
                <th>Suggested</th><th>Change</th><th>Action</th><th>Reason</th>
                <th>Stock</th><th>Days Left</th><th>Confidence</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((s, i) => (
                <tr key={i}>
                  <td style={{ fontWeight: 600 }}>{s.product_name}</td>
                  <td><span className="badge blue">{s.category}</span></td>
                  <td>₹{s.current_price}</td>
                  <td style={{ fontWeight: 700, color: s.action === 'Increase' ? 'var(--accent-green)' : s.action === 'Decrease' ? 'var(--accent-orange)' : 'var(--text-primary)' }}>
                    ₹{s.suggested_price}
                  </td>
                  <td>
                    <span className={`badge ${s.price_change_pct > 0 ? 'green' : s.price_change_pct < 0 ? 'orange' : 'purple'}`}>
                      {s.price_change_pct > 0 ? '+' : ''}{s.price_change_pct}%
                    </span>
                  </td>
                  <td>
                    <span className={`badge ${s.action === 'Increase' ? 'green' : s.action === 'Decrease' ? 'orange' : 'purple'}`}>
                      {s.action === 'Increase' ? '↑' : s.action === 'Decrease' ? '↓' : '—'} {s.action}
                    </span>
                  </td>
                  <td style={{ fontSize: 12, color: 'var(--text-secondary)', maxWidth: 200 }}>{s.reason}</td>
                  <td>{s.current_stock}</td>
                  <td>{s.days_of_stock < 999 ? `${s.days_of_stock}d` : '—'}</td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                      <div style={{ width: 40, height: 4, background: 'rgba(255,255,255,0.1)', borderRadius: 2 }}>
                        <div style={{ width: `${s.confidence * 100}%`, height: '100%', background: 'var(--accent-blue)', borderRadius: 2 }} />
                      </div>
                      <span style={{ fontSize: 11 }}>{(s.confidence * 100).toFixed(0)}%</span>
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
