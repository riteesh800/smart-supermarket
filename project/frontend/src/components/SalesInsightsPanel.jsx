import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell
} from 'recharts';

const COLORS = ['#00d4ff', '#7c3aed', '#10b981', '#f59e0b', '#ef4444', '#ec4899', '#6366f1', '#14b8a6'];

export default function SalesInsightsPanel() {
  const [revenue, setRevenue] = useState(null);
  const [bestSellers, setBestSellers] = useState([]);
  const [byCategory, setByCategory] = useState([]);
  const [view, setView] = useState('daily');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.getRevenue(),
      api.getBestSellers(),
      api.getSalesByCategory()
    ]).then(([rev, best, cat]) => {
      setRevenue(rev);
      setBestSellers(best);
      setByCategory(cat);
      setLoading(false);
    }).catch(e => { console.error(e); setLoading(false); });
  }, []);

  if (loading) return <div className="loading">Loading sales data...</div>;

  const dailyData = (revenue?.daily || []).map(d => ({
    date: d.date?.slice(5),
    revenue: Math.round(d.revenue * 100) / 100,
    transactions: d.transactions
  }));

  const monthlyData = (revenue?.monthly || []).map(d => ({
    month: d.month,
    revenue: Math.round(d.revenue * 100) / 100,
    transactions: d.transactions
  }));

  const chartData = view === 'daily' ? dailyData : monthlyData;
  const xKey = view === 'daily' ? 'date' : 'month';

  const totalRevenue = dailyData.reduce((s, d) => s + d.revenue, 0);
  const totalTxns = dailyData.reduce((s, d) => s + d.transactions, 0);
  const avgDaily = dailyData.length ? totalRevenue / dailyData.length : 0;

  return (
    <div>
      <div className="page-header">
        <h2>🛍️ Sales Insights</h2>
        <p>Revenue trends, top products, and category performance</p>
      </div>

      <div className="kpi-grid">
        <div className="kpi-card green">
          <div className="kpi-icon">💰</div>
          <div className="kpi-label">Total Revenue</div>
          <div className="kpi-value">₹{totalRevenue.toLocaleString(undefined, {maximumFractionDigits: 0})}</div>
        </div>
        <div className="kpi-card blue">
          <div className="kpi-icon">🧾</div>
          <div className="kpi-label">Transactions</div>
          <div className="kpi-value">{totalTxns.toLocaleString()}</div>
        </div>
        <div className="kpi-card purple">
          <div className="kpi-icon">📊</div>
          <div className="kpi-label">Avg Daily Revenue</div>
          <div className="kpi-value">₹{avgDaily.toFixed(0)}</div>
        </div>
        <div className="kpi-card orange">
          <div className="kpi-icon">🏆</div>
          <div className="kpi-label">Top Product</div>
          <div className="kpi-value" style={{ fontSize: 16 }}>{bestSellers[0]?.name || 'N/A'}</div>
        </div>
      </div>

      {/* Revenue Chart */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div className="card-title" style={{ marginBottom: 0 }}>Revenue Trend</div>
          <div className="tabs" style={{ marginBottom: 0 }}>
            <button className={`tab ${view === 'daily' ? 'active' : ''}`} onClick={() => setView('daily')}>Daily</button>
            <button className={`tab ${view === 'monthly' ? 'active' : ''}`} onClick={() => setView('monthly')}>Monthly</button>
          </div>
        </div>
        <div className="chart-container-lg">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey={xKey} tick={{ fill: '#9898b8', fontSize: 10 }} interval="preserveStartEnd" />
              <YAxis tick={{ fill: '#9898b8', fontSize: 11 }} />
              <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid rgba(100,100,255,0.2)', borderRadius: 10, color: '#e8e8f0' }}
                formatter={(val) => [`₹${val.toLocaleString()}`, 'Revenue']} />
              <Line type="monotone" dataKey="revenue" stroke="#10b981" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid-2">
        {/* Best Sellers */}
        <div className="card">
          <div className="card-title">🏆 Best Selling Products</div>
          <div className="table-wrapper" style={{ maxHeight: 350 }}>
            <table>
              <thead><tr><th>Product</th><th>Category</th><th>Qty Sold</th><th>Revenue</th></tr></thead>
              <tbody>
                {bestSellers.slice(0, 15).map((p, i) => (
                  <tr key={p.product_id}>
                    <td>
                      <span style={{ color: 'var(--text-muted)', marginRight: 8, fontSize: 11 }}>#{i + 1}</span>
                      <span style={{ fontWeight: 600 }}>{p.name}</span>
                    </td>
                    <td><span className="badge blue">{p.category}</span></td>
                    <td>{p.total_quantity}</td>
                    <td style={{ fontWeight: 600, color: 'var(--accent-green)' }}>₹{p.total_revenue?.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Category Revenue */}
        <div className="card">
          <div className="card-title">Revenue by Category</div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={byCategory} dataKey="total_revenue" nameKey="category" cx="50%" cy="50%"
                  outerRadius={100} innerRadius={50} paddingAngle={3}
                  label={({ category, total_revenue }) => `${category}: ₹${Math.round(total_revenue)}`}
                  labelLine={{ stroke: '#6868a0' }}>
                  {byCategory.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid rgba(100,100,255,0.2)', borderRadius: 10, color: '#e8e8f0' }}
                  formatter={(val) => `₹${val.toFixed(2)}`} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
