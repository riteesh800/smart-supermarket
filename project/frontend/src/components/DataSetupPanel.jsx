import React, { useEffect, useState, useCallback, useRef } from 'react';
import { api } from '../services/api';
import { confirmDialog } from './ThemeDialog';
import SampleDataModal from './SampleDataModal';
import { getFeatureRequirement } from '../constants/featureRequirements';
import LockedFeaturePopover from './LockedFeaturePopover';
import { useColumnMapping } from '../context/ColumnMappingContext';
import { useAuth } from '../context/AuthContext';

const FILE_TYPES = ['sales', 'products', 'customers', 'inventory', 'suppliers'];
const INTERNAL_FIELDS = {
  sales: ['sale_id', 'basket_id', 'product_id', 'customer_id', 'quantity', 'unit_price', 'total_price', 'discount', 'timestamp', 'payment_method', 'name', 'category'],
  products: ['product_id', 'name', 'category', 'price', 'cost', 'supplier', 'shelf_life_days', 'unit'],
  customers: ['customer_id', 'first_name', 'last_name', 'customer_name', 'age', 'gender', 'membership_tier', 'email', 'phone', 'zip_code'],
  inventory: ['product_id', 'current_stock', 'max_stock', 'reorder_point', 'last_restock_date', 'warehouse_location'],
  suppliers: ['supplier_id', 'name', 'contact_email', 'lead_time_days', 'reliability_score'],
};

export default function DataSetupPanel({ onFlagsUpdate, onNavigateToDashboard }) {
  const { isLoggedIn, updateUserState } = useAuth();
  const { refreshMapping } = useColumnMapping();
  const [status, setStatus] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [importing, setImporting] = useState(false);
  const [showSampleModal, setShowSampleModal] = useState(false);
  const [preview, setPreview] = useState(null);
  const [mapping, setMapping] = useState({});
  const [fileType, setFileType] = useState('');
  const [dragOver, setDragOver] = useState(false);
  const [message, setMessage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lockedFeatureTooltip, setLockedFeatureTooltip] = useState(null);
  const lockedTimerRef = useRef(null);

  const handleLockedBadgeEnter = (e, flagKey) => {
    if (lockedTimerRef.current) {
      clearTimeout(lockedTimerRef.current);
      lockedTimerRef.current = null;
    }
    const requirement = getFeatureRequirement(flagKey);
    if (!requirement) return;
    const rect = e.currentTarget.getBoundingClientRect();
    setLockedFeatureTooltip({ requirement, rect, key: flagKey });
  };

  const handleLockedBadgeLeave = () => {
    lockedTimerRef.current = setTimeout(() => {
      setLockedFeatureTooltip(null);
    }, 180);
  };

  // Drag-to-scroll and horizontal scrolling state for table
  const tableWrapperRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);
  const [startX, setStartX] = useState(0);
  const [scrollLeftState, setScrollLeftState] = useState(0);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(false);

  const updateScrollState = useCallback(() => {
    const el = tableWrapperRef.current;
    if (!el) return;
    const scrollLeft = el.scrollLeft;
    const maxScroll = el.scrollWidth - el.clientWidth;
    setCanScrollLeft(scrollLeft > 6);
    setCanScrollRight(maxScroll > 6 && scrollLeft < maxScroll - 6);
  }, []);

  useEffect(() => {
    const timer = setTimeout(updateScrollState, 60);
    const el = tableWrapperRef.current;
    if (el) {
      el.addEventListener('scroll', updateScrollState, { passive: true });
    }
    window.addEventListener('resize', updateScrollState);
    return () => {
      clearTimeout(timer);
      if (el) el.removeEventListener('scroll', updateScrollState);
      window.removeEventListener('resize', updateScrollState);
    };
  }, [preview, fileType, updateScrollState]);

  const handlePointerDown = (e) => {
    if (e.button !== 0 && e.pointerType === 'mouse') return;
    if (['BUTTON', 'SELECT', 'INPUT', 'A'].includes(e.target.tagName)) return;
    const el = tableWrapperRef.current;
    if (!el) return;

    setIsDragging(true);
    setStartX(e.clientX);
    setScrollLeftState(el.scrollLeft);

    try {
      e.currentTarget.setPointerCapture(e.pointerId);
    } catch (err) {}
  };

  const handlePointerMove = (e) => {
    if (!isDragging) return;
    const el = tableWrapperRef.current;
    if (!el) return;

    const deltaX = e.clientX - startX;
    el.scrollLeft = scrollLeftState - deltaX;
  };

  const handlePointerUp = (e) => {
    if (isDragging) {
      setIsDragging(false);
      try {
        e.currentTarget.releasePointerCapture(e.pointerId);
      } catch (err) {}
    }
  };

  const scrollTable = (direction) => {
    const el = tableWrapperRef.current;
    if (!el) return;
    const distance = 360;
    el.scrollBy({
      left: direction === 'left' ? -distance : distance,
      behavior: 'smooth'
    });
  };

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
    if (!isLoggedIn) {
      setMessage({ type: 'error', text: 'Please sign in to your account before uploading dataset files.' });
      return;
    }
    if (!file || !file.name.endsWith('.csv')) {
      setMessage({ type: 'error', text: 'Please upload a .csv file' });
      return;
    }
    setUploading(true);
    setMessage(null);
    const startTime = Date.now();
    try {
      const result = await api.previewUpload(file);
      // Ensure smooth visible processing rotation so the user gets clear visual feedback
      const elapsed = Date.now() - startTime;
      if (elapsed < 600) {
        await new Promise(r => setTimeout(r, 600 - elapsed));
      }
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
        refreshMapping?.();
        if (onFlagsUpdate && newStatus?.feature_flags) onFlagsUpdate(newStatus.feature_flags);
        if (isLoggedIn && updateUserState) updateUserState({ has_data: true });
      }
    } catch (e) {
      setMessage({ type: 'error', text: 'Import failed: ' + e.message });
    }
    setImporting(false);
  }

  async function handleReset() {
    const confirmed = await confirmDialog({
      title: 'SmartMart AI',
      subtitle: 'Reset Confirmation',
      message: 'This will delete ALL data. Are you sure?',
      confirmText: 'OK',
      cancelText: 'Cancel',
      isDanger: true,
      icon: '🗑️',
    });
    if (!confirmed) return;
    try {
      await api.resetData();
      setMessage({ type: 'success', text: 'All data cleared' });
      setPreview(null);
      const newStatus = await loadStatus();
      refreshMapping?.();
      if (onFlagsUpdate && newStatus?.feature_flags) {
        onFlagsUpdate(newStatus.feature_flags);
      }
      if (isLoggedIn && updateUserState) updateUserState({ has_data: false });
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
        refreshMapping?.();
        if (onFlagsUpdate && newStatus?.feature_flags) onFlagsUpdate(newStatus.feature_flags);
        if (isLoggedIn && updateUserState) updateUserState({ has_data: true });
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
            <div className="card-title" style={{ marginTop: 16, fontSize: 13 }}>
              Available Features
              <span style={{ fontSize: 11, fontWeight: 400, color: 'var(--text-muted)', marginLeft: 8 }}>
                (Hover over locked 🔒 features to see data &amp; column requirements)
              </span>
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {Object.entries(flags).filter(([k]) => k.startsWith('enable_')).map(([k, v]) => {
                const isLocked = !v;
                return (
                  <span
                    key={k}
                    className={`badge ${v ? 'green' : 'red'}`}
                    style={{
                      fontSize: 12,
                      padding: '4px 10px',
                      cursor: isLocked ? 'help' : 'default',
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: 4,
                    }}
                    onMouseEnter={(e) => isLocked && handleLockedBadgeEnter(e, k)}
                    onMouseLeave={() => isLocked && handleLockedBadgeLeave()}
                  >
                    <span>{v ? '✓' : '🔒'}</span>
                    <span>{k.replace('enable_', '').replace(/_/g, ' ')}</span>
                  </span>
                );
              })}
            </div>

            <div style={{ marginTop: 20, display: 'flex', gap: 10, flexWrap: 'wrap' }}>
              {onNavigateToDashboard && (
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={onNavigateToDashboard}
                  style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}
                >
                  📊 Go to Dashboard
                </button>
              )}
              <button
                type="button"
                className="btn btn-primary"
                onClick={handleLoadDemo}
                disabled={importing}
                style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}
              >
                {importing ? (
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                    <span className="upload-spinner-inline">⏳</span> Loading...
                  </span>
                ) : '🚀 Load Demo Data'}
              </button>
              <button className="btn btn-secondary" onClick={handleReset}>🗑️ Reset All Data</button>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setShowSampleModal(true)}
                style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}
              >
                📁 View Sample Data
              </button>
            </div>
          </>
        ) : (
          <div style={{ textAlign: 'center', padding: '30px 0' }}>
            <div style={{ fontSize: 48, marginBottom: 12 }}>📭</div>
            <p style={{ color: 'var(--text-secondary)', marginBottom: 20 }}>No data loaded. Upload your CSV files or load the demo dataset.</p>
            <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap', alignItems: 'center' }}>
              <button className="btn btn-primary" onClick={handleLoadDemo} disabled={importing}
                style={{ padding: '12px 30px', fontSize: 15 }}>
                {importing ? (
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
                    <span className="upload-spinner-inline">⏳</span> Loading...
                  </span>
                ) : '🚀 Load Demo Dataset'}
              </button>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setShowSampleModal(true)}
                style={{ padding: '12px 24px', fontSize: 15, display: 'inline-flex', alignItems: 'center', gap: 8 }}
              >
                📁 View Sample Data
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Upload Area */}
      {!preview && (
        <div className="card" style={{ marginBottom: 24 }}>
          <div className="card-title">Upload CSV File</div>
          <div
            className={`upload-dropzone ${dragOver ? 'drag-over' : ''} ${uploading ? 'uploading' : ''}`}
            onDragOver={e => {
              e.preventDefault();
              if (!uploading) setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={uploading ? e => e.preventDefault() : handleDrop}
            onClick={() => {
              if (!uploading) document.getElementById('csv-file-input')?.click();
            }}
          >
            {uploading ? (
              <div className="upload-processing-state">
                <div className="upload-icon upload-spinner" title="Processing data...">⏳</div>
                <div className="upload-text">
                  <strong style={{ color: 'var(--accent-blue)' }}>Processing dataset...</strong>
                  <span>Analyzing columns and previewing data</span>
                </div>
              </div>
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
              onChange={handleFileInput} disabled={uploading} />
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
            <button className="btn btn-secondary" onClick={() => setPreview(null)} disabled={importing}>✕ Cancel</button>
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
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(min(240px, 100%), 1fr))', gap: 10, marginBottom: 20 }}>
            {INTERNAL_FIELDS[fileType]?.map(field => {
              const isAutoDetected = mapping[field] && mapping[field] === preview.detected_mapping?.[field];
              return (
                <div key={field} className="mapping-row">
                  <label className="mapping-label">
                    {field.replace(/_/g, ' ')}
                    {isAutoDetected && <span className="auto-badge">auto</span>}
                  </label>
                  <select className="filter-select" style={{ width: '100%', minWidth: 0, maxWidth: '100%' }}
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

          {/* Data Preview Header & Table */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10, flexWrap: 'wrap', gap: 10 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
              <div className="card-title" style={{ fontSize: 13, marginBottom: 0 }}>Data Preview (first 10 rows)</div>
              <span className="badge blue" style={{ fontSize: 11, padding: '2px 8px' }}>
                {preview.columns?.length || 0} columns
              </span>
              <span style={{ fontSize: 12, color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: 4 }}>
                <span style={{ color: 'var(--accent-blue)', fontWeight: 700 }}>↔</span> Click & drag table right/left or use scrollbar
              </span>
            </div>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => scrollTable('left')}
                disabled={!canScrollLeft}
                style={{
                  padding: '4px 12px',
                  fontSize: 12,
                  opacity: canScrollLeft ? 1 : 0.4,
                  cursor: canScrollLeft ? 'pointer' : 'default',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 4
                }}
                title="Scroll left to see previous columns"
              >
                ◀ Left
              </button>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => scrollTable('right')}
                disabled={!canScrollRight}
                style={{
                  padding: '4px 12px',
                  fontSize: 12,
                  opacity: canScrollRight ? 1 : 0.4,
                  cursor: canScrollRight ? 'pointer' : 'default',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 4
                }}
                title="Scroll right to see next columns"
              >
                Right ▶
              </button>
            </div>
          </div>

          <div className="table-drag-container">
            {canScrollLeft && (
              <div className="table-scroll-fade left" onClick={() => scrollTable('left')} title="Click to scroll left">
                <span style={{ color: 'var(--accent-blue)', fontSize: 14 }}>◀</span>
              </div>
            )}
            {canScrollRight && (
              <div className="table-scroll-fade right" onClick={() => scrollTable('right')} title="Click to scroll right">
                <span style={{ color: 'var(--accent-blue)', fontSize: 14 }}>▶</span>
              </div>
            )}
            <div
              ref={tableWrapperRef}
              className={`table-wrapper table-draggable ${isDragging ? 'is-dragging' : ''}`}
              style={{ maxHeight: 300, cursor: isDragging ? 'grabbing' : 'grab' }}
              onPointerDown={handlePointerDown}
              onPointerMove={handlePointerMove}
              onPointerUp={handlePointerUp}
              onPointerCancel={handlePointerUp}
            >
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
          </div>

          {/* Import Button */}
          <div style={{ marginTop: 20, display: 'flex', gap: 10, justifyContent: 'flex-end', flexWrap: 'wrap' }}>
            <button className="btn btn-secondary" onClick={() => setPreview(null)} disabled={importing}>Cancel</button>
            <button className="btn btn-primary" onClick={handleImport} disabled={importing}
              style={{ padding: '10px 30px' }}>
              {importing ? (
                <span style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
                  <span className="upload-spinner-inline">⏳</span>
                  <span>Importing &amp; Training ML...</span>
                </span>
              ) : (
                `📥 Import ${preview.total_rows?.toLocaleString()} rows as ${fileType}`
              )}
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

      {/* Sample Data Modal */}
      <SampleDataModal
        isOpen={showSampleModal}
        onClose={() => setShowSampleModal(false)}
        onLoadDemo={handleLoadDemo}
        importing={importing}
      />

      {/* Floating Locked Feature Requirement Popover */}
      {lockedFeatureTooltip && (
        <LockedFeaturePopover
          requirement={lockedFeatureTooltip.requirement}
          targetRect={lockedFeatureTooltip.rect}
          isOpen={Boolean(lockedFeatureTooltip)}
          onMouseEnterPopover={() => {
            if (lockedTimerRef.current) {
              clearTimeout(lockedTimerRef.current);
              lockedTimerRef.current = null;
            }
          }}
          onMouseLeavePopover={() => setLockedFeatureTooltip(null)}
          placement="bottom"
        />
      )}
    </div>
  );
}
