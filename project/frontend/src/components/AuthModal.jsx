import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';

export default function AuthModal({ isOpen, onClose, initialTab = 'login', onSuccess }) {
  const { login, register, loginWithGoogle } = useAuth();
  const [tab, setTab] = useState(initialTab); // 'login' | 'register'
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Google Account Picker modal state
  const [showGooglePicker, setShowGooglePicker] = useState(false);
  const [googleEmail, setGoogleEmail] = useState('');
  const [googleName, setGoogleName] = useState('');

  useEffect(() => {
    if (isOpen) {
      setTab(initialTab);
      setError(null);
      setShowGooglePicker(false);
    }
  }, [isOpen, initialTab]);

  if (!isOpen) return null;

  // Auto-suggest name from email if user types email
  const handleEmailChange = (val) => {
    setEmail(val);
    if (!name && val.includes('@')) {
      const prefix = val.split('@')[0];
      const suggested = prefix.replace(/[._-]+/g, ' ').replace(/\d+/g, '').trim();
      if (suggested) {
        setName(suggested.charAt(0).toUpperCase() + suggested.slice(1));
      }
    }
  };

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (tab === 'register') {
        if (!email.trim() || !email.includes('@')) {
          throw new Error('Please enter a valid email address.');
        }
        if (password.length < 4) {
          throw new Error('Password must be at least 4 characters.');
        }
        if (password !== confirmPassword) {
          throw new Error('Passwords do not match.');
        }
        await register(name.trim(), email.trim(), password);
      } else {
        if (!email.trim() || !email.includes('@')) {
          throw new Error('Please enter your email address.');
        }
        if (!password) {
          throw new Error('Please enter your password.');
        }
        await login(email.trim(), password);
      }

      if (onSuccess) onSuccess();
      onClose();
    } catch (err) {
      setError(err.message || 'Authentication failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenGooglePicker = () => {
    // Pre-fill with user email or sample gmail
    const suggested = email.includes('@gmail') ? email : (email ? `${email.split('@')[0]}@gmail.com` : 'user@gmail.com');
    setGoogleEmail(suggested);
    const userPart = suggested.split('@')[0].replace(/[._-]+/g, ' ').replace(/\d+/g, '').trim();
    setGoogleName(userPart ? userPart.charAt(0).toUpperCase() + userPart.slice(1) : 'Google User');
    setShowGooglePicker(true);
  };

  const handleGoogleSubmit = async (selectedEmail, selectedName) => {
    setError(null);
    setLoading(true);
    try {
      const emailToUse = selectedEmail || googleEmail;
      const nameToUse = selectedName || googleName;
      await loginWithGoogle(emailToUse, nameToUse);
      setShowGooglePicker(false);
      if (onSuccess) onSuccess();
      onClose();
    } catch (err) {
      setError(err.message || 'Google Sign-In failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-overlay" onClick={onClose}>
      <div className="auth-modal" onClick={e => e.stopPropagation()}>
        <button className="auth-close-btn" onClick={onClose} aria-label="Close dialog">
          ✕
        </button>

        {!showGooglePicker ? (
          <>
            {/* Modal Header */}
            <div className="auth-header">
              <div className="auth-brand-badge">
                <span className="auth-logo-icon">🏪</span>
                <span>SmartMart AI Intelligence</span>
              </div>
              <h3>{tab === 'login' ? 'Welcome Back' : 'Create an Account'}</h3>
              {tab === 'login' && (
                <p>Sign in to access your saved supermarket data and AI models</p>
              )}
            </div>

            {/* Tab Switcher */}
            <div className="auth-tabs">
              <button
                type="button"
                className={`auth-tab ${tab === 'login' ? 'active' : ''}`}
                onClick={() => { setTab('login'); setError(null); }}
              >
                Sign In
              </button>
              <button
                type="button"
                className={`auth-tab ${tab === 'register' ? 'active' : ''}`}
                onClick={() => { setTab('register'); setError(null); }}
              >
                Register
              </button>
            </div>

            {error && <div className="auth-error-banner">{error}</div>}

            {/* 1-Click Google Auth Option */}
            <div className="auth-social-section">
              <button
                type="button"
                className="google-auth-btn"
                onClick={handleOpenGooglePicker}
                disabled={loading}
              >
                <svg className="google-icon" viewBox="0 0 24 24" width="20" height="20">
                  <path
                    fill="#4285F4"
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                  />
                  <path
                    fill="#34A853"
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  />
                  <path
                    fill="#FBBC05"
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
                  />
                  <path
                    fill="#EA4335"
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
                  />
                </svg>
                <span>{tab === 'login' ? 'Continue with Google' : 'Sign up with Google'}</span>
              </button>
            </div>

            {/* Divider */}
            <div className="auth-divider">
              <span>or continue with email</span>
            </div>

            {/* Email + Password Form */}
            <form onSubmit={handlePasswordSubmit} className="auth-form">
              {tab === 'register' && (
                <div className="auth-field">
                  <label htmlFor="auth-name">Your Name / Username</label>
                  <div className="auth-input-wrapper">
                    <span className="auth-field-icon">👤</span>
                    <input
                      id="auth-name"
                      type="text"
                      placeholder="e.g. Alex Morgan"
                      value={name}
                      onChange={e => setName(e.target.value)}
                    />
                  </div>
                </div>
              )}

              <div className="auth-field">
                <label htmlFor="auth-email">Email Address</label>
                <div className="auth-input-wrapper">
                  <span className="auth-field-icon">✉️</span>
                  <input
                    id="auth-email"
                    type="email"
                    required
                    placeholder="name@example.com"
                    value={email}
                    onChange={e => handleEmailChange(e.target.value)}
                  />
                </div>
              </div>

              <div className="auth-field">
                <label htmlFor="auth-password">Password</label>
                <div className="auth-input-wrapper">
                  <span className="auth-field-icon">🔒</span>
                  <input
                    id="auth-password"
                    type={showPassword ? 'text' : 'password'}
                    required
                    placeholder={tab === 'register' ? 'Choose a password (min 4 chars)' : 'Enter your password'}
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                  />
                  <button
                    type="button"
                    className="auth-password-toggle"
                    onClick={() => setShowPassword(p => !p)}
                    tabIndex="-1"
                  >
                    {showPassword ? '👁️' : '🙈'}
                  </button>
                </div>
              </div>

              {tab === 'register' && (
                <div className="auth-field">
                  <label htmlFor="auth-confirm-password">Confirm Password</label>
                  <div className="auth-input-wrapper">
                    <span className="auth-field-icon">🔑</span>
                    <input
                      id="auth-confirm-password"
                      type={showPassword ? 'text' : 'password'}
                      required
                      placeholder="Re-enter your password"
                      value={confirmPassword}
                      onChange={e => setConfirmPassword(e.target.value)}
                    />
                  </div>
                </div>
              )}

              <button
                type="submit"
                className="auth-submit-btn"
                disabled={loading}
              >
                {loading ? (
                  <span className="auth-btn-spinner">Processing...</span>
                ) : (
                  <span>{tab === 'login' ? 'Sign In to SmartMart' : 'Create Free Account'}</span>
                )}
              </button>
            </form>

            <div className="auth-footer-prompt">
              {tab === 'login' ? (
                <>
                  Don't have an account?{' '}
                  <button
                    type="button"
                    className="auth-inline-link"
                    onClick={() => { setTab('register'); setError(null); }}
                  >
                    Register here
                  </button>
                </>
              ) : (
                <>
                  Already registered?{' '}
                  <button
                    type="button"
                    className="auth-inline-link"
                    onClick={() => { setTab('login'); setError(null); }}
                  >
                    Sign in here
                  </button>
                </>
              )}
            </div>
          </>
        ) : (
          /* Google Account Picker / Sign-In Dialog */
          <div className="google-picker-card">
            <div className="google-picker-header">
              <svg viewBox="0 0 24 24" width="28" height="28">
                <path
                  fill="#4285F4"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                />
                <path
                  fill="#34A853"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
                />
                <path
                  fill="#EA4335"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
                />
              </svg>
              <h4>Choose a Google Account</h4>
              <p>to continue to <strong>SmartMart AI</strong></p>
            </div>

            {/* Quick-Select Account Item */}
            <div
              className="google-account-item"
              onClick={() => handleGoogleSubmit(googleEmail, googleName)}
            >
              <div className="google-avatar-circle">
                {googleName.charAt(0).toUpperCase() || 'G'}
              </div>
              <div className="google-account-details">
                <div className="google-account-name">{googleName || 'Google User'}</div>
                <div className="google-account-email">{googleEmail || 'user@gmail.com'}</div>
              </div>
              <span className="google-select-arrow">➔</span>
            </div>

            {/* Or custom Google account inputs */}
            <div className="google-custom-entry">
              <label>Or enter your Gmail address:</label>
              <input
                type="email"
                placeholder="yourname@gmail.com"
                value={googleEmail}
                onChange={e => {
                  setGoogleEmail(e.target.value);
                  const userPart = e.target.value.split('@')[0].replace(/[._-]+/g, ' ').replace(/\d+/g, '').trim();
                  if (userPart) setGoogleName(userPart.charAt(0).toUpperCase() + userPart.slice(1));
                }}
              />
              <input
                type="text"
                placeholder="Gmail Username / Display Name"
                value={googleName}
                onChange={e => setGoogleName(e.target.value)}
              />
            </div>

            <div className="google-picker-actions">
              <button
                type="button"
                className="btn-cancel"
                onClick={() => setShowGooglePicker(false)}
              >
                Back
              </button>
              <button
                type="button"
                className="google-confirm-btn"
                onClick={() => handleGoogleSubmit(googleEmail, googleName)}
                disabled={loading || !googleEmail.includes('@')}
              >
                {loading ? 'Signing In...' : 'Continue as ' + (googleName || 'User')}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
