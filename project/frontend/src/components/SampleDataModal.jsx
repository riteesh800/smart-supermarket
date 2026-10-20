import React, { useState, useEffect } from 'react';
import { api } from '../services/api';

export default function SampleDataModal({ isOpen, onClose, onLoadDemo, importing }) {
  const [datasets, setDatasets] = useState([]);
  const [selectedId, setSelectedId] = useState('sales');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [downloadingId, setDownloadingId] = useState(null);

  useEffect(() => {
    if (!isOpen) return;
    let isMounted = true;
    setLoading(true);
    setError(null);

    api.getSampleDatasets()
      .then((data) => {
        if (isMounted) {
          setDatasets(data);
          if (data && data.length > 0 && !data.find(d => d.id === selectedId)) {
            setSelectedId(data[0].id);
          }
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError('Failed to load sample datasets: ' + err.message);
          setLoading(false);
        }
      });

    return () => { isMounted = false; };
  }, [isOpen]);

  // Handle escape key
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const currentDataset = datasets.find((d) => d.id === selectedId) || datasets[0];

  const handleDownload = (filename) => {
    setDownloadingId(filename);
    const downloadUrl = api.getSampleDownloadUrl(filename);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    setTimeout(() => setDownloadingId(null), 800);
  };

  const handleDownloadAll = async () => {
    for (const item of datasets) {
      handleDownload(item.filename);
      await new Promise((r) => setTimeout(r, 350));
    }
  };

  return (
    <div className="sample-modal-overlay" onClick={onClose} role="dialog" aria-modal="true">
      <div className="sample-modal-box" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="sample-modal-header">
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <span style={{ fontSize: 24 }}>📁</span>
              <h3 style={{ margin: 0, fontSize: 20, fontWeight: 700, color: 'var(--text-primary)' }}>
                Sample Retail Datasets
              </h3>
              <span className="badge blue" style={{ fontSize: 11, padding: '3px 8px' }}>
                5 Files Available
              </span>
            </div>
            <p style={{ margin: '6px 0 0 0', fontSize: 13, color: 'var(--text-secondary)' }}>
              Explore the 5 built-in supermarket CSV datasets or download them individually for custom inspection and testing.
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            {datasets.length > 0 && (
              <button
                type="button"
                className="btn btn-secondary"
                onClick={handleDownloadAll}
                style={{ padding: '8px 14px', fontSize: 12, display: 'inline-flex', alignItems: 'center', gap: 6 }}
                title="Download all 5 CSV files to your computer"
              >
                <span>📦</span> Download All 5 CSVs
              </button>
            )}
            <button
              type="button"
              className="theme-dialog-close"
              onClick={onClose}
              aria-label="Close"
              style={{ fontSize: 18, padding: '6px 10px' }}
            >
              ✕
            </button>
          </div>
        </div>

        {loading ? (
          <div className="loading" style={{ minHeight: 300 }}>
            <span className="upload-spinner-inline" style={{ marginRight: 8, fontSize: 20 }}>⏳</span>
            Loading sample dataset catalogs...
          </div>
        ) : error ? (
          <div style={{ padding: 40, textAlign: 'center', color: 'var(--accent-red)' }}>
            <div style={{ fontSize: 32, marginBottom: 10 }}>⚠️</div>
            <p>{error}</p>
            <button className="btn btn-secondary" onClick={onClose} style={{ marginTop: 12 }}>
              Close
            </button>
          </div>
        ) : (
          <>
            {/* 5 Dataset Tabs */}
            <div className="sample-tabs">
              {datasets.map((item) => {
                const isActive = item.id === (currentDataset?.id || selectedId);
                return (
                  <button
                    key={item.id}
                    type="button"
                    className={`sample-tab ${isActive ? 'active' : ''}`}
                    onClick={() => setSelectedId(item.id)}
                  >
                    <span className="sample-tab-icon">{item.icon}</span>
                    <div className="sample-tab-text">
                      <span className="sample-tab-filename">{item.filename}</span>
                      <span className="sample-tab-meta">
                        {item.total_rows.toLocaleString()} rows • {item.size_formatted}
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>

            {/* Selected File Details Banner */}
            {currentDataset && (
              <div className="sample-file-banner">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 14 }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                      <span style={{ fontSize: 20 }}>{currentDataset.icon}</span>
                      <strong style={{ fontSize: 16, color: 'var(--text-primary)' }}>
                        {currentDataset.name} ({currentDataset.filename})
                      </strong>
                      <span className="badge green" style={{ fontSize: 11 }}>
                        {currentDataset.total_rows.toLocaleString()} rows
                      </span>
                      <span className="badge purple" style={{ fontSize: 11 }}>
                        {currentDataset.size_formatted}
                      </span>
                      <span className="badge orange" style={{ fontSize: 11 }}>
                        {currentDataset.columns.length} columns
                      </span>
                    </div>
                    <p style={{ margin: 0, fontSize: 13, color: 'var(--text-secondary)', maxWidth: 640, lineHeight: 1.5 }}>
                      {currentDataset.description}
                    </p>
                  </div>

                  <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                    <button
                      type="button"
                      className="btn btn-primary"
                      onClick={() => handleDownload(currentDataset.filename)}
                      disabled={downloadingId === currentDataset.filename}
                      style={{ padding: '9px 18px', fontSize: 13, display: 'inline-flex', alignItems: 'center', gap: 8 }}
                    >
                      <span>{downloadingId === currentDataset.filename ? '⏳' : '⬇️'}</span>
                      {downloadingId === currentDataset.filename ? 'Downloading...' : `Download ${currentDataset.filename}`}
                    </button>
                  </div>
                </div>

                {/* Column schema chips */}
                <div style={{ marginTop: 14 }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 6 }}>
                    Dataset Schema ({currentDataset.columns.length} Fields)
                  </div>
                  <div className="sample-columns-chips">
                    {currentDataset.columns.map((col) => (
                      <span key={col} className="sample-column-chip">
                        {col}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Live Data Preview Table */}
            {currentDataset && (
              <div className="sample-table-section">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)' }}>
                    Data Preview: Showing first {currentDataset.preview_rows.length} rows of {currentDataset.filename}
                  </div>
                  <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                    Scroll horizontally to inspect all columns ↔
                  </span>
                </div>

                <div className="sample-table-wrapper">
                  <table>
                    <thead>
                      <tr>
                        <th style={{ width: 44, textAlign: 'center' }}>#</th>
                        {currentDataset.columns.map((col) => (
                          <th key={col}>{col}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {currentDataset.preview_rows.map((row, idx) => (
                        <tr key={idx}>
                          <td style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: 11 }}>{idx + 1}</td>
                          {currentDataset.columns.map((col) => (
                            <td key={col} style={{ whiteSpace: 'nowrap', fontSize: 12 }}>
                              {String(row[col] ?? '')}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Modal Footer */}
            <div className="sample-modal-footer">
              <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                Tip: You can download any CSV, modify it in Excel, and upload it in the <strong>Upload CSV File</strong> section below.
              </div>
              <div style={{ display: 'flex', gap: 10 }}>
                {onLoadDemo && (
                  <button
                    type="button"
                    className="btn btn-primary"
                    onClick={() => {
                      onClose();
                      onLoadDemo();
                    }}
                    disabled={importing}
                    style={{ padding: '8px 18px', fontSize: 13 }}
                  >
                    🚀 Load Full Dataset
                  </button>
                )}
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={onClose}
                  style={{ padding: '8px 18px', fontSize: 13 }}
                >
                  Close
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
