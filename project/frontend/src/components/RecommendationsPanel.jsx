import React, { useEffect, useState } from 'react';
import { api } from '../services/api';

export default function RecommendationsPanel() {
  const [data, setData] = useState(null);
  const [pricing, setPricing] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.allSettled([
      api.getRecommendations(),
      api.getPricing()
    ]).then(([rec, price]) => {
      if (rec.status === 'fulfilled') setData(rec.value);
      if (price.status === 'fulfilled') setPricing(price.value);
      setLoading(false);
    });
  }, []);

  if (loading) return <div className="loading">Loading recommendations...</div>;

  const suggestions = data?.suggestions || [];
  const rules = data?.top_rules || [];
  const priceSuggestions = pricing?.suggestions || [];
  const actionSummary = pricing?.action_summary || {};

  return (
    <div>
      <div className="page-header">
        <h2>🤖 Recommendations & Pricing</h2>
        <p>AI-powered product suggestions and dynamic pricing intelligence</p>
      </div>

      <div className="kpi-grid">
        <div className="kpi-card blue">
          <div className="kpi-icon">📦</div>
          <div className="kpi-label">Restock Suggestions</div>
          <div className="kpi-value">{suggestions.length}</div>
        </div>
        <div className="kpi-card green">
          <div className="kpi-icon">📈</div>
          <div className="kpi-label">Price Increase</div>
          <div className="kpi-value">{actionSummary.Increase || 0}</div>
        </div>
        <div className="kpi-card orange">
          <div className="kpi-icon">📉</div>
          <div className="kpi-label">Price Decrease</div>
          <div className="kpi-value">{actionSummary.Decrease || 0}</div>
        </div>
        <div className="kpi-card purple">
          <div className="kpi-icon">🔗</div>
          <div className="kpi-label">Association Rules</div>
          <div className="kpi-value">{data?.total_rules || 0}</div>
        </div>
      </div>

      <div className="grid-2">
        {/* Product Suggestions */}
        <div className="card">
          <div className="card-title">🛒 Product Suggestions (Co-purchase Patterns)</div>
          {suggestions.length === 0
            ? <p style={{ color: 'var(--text-muted)' }}>No suggestions available</p>
            : suggestions.map((s, i) => (
              <div key={i} style={{
                display: 'flex', alignItems: 'center', gap: 12, padding: '12px 0',
                borderBottom: '1px solid rgba(255,255,255,0.03)'
              }}>
                <span style={{ fontSize: 24 }}>📦</span>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600 }}>{s.product_name}</div>
                  <div style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{s.reason}</div>
                </div>
                <span className="badge blue">{s.category}</span>
                <span style={{ fontSize: 12, color: 'var(--accent-purple)' }}>Lift: {Number(s.lift || 0).toFixed(2)}x</span>
              </div>
            ))
          }
        </div>

        {/* Association Rules */}
        <div className="card">
          <div className="card-title">🔗 Association Rules (Frequently Bought Together)</div>
          <div className="table-wrapper" style={{ maxHeight: 350 }}>
            <table>
              <thead><tr><th>If Buys</th><th>Then Buys</th><th>Confidence</th><th>Lift</th></tr></thead>
              <tbody>
                {rules.map((r, i) => (
                  <tr key={i}>
                    <td style={{ fontWeight: 500 }}>{r.antecedent_name}</td>
                    <td style={{ fontWeight: 500 }}>{r.consequent_name}</td>
                    <td>{(r.confidence * 100).toFixed(1)}%</td>
                    <td style={{ color: 'var(--accent-purple)', fontWeight: 600 }}>{Number(r.lift || 0).toFixed(2)}x</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Dynamic Pricing Table */}
      <div className="card">
        <div className="card-title">💲 Dynamic Pricing Suggestions</div>
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Product</th><th>Category</th><th>Current Price</th>
                <th>Suggested</th><th>Change</th><th>Action</th><th>Reason</th>
                <th>Stock</th><th>Confidence</th>
              </tr>
            </thead>
            <tbody>
              {priceSuggestions.filter(s => s.action !== 'Hold').map((s, i) => (
                <tr key={i}>
                  <td style={{ fontWeight: 600 }}>{s.product_name}</td>
                  <td><span className="badge blue">{s.category}</span></td>
                  <td>₹{s.current_price}</td>
                  <td style={{ fontWeight: 700, color: s.action === 'Increase' ? 'var(--accent-green)' : 'var(--accent-orange)' }}>
                    ₹{s.suggested_price}
                  </td>
                  <td>
                    <span className={`badge ${s.price_change_pct > 0 ? 'green' : 'orange'}`}>
                      {s.price_change_pct > 0 ? '+' : ''}{s.price_change_pct}%
                    </span>
                  </td>
                  <td>
                    <span className={`badge ${s.action === 'Increase' ? 'green' : 'orange'}`}>
                      {s.action === 'Increase' ? '↑' : '↓'} {s.action}
                    </span>
                  </td>
                  <td style={{ fontSize: 12, color: 'var(--text-secondary)', maxWidth: 200 }}>{s.reason}</td>
                  <td>{s.current_stock}</td>
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
