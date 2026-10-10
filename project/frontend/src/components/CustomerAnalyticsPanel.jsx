import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, ZAxis,
  BarChart, Bar, LineChart, Line
} from 'recharts';

const SEGMENT_COLORS = {
  'Champions': '#10b981',
  'Loyal Customers': '#00d4ff',
  'Potential': '#7c3aed',
  'At Risk': '#f59e0b',
  'Lost': '#ef4444',
};

export default function CustomerAnalyticsPanel() {
  const [segments, setSegments] = useState(null);
  const [allCustomers, setAllCustomers] = useState([]);
  const [topCustomers, setTopCustomers] = useState([]);
  const [demographics, setDemographics] = useState(null);
  const [retention, setRetention] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({
    first_name: '', last_name: '', age: 30, gender: 'Other', membership_tier: 'Bronze', email: ''
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.allSettled([
      api.getSegments(),
      api.getAllSegmented(),
      api.getTopCustomers(),
      api.getDemographics(),
      api.getRetention()
    ]).then(([seg, all, top, demo, ret]) => {
      if (seg.status === 'fulfilled') setSegments(seg.value);
      if (all.status === 'fulfilled') setAllCustomers(all.value);
      if (top.status === 'fulfilled') setTopCustomers(top.value);
      if (demo.status === 'fulfilled') setDemographics(demo.value);
      if (ret.status === 'fulfilled') setRetention(ret.value);
      setLoading(false);
    });
  }, []);

  // Close modal on Escape key
  useEffect(() => {
    if (!showModal) return;
    const onKey = (e) => { if (e.key === 'Escape') setShowModal(false); };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [showModal]);

  async function handleAddCustomer(e) {
    e.preventDefault();
    try {
      await api.addCustomer({ ...form, age: parseInt(form.age) });
      setShowModal(false);
      setForm({ first_name: '', last_name: '', age: 30, gender: 'Other', membership_tier: 'Bronze', email: '' });
      const top = await api.getTopCustomers();
      setTopCustomers(top);
    } catch (e) { alert('Error adding customer'); }
  }

  function handleExportCSV() {
    const url = api.exportCustomersCSV();
    window.open(url, '_blank');
  }

  if (loading) return <div className="loading">Loading customer data...</div>;

  const segmentData = segments?.segment_counts
    ? Object.entries(segments.segment_counts).map(([name, value]) => ({ name, value }))
    : [];

  const TIER_COLORS = { Platinum: '#00d4ff', Gold: '#f59e0b', Silver: '#9898b8', Bronze: '#b45309' };

  return (
    <div>
      <div className="page-header">
        <h2>👥 Customer Analytics</h2>
        <p>RFM analysis, K-Means segmentation, demographics, and retention — {segments?.total_customers?.toLocaleString()} customers</p>
      </div>

      {/* KPI Row */}
      <div className="kpi-grid">
        <div className="kpi-card green">
          <div className="kpi-icon">🏆</div>
          <div className="kpi-label">Champions</div>
          <div className="kpi-value">{segments?.segment_counts?.Champions || 0}</div>
        </div>
        <div className="kpi-card blue">
          <div className="kpi-icon">💎</div>
          <div className="kpi-label">Loyal</div>
          <div className="kpi-value">{segments?.segment_counts?.['Loyal Customers'] || 0}</div>
        </div>
        <div className="kpi-card purple">
          <div className="kpi-icon">🌱</div>
          <div className="kpi-label">Potential</div>
          <div className="kpi-value">{segments?.segment_counts?.Potential || 0}</div>
        </div>
        <div className="kpi-card orange">
          <div className="kpi-icon">⚡</div>
          <div className="kpi-label">At Risk</div>
          <div className="kpi-value">{segments?.segment_counts?.['At Risk'] || 0}</div>
        </div>
        <div className="kpi-card red">
          <div className="kpi-icon">📉</div>
          <div className="kpi-label">Lost</div>
          <div className="kpi-value">{segments?.segment_counts?.Lost || 0}</div>
        </div>
      </div>

      <div className="grid-2">
        {/* Segment Distribution */}
        <div className="card">
          <div className="card-title">Customer Segments</div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={segmentData} dataKey="value" nameKey="name" cx="50%" cy="50%"
                  outerRadius={100} innerRadius={50} paddingAngle={4}
                  label={({ name, value }) => `${name}: ${value}`}
                  labelLine={{ stroke: '#6868a0' }}>
                  {segmentData.map((entry, i) => (
                    <Cell key={i} fill={SEGMENT_COLORS[entry.name] || '#6366f1'} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid rgba(100,100,255,0.2)', borderRadius: 10, color: '#e8e8f0' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* RFM Scatter */}
        <div className="card">
          <div className="card-title">RFM Analysis (Frequency vs Monetary)</div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="frequency" name="Frequency" tick={{ fill: '#9898b8', fontSize: 11 }} />
                <YAxis dataKey="monetary" name="Monetary" tick={{ fill: '#9898b8', fontSize: 11 }} />
                <ZAxis dataKey="recency" range={[20, 200]} name="Recency" />
                <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid rgba(100,100,255,0.2)', borderRadius: 10, color: '#e8e8f0' }}
                  formatter={(val, name) => [name === 'Monetary' ? `₹${val}` : val, name]} />
                {Object.keys(SEGMENT_COLORS).map(seg => (
                  <Scatter key={seg} name={seg} data={allCustomers.filter(c => c.segment === seg)}
                    fill={SEGMENT_COLORS[seg]} opacity={0.7} />
                ))}
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Demographics */}
      {demographics && (
        <div className="grid-2" style={{ marginTop: 0 }}>
          {/* Age Distribution */}
          <div className="card">
            <div className="card-title">Age Distribution</div>
            <div className="chart-container">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={demographics.age_distribution}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="age_group" tick={{ fill: '#9898b8', fontSize: 11 }} />
                  <YAxis tick={{ fill: '#9898b8', fontSize: 11 }} />
                  <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid rgba(100,100,255,0.2)', borderRadius: 10, color: '#e8e8f0' }} />
                  <Bar dataKey="count" fill="#7c3aed" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Tier Distribution */}
          <div className="card">
            <div className="card-title">Membership Tiers</div>
            <div className="chart-container">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={demographics.tier_distribution} dataKey="count" nameKey="tier" cx="50%" cy="50%"
                    outerRadius={100} innerRadius={50} paddingAngle={4}
                    label={({ tier, count }) => `${tier}: ${count}`}
                    labelLine={{ stroke: '#6868a0' }}>
                    {demographics.tier_distribution.map((entry, i) => (
                      <Cell key={i} fill={TIER_COLORS[entry.tier] || '#6366f1'} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid rgba(100,100,255,0.2)', borderRadius: 10, color: '#e8e8f0' }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* Retention Chart */}
      {retention.length > 0 && (
        <div className="card" style={{ marginBottom: 24 }}>
          <div className="card-title">Monthly Active Customers (Retention)</div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={retention}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="month" tick={{ fill: '#9898b8', fontSize: 10 }} />
                <YAxis tick={{ fill: '#9898b8', fontSize: 11 }} />
                <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid rgba(100,100,255,0.2)', borderRadius: 10, color: '#e8e8f0' }} />
                <Line type="monotone" dataKey="active_customers" stroke="#00d4ff" strokeWidth={2} dot={false} name="Active Customers" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Top Customers + Actions */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, flexWrap: 'wrap', gap: 8 }}>
          <div className="card-title" style={{ marginBottom: 0 }}>Top Customers</div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn btn-secondary" onClick={handleExportCSV}>📥 Export CSV</button>
            <button className="btn btn-primary" onClick={() => setShowModal(true)}>+ Add Customer</button>
          </div>
        </div>
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>ID</th><th>Name</th><th>Segment</th><th>Tier</th>
                <th>Recency</th><th>Frequency</th><th>Monetary</th>
              </tr>
            </thead>
            <tbody>
              {topCustomers.map(c => (
                <tr key={c.customer_id}>
                  <td style={{ color: 'var(--text-muted)', fontSize: 12 }}>{c.customer_id}</td>
                  <td style={{ fontWeight: 600 }}>{c.first_name} {c.last_name}</td>
                  <td>
                    <span className="badge" style={{
                      background: `${SEGMENT_COLORS[c.segment] || '#6366f1'}22`,
                      color: SEGMENT_COLORS[c.segment] || '#6366f1'
                    }}>{c.segment}</span>
                  </td>
                  <td><span className="badge purple">{c.membership_tier}</span></td>
                  <td>{c.recency}d</td>
                  <td>{c.frequency}</td>
                  <td style={{ fontWeight: 600, color: 'var(--accent-green)' }}>₹{c.monetary?.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add Customer Modal */}
      {showModal && (
        <div className="modal-overlay" role="dialog" aria-modal="true" aria-label="Add New Customer" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <h3>👤 Add New Customer</h3>
            <form onSubmit={handleAddCustomer}>
              <div className="form-row">
                <div className="form-group">
                  <label>First Name</label>
                  <input required value={form.first_name} onChange={e => setForm({...form, first_name: e.target.value})} />
                </div>
                <div className="form-group">
                  <label>Last Name</label>
                  <input required value={form.last_name} onChange={e => setForm({...form, last_name: e.target.value})} />
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Age</label>
                  <input type="number" min="18" max="100" value={form.age} onChange={e => setForm({...form, age: e.target.value})} />
                </div>
                <div className="form-group">
                  <label>Gender</label>
                  <select value={form.gender} onChange={e => setForm({...form, gender: e.target.value})}>
                    <option value="M">Male</option>
                    <option value="F">Female</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Membership Tier</label>
                  <select value={form.membership_tier} onChange={e => setForm({...form, membership_tier: e.target.value})}>
                    {['Bronze','Silver','Gold','Platinum'].map(t => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label>Email</label>
                  <input type="email" value={form.email} onChange={e => setForm({...form, email: e.target.value})} placeholder="Optional" />
                </div>
              </div>
              <div className="modal-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Add Customer</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
