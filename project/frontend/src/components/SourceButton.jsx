import React, { useState, useRef } from 'react';
import { createPortal } from 'react-dom';

/**
 * SourceButton component that displays a sleek "Source" pill button.
 * On mouse hover, shows a tooltip listing the referenced CSV file name(s)
 * and only the columns used in that feature representation.
 *
 * @param {Array<{file: string, columns: string[] | string}>} sources
 */
export default function SourceButton({ sources = [] }) {
  const [isOpen, setIsOpen] = useState(false);
  const [coords, setCoords] = useState({ top: 0, left: 0 });
  const buttonRef = useRef(null);

  const handleMouseEnter = () => {
    if (buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect();
      const scrollX = window.scrollX || window.pageXOffset;
      const scrollY = window.scrollY || window.pageYOffset;

      let left = rect.left + scrollX;
      // Prevent tooltip overflow past right edge of window
      if (rect.left + 300 > window.innerWidth) {
        left = Math.max(12, window.innerWidth - 320 + scrollX);
      }

      let top = rect.bottom + scrollY + 6;
      // If close to bottom of viewport, position above button
      if (rect.bottom + 180 > window.innerHeight && rect.top > 160) {
        top = rect.top + scrollY - 8;
      }

      setCoords({ top, left });
    }
    setIsOpen(true);
  };

  const handleMouseLeave = () => {
    setIsOpen(false);
  };

  return (
    <>
      <button
        ref={buttonRef}
        type="button"
        className="source-btn"
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        aria-label="View data source and columns"
      >
        Source
      </button>

      {isOpen && sources && sources.length > 0 && createPortal(
        <div
          className="source-tooltip-portal"
          style={{
            top: `${coords.top}px`,
            left: `${coords.left}px`,
          }}
        >
          {sources.map((src, idx) => (
            <div key={idx} className="source-item">
              <div className="source-filename">{src.file}</div>
              <div className="source-columns">
                {Array.isArray(src.columns) ? src.columns.join(', ') : src.columns}
              </div>
            </div>
          ))}
        </div>,
        document.body
      )}
    </>
  );
}
