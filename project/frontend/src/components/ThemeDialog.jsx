import React, { useState, useEffect } from 'react';

let dialogHandler = null;

/**
 * Open a theme-matching confirmation dialog in the center of the screen.
 * Resolves to true if confirmed (OK), false if cancelled.
 */
export function confirmDialog(options) {
  const opts = typeof options === 'string' ? { message: options } : options;
  if (dialogHandler) {
    return dialogHandler.openConfirm(opts);
  }
  return Promise.resolve(window.confirm(opts.message));
}

/**
 * Open a theme-matching alert dialog in the center of the screen.
 * Resolves when dismissed.
 */
export function alertDialog(options) {
  const opts = typeof options === 'string' ? { message: options } : options;
  if (dialogHandler) {
    return dialogHandler.openAlert(opts);
  }
  window.alert(opts.message);
  return Promise.resolve();
}

export default function ThemeDialog() {
  const [dialog, setDialog] = useState(null);

  useEffect(() => {
    dialogHandler = {
      openConfirm: (opts) =>
        new Promise((resolve) => {
          setDialog({
            type: 'confirm',
            title: opts.title || 'SmartMart AI',
            subtitle: opts.subtitle || 'Confirmation',
            message: opts.message || '',
            confirmText: opts.confirmText || 'OK',
            cancelText: opts.cancelText || 'Cancel',
            isDanger: opts.isDanger !== undefined ? opts.isDanger : true,
            icon: opts.icon || (opts.isDanger ? '⚠️' : '❓'),
            onConfirm: () => {
              setDialog(null);
              resolve(true);
            },
            onCancel: () => {
              setDialog(null);
              resolve(false);
            },
          });
        }),
      openAlert: (opts) =>
        new Promise((resolve) => {
          setDialog({
            type: 'alert',
            title: opts.title || 'SmartMart AI',
            subtitle: opts.subtitle || 'Notification',
            message: opts.message || '',
            confirmText: opts.confirmText || 'OK',
            icon: opts.icon || (opts.type === 'error' ? '❌' : opts.type === 'success' ? '✅' : 'ℹ️'),
            isDanger: opts.type === 'error',
            onConfirm: () => {
              setDialog(null);
              resolve(true);
            },
            onCancel: () => {
              setDialog(null);
              resolve(false);
            },
          });
        }),
    };

    // Safely bridge native window.alert to our theme dialog so no browser alert popup appears
    const originalAlert = window.alert;
    window.alert = (msg) => {
      if (dialogHandler) {
        dialogHandler.openAlert({ message: String(msg) });
      } else {
        originalAlert(msg);
      }
    };

    return () => {
      dialogHandler = null;
      window.alert = originalAlert;
    };
  }, []);

  // Keyboard accessibility: Escape cancels, Enter confirms
  useEffect(() => {
    if (!dialog) return;
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        dialog.onCancel();
      } else if (e.key === 'Enter') {
        e.preventDefault();
        dialog.onConfirm();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [dialog]);

  if (!dialog) return null;

  return (
    <div
      className="theme-dialog-overlay"
      onClick={dialog.onCancel}
      role="dialog"
      aria-modal="true"
    >
      <div
        className="theme-dialog-box"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="theme-dialog-header">
          <div className="theme-dialog-title-wrap">
            <span className="theme-dialog-icon">{dialog.icon}</span>
            <div className="theme-dialog-title-text">
              <span className="theme-dialog-origin">{dialog.title}</span>
              {dialog.subtitle && (
                <span className="theme-dialog-subtitle">{dialog.subtitle}</span>
              )}
            </div>
          </div>
          <button
            type="button"
            className="theme-dialog-close"
            onClick={dialog.onCancel}
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        <div className="theme-dialog-body">
          <p>{dialog.message}</p>
        </div>

        <div className="theme-dialog-actions">
          {dialog.type === 'confirm' && (
            <button
              type="button"
              className="btn btn-secondary theme-dialog-btn"
              onClick={dialog.onCancel}
            >
              {dialog.cancelText}
            </button>
          )}
          <button
            type="button"
            className={`btn ${dialog.isDanger ? 'btn-danger' : 'btn-primary'} theme-dialog-btn`}
            onClick={dialog.onConfirm}
            autoFocus
          >
            {dialog.confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}
