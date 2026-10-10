import React, { useEffect, useState, useCallback } from 'react';
import { api } from '../services/api';

const FILE_TYPES = ['sales', 'products', 'customers', 'inventory', 'suppliers'];
const INTERNAL_FIELDS = {
  sales: ['sale_id', 'basket_id', 'product_id', 'customer_id', 'quantity', 'unit_price', 'total_price', 'discount', 'timestamp', 'payment_method', 'name', 'category'],
  products: ['product_id', 'name', 'category', 'price', 'cost', 'supplier', 'shelf_life_days', 'unit'],
  customers: ['customer_id', 'first_name', 'last_name', 'customer_name', 'age', 'gender', 'membership_tier', 'email', 'phone', 'zip_code'],
  inventory: ['product_id', 'current_stock', 'max_stock', 'reorder_point', 'last_restock_date', 'warehouse_location'],
  suppliers: ['supplier_id', 'name', 'contact_email', 'lead_time_days', 'reliability_score'],
};

export default function DataSetupPanel({ onFlagsUpdate }) {
  const [status, setStatus] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [importing, setImporting] = useState(false);
  const [preview, setPreview] = useState(null);
  const [mapping, setMapping] = useState({});
  const [fileType, setFileType] = useState('');
  const [dragOver, setDragOver] = useState(false);
  const [message, setMessage] = useState(null);
  const [loading, setLoading] = useState(true);

  const loadStatus = useCallback(async () => {
    try {
      const s = await api.getUploadStatus();
      setStatus(s);
      return s;
    } catch (e) { console.error(e); } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadStatus(); }, [loadStatus]);

  async function handleFile(file) {
    if (!file || !file.name.endsWith('.csv')) {
      setMessage({ type: 'error', text: 'Please upload a .csv file' });
      return;
    }
    setUploading(true);
    setMessage(null);
    try {
      const result = await api.previewUpload(file);
      if (result.error) {
        setMessage({ type: 'error', text: result.error });
      } else {
        setPreview(result);
        setMapping(result.detected_mapping || {});
        setFileType(result.detected_type || 'sales');
      }
    } catch (e) {
      setMessage({ type: 'error', text: 'Upload failed: ' + e.message });
    }
    setUploading(false);
  }

  function handleDrop(e) {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer?.files?.[0];
    if (file) handleFile(file);
  }

  function handleFileInput(e) {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  }

  function updateMapping(internalField, csvColumn) {
    setMapping(prev => {
      const next = { ...prev };
      // Remove old mapping for this field
      delete next[internalField];
      if (csvColumn) next[internalField] = csvColumn;
      return next;
    });
  }

  async function handleImport() {
    if (!preview) return;
    setImporting(true);
    setMessage(null);
    try {
      const result = await api.importData(preview.upload_id, fileType, mapping);
      if (result.error) {
        setMessage({ type: 'error', text: result.error });
      } else {
        setMessage({
          type: 'success',
          text: `Imported ${result.rows_imported} rows as ${result.file_type}. ${result.ml_status === 'trained' ? 'ML models trained!' : result.ml_status || ''}`
        });
        setPreview(null);
        const newStatus = await loadStatus();
        if (onFlagsUpdate && newStatus?.feature_flags) onFlagsUpdate(newStatus.feature_flags);
      }
    } catch (e) {
      setMessage({ type: 'error', text: 'Import failed: ' + e.message });
    }
    setImporting(false);
  }

  async function handleReset() {
    if (!window.confirm('This will delete ALL data. Are you sure?')) return;
    try {
      await api.resetData();
      setMessage({ type: 'success', text: 'All data cleared' });
      setPreview(null);
      const newStatus = await loadStatus();
      if (onFlagsUpdate && newStatus?.feature_flags) {
        onFlagsUpdate(newStatus.feature_flags);
      }
    } catch (e) {
      setMessage({ type: 'error', text: 'Reset failed' });
    }
  }

  async function handleLoadDemo() {
    setImporting(true);
    setMessage(null);
    try {
      const result = await api.loadDemoData();
      if (result.error) {
        setMessage({ type: 'error', text: result.error });
      } else {
        setMessage({ type: 'success', text: 'Demo data loaded with all features!' });
        const newStatus = await loadStatus();
        if (onFlagsUpdate && newStatus?.feature_flags) onFlagsUpdate(newStatus.feature_flags);
      }
    } catch (e) {
      setMessage({ type: 'error', text: 'Failed to load demo data' });
    }
    setImporting(false);
  }

  if (loading) return <div className="loading">Loading data status...</div>;

  const flags = status?.feature_flags || {};
  const counts = status?.table_counts || {};

  return (
    <div>
      <div className="page-header">
        <h2>📁 Data Setup</h2>
        <p>Upload your own CSV datasets or use the built-in demo data</p>
      </div>

      {/* Message */}
      {message && (
        <div className={`upload-message ${message.type}`}>
          {message.type === 'success' ? '✅' : '❌'} {message.text}
        </div>
      )}

      {/* Current Data Status */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-title">Current Data Status</div>
        {flags.has_data ? (
          <>
            <div className="kpi-grid" style={{ marginBottom: 16 }}>
              <div className="kpi-card blue" style={{ minHeight: 'auto', padding: '16px 20px' }}>
                <div className="kpi-label">Products</div>
                <div className="kpi-value" style={{ fontSize: 24 }}>{counts.products?.toLocaleString() || 0}</div>
              </div>
              <div className="kpi-card green" style={{ minHeight: 'auto', padding: '16px 20px' }}>
                <div className="kpi-label">Customers</div>
                <div className="kpi-value" style={{ fontSize: 24 }}>{counts.customers?.toLocaleString() || 0}</div>
              </div>
              <div className="kpi-card purple" style={{ minHeight: 'auto', padding: '16px 20px' }}>
                <div className="kpi-label">Sales</div>
                <div className="kpi-value" style={{ fontSize: 24 }}>{counts.sales?.toLocaleString() || 0}</div>
              </div>
              <div className="kpi-card orange" style={{ minHeight: 'auto', padding: '16px 20px' }}>
                <div className="kpi-label">Inventory</div>
                <div className="kpi-value" style={{ fontSize: 24 }}>{counts.inventory?.toLocaleString() || 0}</div>
              </div>
            </div>

            {/* Feature Availability */}
            <div className="card-title" style={{ marginTop: 16, fontSize: 13 }}>Available Features</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {Object.entries(flags).filter(([k]) => k.startsWith('enable_')).map(([k, v]) => (
                <span key={k} className={`badge ${v ? 'green' : 'red'}`} style={{ fontSize: 12, padding: '4px 10px' }}>
                  {v ? '✓' : '✗'} {k.replace('enable_', '').replace(/_/g, ' ')}
                </span>
              ))}
            </div>

            <div style={{ marginTop: 20, display: 'flex', gap: 10 }}>
              <button className="btn btn-secondary" onClick={handleReset}>🗑️ Reset All Data</button>
            </div>
          </>
        ) : (
          <div style={{ textAlign: 'center', padding: '30px 0' }}>
            <div style={{ fontSize: 48, marginBottom: 12 }}>📭</div>
            <p style={{ color: 'var(--text-secondary)', marginBottom: 20 }}>No data loaded. Upload your CSV files or load the demo dataset.</p>
            <button className="btn btn-primary" onClick={handleLoadDemo} disabled={importing}
              style={{ padding: '12px 30px', fontSize: 15 }}>
              {importing ? '⏳ Loading...' : '🚀 Load Demo Dataset'}
            </button>
          </div>
        )}
      </div>

      {/* Upload Area */}
      {!preview && (
        <div className="card" style={{ marginBottom: 24 }}>
          <div className="card-title">Upload CSV File</div>
          <div
            className={`upload-dropzone ${dragOver ? 'drag-over' : ''}`}
            onDragOver={e => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => document.getElementById('csv-file-input')?.click()}
          >
            {uploading ? (
              <div className="upload-icon">⏳</div>
            ) : (
              <>
                <div className="upload-icon">📄</div>
                <div className="upload-text">
                  <strong>Drop your CSV file here</strong>
                  <span>or click to browse</span>
                </div>
                <div className="upload-hint">
                  Supports: Sales, Product, Customer, Inventory, and Supplier CSVs
                </div>
              </>
            )}
            <input id="csv-file-input" type="file" accept=".csv" style={{ display: 'none' }}
              onChange={handleFileInput} />
          </div>
        </div>
      )}

      {/* Preview & Mapping */}
      {preview && (
        <div className="card" style={{ marginBottom: 24 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <div>
              <div className="card-title" style={{ marginBottom: 4 }}>
                Preview: {preview.filename}
              </div>
              <span style={{ color: 'var(--text-secondary)', fontSize: 13 }}>
                {preview.total_rows?.toLocaleString()} rows • {preview.columns?.length} columns • 
                Detected as: <strong style={{ color: 'var(--accent-blue)' }}>{fileType}</strong>
              </span>
            </div>
            <button className="btn btn-secondary" onClick={() => setPreview(null)}>✕ Cancel</button>
          </div>

          {/* File Type Selector */}
          <div style={{ marginBottom: 16 }}>
            <label style={{ fontSize: 13, color: 'var(--text-secondary)', marginRight: 8 }}>Data type:</label>
            {FILE_TYPES.map(t => (
              <button key={t} className={`tab ${fileType === t ? 'active' : ''}`}
                onClick={() => setFileType(t)} style={{ marginRight: 6 }}>
                {t === 'sales' ? '🛍️' : t === 'products' ? '📦' : t === 'customers' ? '👥' : t === 'inventory' ? '📋' : '🚚'} {t.charAt(0).toUpperCase() + t.slice(1)}
              </button>
            ))}
          </div>

          {/* Column Mapping */}
          <div className="card-title" style={{ fontSize: 13, marginBottom: 8 }}>Column Mapping</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 10, marginBottom: 20 }}>
            {INTERNAL_FIELDS[fileType]?.map(field => {
              const isAutoDetected = mapping[field] && mapping[field] === preview.detected_mapping?.[field];
              return (
                <div key={field} className="mapping-row">
                  <label className="mapping-label">
                    {field.replace(/_/g, ' ')}
                    {isAutoDetected && <span className="auto-badge">auto</span>}
                  </label>
                  <select className="filter-select" style={{ width: '100%', minWidth: 0 }}
                    value={mapping[field] || ''}
                    onChange={e => updateMapping(field, e.target.value)}>
                    <option value="">— skip —</option>
                    {preview.columns?.map(col => (
                      <option key={col} value={col}>{col}</option>
                    ))}
                  </select>
                </div>
              );
            })}
          </div>

          {/* Data Preview Table */}
          <div className="card-title" style={{ fontSize: 13, marginBottom: 8 }}>Data Preview (first 10 rows)</div>
          <div className="table-wrapper" style={{ maxHeight: 300 }}>
            <table>
              <thead>
                <tr>
                  {preview.columns?.map(col => {
                    const mappedTo = Object.entries(mapping).find(([k, v]) => v === col);
                    return (
                      <th key={col}>
                        {col}
                        {mappedTo && <div style={{ fontSize: 10, color: 'var(--accent-green)', fontWeight: 400 }}>→ {mappedTo[0]}</div>}
                      </th>
                    );
                  })}
                </tr>
              </thead>
              <tbody>
                {preview.preview_rows?.map((row, i) => (
                  <tr key={i}>
                    {preview.columns?.map(col => (
                      <td key={col} style={{ fontSize: 12, whiteSpace: 'nowrap' }}>{String(row[col] ?? '')}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Import Button */}
          <div style={{ marginTop: 20, display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
            <button className="btn btn-secondary" onClick={() => setPreview(null)}>Cancel</button>
            <button className="btn btn-primary" onClick={handleImport} disabled={importing}
              style={{ padding: '10px 30px' }}>
              {importing ? '⏳ Importing & Training ML...' : `📥 Import ${preview.total_rows?.toLocaleString()} rows as ${fileType}`}
            </button>
          </div>
        </div>
      )}

      {/* Instructions */}
      <div className="card">
        <div className="card-title">📋 How It Works</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 20 }}>
          <div>
            <h4 style={{ color: 'var(--accent-blue)', marginBottom: 8 }}>1. Upload CSV</h4>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
              Drop any retail CSV file. The system auto-detects your columns.
              Minimum needed: product ID + amount + date.
            </p>
          </div>
          <div>
            <h4 style={{ color: 'var(--accent-green)', marginBottom: 8 }}>2. Confirm Mapping</h4>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
              Review auto-detected column mappings. Adjust if needed.
              Unmapped columns are simply skipped.
            </p>
          </div>
          <div>
            <h4 style={{ color: 'var(--accent-purple)', marginBottom: 8 }}>3. Analyze</h4>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
              System loads data, trains ML models, and enables features based on available columns.
              Missing data = features gracefully hidden.
            </p>
          </div>
        </div>

        <div style={{ marginTop: 20, padding: 16, background: 'rgba(0,212,255,0.05)', borderRadius: 8, border: '1px solid rgba(0,212,255,0.15)' }}>
          <strong style={{ color: 'var(--accent-blue)' }}>💡 Tip:</strong>
          <span style={{ color: 'var(--text-secondary)', fontSize: 13, marginLeft: 8 }}>
            Upload sales first. Products and customers get auto-extracted. Upload separate product/customer CSVs for richer data.
          </span>
        </div>
      </div>
    </div>
  );
}
