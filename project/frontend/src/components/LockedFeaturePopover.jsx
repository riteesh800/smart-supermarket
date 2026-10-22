import React, { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';

/**
 * LockedFeaturePopover
 *
 * Renders a rich, floating portal popover whenever a user hovers over
 * a locked feature in the sidebar or an unavailable feature badge.
 * Displays the required dataset, schema requirements, column names,
 * and data types needed to unlock the feature.
 */
export default function LockedFeaturePopover({
  requirement,
  targetRect,
  isOpen,
  onMouseEnterPopover,
  onMouseLeavePopover,
  onNavigate,
  placement = 'right',
}) {
  const popoverRef = useRef(null);
  const [coords, setCoords] = useState({ top: 0, left: 0, arrowTop: 20 });

  useEffect(() => {
    if (!isOpen || !targetRect) return;

    const popoverWidth = 460;
    const estimatedHeight = 440;
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;

    let left = 0;
    let top = 0;
    let arrowTop = 24;

    if (placement === 'right') {
      left = targetRect.right + 12;

      // If overflowing right window boundary, try left side of trigger
      if (left + popoverWidth > viewportWidth - 16) {
        left = Math.max(12, targetRect.left - popoverWidth - 12);
      }

      // Vertically align with trigger top, but clamp inside viewport
      const targetCenterY = targetRect.top + targetRect.height / 2;
      top = targetRect.top - 12;

      // Clamp so popover does not overflow bottom of viewport
      if (top + estimatedHeight > viewportHeight - 16) {
        top = Math.max(16, viewportHeight - estimatedHeight - 16);
      }
      if (top < 12) {
        top = 12;
      }

      // Calculate arrow position pointing directly to the middle of the trigger
      arrowTop = Math.max(16, Math.min(estimatedHeight - 24, targetCenterY - top));
    } else {
      // Top or bottom placement (e.g. for badges in DataSetupPanel)
      left = targetRect.left + targetRect.width / 2 - popoverWidth / 2;
      if (left < 12) left = 12;
      if (left + popoverWidth > viewportWidth - 12) {
        left = viewportWidth - popoverWidth - 12;
      }

      // Check if space below or above
      if (targetRect.bottom + estimatedHeight + 16 <= viewportHeight) {
        top = targetRect.bottom + 10;
      } else {
        top = Math.max(12, targetRect.top - estimatedHeight - 10);
      }
    }

    setCoords({ top, left, arrowTop });
  }, [isOpen, targetRect, placement]);

  if (!isOpen || !requirement) return null;

  const dataset = requirement.dataset || {};
  const columns = requirement.columns || [];

  return createPortal(
    <div
      ref={popoverRef}
      className="locked-popover-portal"
      style={{
        top: `${coords.top}px`,
        left: `${coords.left}px`,
      }}
      onMouseEnter={onMouseEnterPopover}
      onMouseLeave={onMouseLeavePopover}
      role="tooltip"
      aria-label={`Unlock requirements for ${requirement.title}`}
    >
      {/* Arrow indicator */}
      {placement === 'right' && (
        <div
          className="locked-popover-arrow"
          style={{ top: `${coords.arrowTop}px` }}
        />
      )}

      {/* Header */}
      <div className="locked-popover-header">
        <div className="locked-popover-title-row">
          <div className="locked-popover-title">
            <span className="locked-popover-icon">{requirement.icon || '🔒'}</span>
            <h4>{requirement.title}</h4>
          </div>
          <span className="locked-status-badge">
            <span className="lock-icon">🔒</span> Feature Locked
          </span>
        </div>
        <p className="locked-popover-summary">{requirement.summary}</p>
      </div>

      {/* Required Dataset Box */}
      <div className="locked-popover-dataset">
        <div className="locked-dataset-label">Data Needed To Unlock:</div>
        <div className="locked-dataset-card">
          <span className="locked-dataset-icon">{dataset.icon || '📁'}</span>
          <div className="locked-dataset-info">
            <div className="locked-dataset-name">
              <strong>{dataset.name || 'Dataset'}</strong>
              {dataset.filename && <code className="locked-dataset-file">{dataset.filename}</code>}
            </div>
            {dataset.description && (
              <div className="locked-dataset-desc">{dataset.description}</div>
            )}
            {dataset.alternative && (
              <div className="locked-dataset-alt">💡 {dataset.alternative}</div>
            )}
          </div>
        </div>
      </div>

      {/* Required Columns & Data Types */}
      <div className="locked-popover-columns-section">
        <div className="locked-columns-header">
          <span>Required Columns &amp; Data Types</span>
          <span className="locked-col-count">{columns.length} columns defined</span>
        </div>

        <div className="locked-columns-table-wrapper">
          <table className="locked-columns-table">
            <thead>
              <tr>
                <th>Column Name</th>
                <th>Data Type</th>
                <th>Status</th>
                <th>Description / Example</th>
              </tr>
            </thead>
            <tbody>
              {columns.map((col) => {
                const typeClass = col.type.toLowerCase().includes('int')
                  ? 'type-int'
                  : col.type.toLowerCase().includes('float') || col.type.toLowerCase().includes('currency')
                  ? 'type-float'
                  : col.type.toLowerCase().includes('date') || col.type.toLowerCase().includes('time')
                  ? 'type-date'
                  : 'type-string';

                return (
                  <tr key={col.name}>
                    <td className="locked-col-name">
                      <code>{col.name}</code>
                    </td>
                    <td>
                      <span className={`locked-type-pill ${typeClass}`}>
                        {col.type}
                      </span>
                    </td>
                    <td>
                      <span className={`locked-req-pill ${col.required ? 'required' : 'optional'}`}>
                        {col.required ? 'Required' : 'Optional'}
                      </span>
                    </td>
                    <td className="locked-col-desc">
                      <div>{col.desc}</div>
                      {col.example && (
                        <div className="locked-col-example">
                          e.g. <code>{col.example}</code>
                        </div>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Footer & Quick Navigation */}
      <div className="locked-popover-footer">
        <div className="locked-footer-hint">
          <span>💡 Upload your CSV or click <strong>Load Demo Dataset</strong> in Data Setup.</span>
        </div>
        {onNavigate && (
          <button
            type="button"
            className="btn btn-primary locked-goto-btn"
            onClick={() => onNavigate('datasetup')}
          >
            <span>📁</span> Open Data Setup
          </button>
        )}
      </div>
    </div>,
    document.body
  );
}
