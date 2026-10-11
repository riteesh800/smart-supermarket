import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { getCategoryColor } from '../constants/colors';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';

export default function DemandForecastPanel() {
  const [forecasts, setForecasts] = useState(null);
  const [selectedCat, setSelectedCat] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getForecasts().then(data => {
      setForecasts(data);
      const cats = Object.keys(data);
      if (cats.length > 0) setSelectedCat(cats[0]);
      setLoading(false);
    }).catch(e => { console.error(e); setLoading(false); });
  }, []);

  if (loading) return <div className="loading">Loading forecast data...</div>;
  if (!forecasts || !selectedCat) return <div className="loading">No forecast data available</div>;

  const categories = Object.keys(forecasts);
  const catData = forecasts[selectedCat];

  // Build chart data from historical
  const historical = (catData.historical_last_60 || catData.historical_last_30 || catData.historical || []).slice(-90);
  const forecast = catData.forecast || [];

  // Combine for visualization — connect forecast seamlessly to last actual point
  const chartData = [
    ...historical.map((d, i) => ({
      date: d.date?.slice(5) || '',
      fullDate: d.date || '',
      actual: d.quantity,
      predicted: i === historical.length - 1 ? d.quantity : null
    })),
    ...forecast.map(d => ({
      date: d.date?.slice(5) || '',
      fullDate: d.date || '',
      actual: null,
      predicted: d.predicted_demand
    })),
  ];

  return (
    <div>
      <div className="page-header">
        <h2>📈 Demand Forecasting</h2>
        <p>AI-powered demand predictions using Holt-Winters exponential smoothing</p>
      </div>

      {/* Category Tabs */}
      <div className="tabs" style={{ flexWrap: 'wrap' }}>
        {categories.map(cat => (
          <button key={cat} className={`tab ${selectedCat === cat ? 'active' : ''}`}
            onClick={() => setSelectedCat(cat)}
            style={selectedCat === cat ? { background: getCategoryColor(cat) } : {}}>
            {cat}
          </button>
        ))}
      </div>

      {/* Main Forecast Chart */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-title">Predicted vs Actual Demand — {selectedCat}</div>
        <div className="chart-container-lg">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="date" tick={{ fill: '#9898b8', fontSize: 10 }} interval="preserveStartEnd" />
              <YAxis tick={{ fill: '#9898b8', fontSize: 11 }} />
              <Tooltip
                contentStyle={{ background: '#1a1a2e', border: '1px solid rgba(100,100,255,0.2)', borderRadius: 10, color: '#e8e8f0' }}
                labelFormatter={(label, payload) => payload?.[0]?.payload?.fullDate || label}
                formatter={(val, name) => [val != null ? Math.round(val) : '—', name]}
              />
              <Legend />
              <Line type="monotone" dataKey="actual" stroke="#00d4ff" strokeWidth={2} dot={false} name="Actual Demand" />
              <Line type="monotone" dataKey="predicted" stroke="#f59e0b" strokeWidth={2} strokeDasharray="8 4" dot={false} name={`Predicted (${forecast.length || 30} days)`} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid-2">
        {/* Forecast Table */}
        <div className="card">
          <div className="card-title">30-Day Forecast — {selectedCat}</div>
          <div className="table-wrapper" style={{ maxHeight: 300 }}>
            <table>
              <thead><tr><th>Date</th><th>Predicted Demand</th></tr></thead>
              <tbody>
                {forecast.map((d, i) => (
                  <tr key={i}>
                    <td>{d.date}</td>
                    <td style={{ fontWeight: 600 }}>{d.predicted_demand}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Model Info */}
        <div className="card">
          <div className="card-title">Model Summary</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <div>
              <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>MODEL</span>
              <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--accent-blue)' }}>{(catData.model || 'holt_winters').replaceAll('_', ' ').toUpperCase()}</div>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>FORECAST HORIZON</span>
              <div style={{ fontSize: 18, fontWeight: 700 }}>{forecast.length || 30} Days</div>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>CATEGORIES MODELED</span>
              <div style={{ fontSize: 18, fontWeight: 700 }}>{categories.length}</div>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>HISTORICAL DATA</span>
              <div style={{ fontSize: 18, fontWeight: 700 }}>{historical.length} days</div>
            </div>
            <div style={{ marginTop: 8 }}>
              {categories.map(cat => (
                <span key={cat} className="badge blue" style={{ marginRight: 6, marginBottom: 4, display: 'inline-block', background: `${getCategoryColor(cat)}22`, color: getCategoryColor(cat) }}>
                  {cat}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
