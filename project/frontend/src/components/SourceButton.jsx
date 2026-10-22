import React, { useState, useRef, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { useColumnMapping } from '../context/ColumnMappingContext';

/**
 * Enhanced SourceButton Component
 *
 * Displays a sleek "Source" pill button. When hovered or clicked, opens a rich
 * popover showing:
 * 1. What the feature is and what it shows
 * 2. How it is calculated (with dynamic column names) & its business use
 * 3. The currently existing Data Source & Columns section (with dynamic column names)
 *
 * @param {Object|Array} sources - Feature metadata object or legacy array of source definitions
 * @param {Object} [info] - Alternative prop for feature metadata object
 */
export default function SourceButton({ sources, info }) {
  const [isOpen, setIsOpen] = useState(false);
  const [isPinned, setIsPinned] = useState(false);
  const [coords, setCoords] = useState({ top: 0, left: 0, placement: 'bottom' });

  const buttonRef = useRef(null);
  const popoverRef = useRef(null);
  const closeTimeoutRef = useRef(null);

  const { resolveColumns, renderDynamicText } = useColumnMapping();

  // Extract metadata cleanly whether passed as object or array
  const rawData = info || sources || {};
  const isLegacyArray = Array.isArray(rawData);

  const feature = isLegacyArray ? { sources: rawData } : rawData;
  const title = feature.title || '';
  const whatItShows = feature.whatItShows || '';
  const howItCalculated = feature.howItCalculated || '';
  const useCase = feature.useCase || '';
  const sourceList = Array.isArray(feature.sources) ? feature.sources : [];

  const updatePosition = useCallback(() => {
    if (!buttonRef.current) return;
    const rect = buttonRef.current.getBoundingClientRect();

    const popoverWidth = Math.min(420, window.innerWidth - 24);
    const popoverHeight = 440; // estimated

    // Center horizontally on button if possible, but clamp within window
    let left = rect.left + rect.width / 2 - popoverWidth / 2;
    if (left < 12) {
      left = 12;
    } else if (left + popoverWidth > window.innerWidth - 16) {
      left = window.innerWidth - popoverWidth - 16;
    }

    // Default to placing below button
    let top = rect.bottom + 8;
    let placement = 'bottom';

    // If bottom overflow and space available above, place above
    if (rect.bottom + popoverHeight > window.innerHeight && rect.top > popoverHeight + 20) {
      top = rect.top - popoverHeight - 8;
      placement = 'top';
    }

    setCoords({ top, left, placement });
  }, []);

  const handleMouseEnter = () => {
    if (closeTimeoutRef.current) {
      clearTimeout(closeTimeoutRef.current);
      closeTimeoutRef.current = null;
    }
    updatePosition();
    setIsOpen(true);
  };

  const handleMouseLeave = () => {
    if (isPinned) return; // do not close on hover-out if pinned
    closeTimeoutRef.current = setTimeout(() => {
      setIsOpen(false);
    }, 220); // Grace period to move cursor into popover
  };

  const handlePopoverMouseEnter = () => {
    if (closeTimeoutRef.current) {
      clearTimeout(closeTimeoutRef.current);
      closeTimeoutRef.current = null;
    }
  };

  const handlePopoverMouseLeave = () => {
    if (isPinned) return;
    closeTimeoutRef.current = setTimeout(() => {
      setIsOpen(false);
    }, 220);
  };

  const handleClick = (e) => {
    e.stopPropagation();
    if (!isOpen) {
      updatePosition();
      setIsOpen(true);
      setIsPinned(true);
    } else {
      // If already open, toggle pin state or close
      if (isPinned) {
        setIsPinned(false);
        setIsOpen(false);
      } else {
        setIsPinned(true);
      }
    }
  };

  const handleClose = (e) => {
    e.stopPropagation();
    setIsPinned(false);
    setIsOpen(false);
  };

  // Close when clicking outside or pressing Escape if pinned
  useEffect(() => {
    if (!isOpen) return;

    function handleDocClick(e) {
      if (
        popoverRef.current &&
        !popoverRef.current.contains(e.target) &&
        buttonRef.current &&
        !buttonRef.current.contains(e.target)
      ) {
        setIsPinned(false);
        setIsOpen(false);
      }
    }

    function handleKeyDown(e) {
      if (e.key === 'Escape') {
        setIsPinned(false);
        setIsOpen(false);
      }
    }

    function handleScrollOrResize() {
      if (!isPinned) {
        setIsOpen(false);
      } else {
        updatePosition();
      }
    }

    document.addEventListener('mousedown', handleDocClick);
    document.addEventListener('keydown', handleKeyDown);
    window.addEventListener('scroll', handleScrollOrResize, true);
    window.addEventListener('resize', handleScrollOrResize);
    return () => {
      document.removeEventListener('mousedown', handleDocClick);
      document.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('scroll', handleScrollOrResize, true);
      window.removeEventListener('resize', handleScrollOrResize);
      if (closeTimeoutRef.current) clearTimeout(closeTimeoutRef.current);
    };
  }, [isOpen, isPinned, updatePosition]);

  const hasExtraContent = Boolean(whatItShows || howItCalculated || useCase);

  return (
    <>
      <button
        ref={buttonRef}
        type="button"
        className={`source-btn ${isOpen ? 'active' : ''} ${isPinned ? 'pinned' : ''}`}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        onClick={handleClick}
        aria-label={`View data source and calculation logic for ${title || 'feature'}`}
        aria-expanded={isOpen}
      >
        <span className="source-btn-icon">ℹ️</span>
        <span className="source-btn-text">Source</span>
      </button>

      {isOpen && (sourceList.length > 0 || hasExtraContent) && createPortal(
        <div
          ref={popoverRef}
          className="source-tooltip-portal rich-source-popover"
          style={{
            top: `${coords.top}px`,
            left: `${coords.left}px`,
          }}
          onMouseEnter={handlePopoverMouseEnter}
          onMouseLeave={handlePopoverMouseLeave}
          role="dialog"
          aria-label={title || 'Feature Source Details'}
        >
          {/* Header */}
          <div className="source-popover-header">
            <div className="source-popover-title-row">
              <span className="source-badge">Feature Intelligence</span>
              {isPinned && <span className="source-pin-badge">📌 Pinned</span>}
              <button
                type="button"
                className="source-close-btn"
                onClick={handleClose}
                aria-label="Close details"
              >
                ✕
              </button>
            </div>
            {title && <h4 className="source-feature-title">{title}</h4>}
          </div>

          <div className="source-popover-body">
            {/* 1. FIRST: What is this feature and what it shows */}
            {whatItShows && (
              <div className="source-section source-section-what">
                <div className="source-section-header">
                  <span className="source-section-icon">👁️</span>
                  <span className="source-section-title">What this feature shows</span>
                </div>
                <div className="source-section-content">
                  <p>{renderDynamicText(whatItShows)}</p>
                </div>
              </div>
            )}

            {/* 2. NEXT: How it is calculated and what is the use of this */}
            {(howItCalculated || useCase) && (
              <div className="source-section source-section-calc">
                <div className="source-section-header">
                  <span className="source-section-icon">🧮</span>
                  <span className="source-section-title">How It Is Calculated &amp; Business Use</span>
                </div>
                <div className="source-section-content">
                  {howItCalculated && (
                    <div className="source-calc-subblock">
                      <div className="source-sublabel">Calculation &amp; Logic:</div>
                      <div className="source-formula-box">
                        {renderDynamicText(howItCalculated)}
                      </div>
                    </div>
                  )}

                  {useCase && (
                    <div className="source-use-subblock">
                      <div className="source-sublabel">Business Purpose &amp; Action:</div>
                      <p className="source-use-text">{renderDynamicText(useCase)}</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* 3. NEXT: Keep the currently existed thing (Data Source & Columns) */}
            {sourceList && sourceList.length > 0 && (
              <div className="source-section source-section-data">
                <div className="source-section-header">
                  <span className="source-section-icon">🗄️</span>
                  <span className="source-section-title">Data Source &amp; Columns</span>
                </div>
                <div className="source-section-content">
                  {sourceList.map((src, idx) => {
                    const resolvedCols = resolveColumns(src.file, src.columns);
                    return (
                      <div key={idx} className="source-item">
                        <div className="source-filename-row">
                          <span className="source-file-icon">📄</span>
                          <span className="source-filename">{src.file}</span>
                        </div>
                        <div className="source-columns-list">
                          {resolvedCols.map((colName, cIdx) => (
                            <span key={cIdx} className="source-col-chip">
                              {colName}
                            </span>
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>

          {/* Footer note */}
          <div className="source-popover-footer">
            <span className="source-footer-hint">
              💡 Column names automatically adapt to your uploaded dataset mappings.
            </span>
          </div>
        </div>,
        document.body
      )}
    </>
  );
}
