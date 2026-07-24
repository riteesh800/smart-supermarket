import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceDot
} from 'recharts';

export default function AnomaliesPanel() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getAnomalies().then(d => {
      setData(d);
      setLoading(false);
    }).catch(e => { console.error(e); setLoading(false); });
  }, []);

  if (loading) return <div className="loading">Loading anomaly data...</div>;
  if (!data) return <div className="loading">No anomaly data available</div>;

  const anomalies = data.anomalies || [];
  const daily = (data.daily_summary || []).map(d => ({
    date: d.date?.slice(5),
    fullDate: d.date,
    sales: Math.round(d.total_sales * 100) / 100,
    isAnomaly: d.is_anomaly
  }));

  const anomalyDots = daily.filter(d => d.isAnomaly);

  return (
    <div>
      <div className="page-header">
        <h2>⚠️ Anomaly Detection</h2>
        <p>Isolation Forest powered detection of unusual sales patterns</p>
      </div>

      <div className="kpi-grid">
        <div className="kpi-card red">
          <div className="kpi-icon">🔍</div>
          <div className="kpi-label">Total Anomalies</div>
          <div className="kpi-value">{data.total_anomalies}</div>
        </div>
        <div className="kpi-card orange">
          <div className="kpi-icon">📈</div>
          <div className="kpi-label">Sales Spikes</div>
          <div className="kpi-value">{data.spikes}</div>
        </div>
        <div className="kpi-card purple">
          <div className="kpi-icon">📉</div>
          <div className="kpi-label">Sales Drops</div>
          <div className="kpi-value">{data.drops}</div>
        </div>
        <div className="kpi-card blue">
          <div className="kpi-icon">🤖</div>
          <div className="kpi-label">Model</div>
          <div className="kpi-value" style={{ fontSize: 16 }}>Isolation Forest</div>
        </div>
      </div>

      {/* Sales Timeline with Anomalies */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-title">Sales Timeline with Detected Anomalies</div>
        <div className="chart-container-lg">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={daily}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="date" tick={{ fill: '#9898b8', fontSize: 10 }} interval="preserveStartEnd" />
              <YAxis tick={{ fill: '#9898b8', fontSize: 11 }} />
              <Tooltip
                contentStyle={{ background: '#1a1a2e', border: '1px solid rgba(100,100,255,0.2)', borderRadius: 10, color: '#e8e8f0' }}
                formatter={(val) => [`₹${val.toLocaleString()}`, 'Sales']}
              />
              <Line type="monotone" dataKey="sales" stroke="#00d4ff" strokeWidth={1.5} dot={false} />
              {anomalyDots.map((d, i) => (
                <ReferenceDot key={i} x={d.date} y={d.sales} r={5} fill="#ef4444" stroke="#ef4444" strokeWidth={2} />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div style={{ display: 'flex', gap: 20, marginTop: 12, justifyContent: 'center' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--text-secondary)' }}>
            <span style={{ width: 12, height: 3, background: '#00d4ff', display: 'inline-block', borderRadius: 2 }}></span> Daily Sales
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--text-secondary)' }}>
            <span style={{ width: 8, height: 8, background: '#ef4444', display: 'inline-block', borderRadius: '50%' }}></span> Anomaly
          </span>
        </div>
      </div>

      {/* Anomaly Details Table */}
      <div className="card">
        <div className="card-title">Anomaly Details</div>
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Date</th><th>Type</th><th>Severity</th><th>Total Sales</th>
                <th>7-Day Avg</th><th>Deviation</th>
                <th>Transactions</th>
              </tr>
            </thead>
            <tbody>
              {anomalies.map((a, i) => (
                <tr key={i}>
                  <td style={{ fontWeight: 500 }}>{a.date}</td>
                  <td>
                    <span className={`badge ${a.anomaly_type === 'Spike' ? 'orange' : 'purple'}`}>
                      {a.anomaly_type === 'Spike' ? '📈' : '📉'} {a.anomaly_type}
                    </span>
                  </td>
                  <td>
                    <span className={`badge ${a.severity === 'High' ? 'red' : 'orange'}`}>
                      {a.severity}
                    </span>
                  </td>
                  <td style={{ fontWeight: 600 }}>₹{a.total_sales}</td>
                  <td style={{ color: 'var(--text-secondary)' }}>₹{a.sales_7d_avg}</td>
                  <td style={{
                    fontWeight: 600,
                    color: a.sales_deviation > 0 ? 'var(--accent-green)' : 'var(--accent-red)'
                  }}>
                    {a.sales_deviation > 0 ? '+' : ''}₹{a.sales_deviation}
                  </td>
                  <td>{a.num_transactions}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
