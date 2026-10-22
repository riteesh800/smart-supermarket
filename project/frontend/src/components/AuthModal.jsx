import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';

function deriveNameFromEmail(email) {
  if (!email || !email.includes('@')) return 'User';
  const prefix = email.split('@')[0];
  const cleaned = prefix.replace(/[._-]+/g, ' ').replace(/\d+/g, '').trim();
  if (!cleaned) return prefix;
  return cleaned.charAt(0).toUpperCase() + cleaned.slice(1);
}

function PasswordToggleIcon({ open }) {
  if (open) {
    // Eye open icon
    return (
      <svg
        width="16"
        height="16"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
      >
        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
        <circle cx="12" cy="12" r="3" />
      </svg>
    );
  }
  // Eye closed icon (slashed eye)
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
      <line x1="1" y1="1" x2="23" y2="23" />
    </svg>
  );
}

export default function AuthModal({ isOpen, onClose, initialTab = 'login', onSuccess }) {
  const { login, register, oauthNotice, linkAccount, clearOauthNotice } = useAuth();
  const [tab, setTab] = useState(initialTab); // 'login' | 'register' | 'link_account' | 'config_info'
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [isRedirecting, setIsRedirecting] = useState(false);
  const [error, setError] = useState(null);

  // Explicit account-linking password
  const [linkPassword, setLinkPassword] = useState('');
  const [showLinkPassword, setShowLinkPassword] = useState(false);

  // Sync state when opened or when oauthNotice arrives
  useEffect(() => {
    if (isOpen) {
      if (oauthNotice) {
        if (oauthNotice.type === 'linking_required') {
          setTab('link_account');
          setError(null);
        } else if (oauthNotice.type === 'config_required') {
          setTab('config_info');
          setError(oauthNotice.message);
        } else if (oauthNotice.type === 'error') {
          setError(oauthNotice.message);
        }
      } else {
        setTab(initialTab);
        setError(null);
      }
      setIsRedirecting(false);
      setLoading(false);
      setLinkPassword('');
    }
  }, [isOpen, initialTab, oauthNotice]);

  if (!isOpen) return null;

  const handleEmailChange = (val) => {
    setEmail(val);
    if (!name && val.includes('@')) {
      const suggested = deriveNameFromEmail(val);
      if (suggested) setName(suggested);
    }
  };

  // Regular Email + Password submission
  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const cleanEmail = email.trim().toLowerCase();
      if (!cleanEmail || !cleanEmail.includes('@')) {
        throw new Error('Please enter a valid email address.');
      }

      if (tab === 'register') {
        if (password.length < 6) {
          throw new Error('Password must be at least 6 characters long.');
        }
        if (password !== confirmPassword) {
          throw new Error('Passwords do not match.');
        }
        await register(name.trim(), cleanEmail, password);
      } else {
        if (!password) {
          throw new Error('Please enter your password.');
        }
        await login(cleanEmail, password);
      }

      if (onSuccess) onSuccess();
      onClose();
    } catch (err) {
      setError(err.message || 'Authentication failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  // Real Google OAuth 2.0 flow initiation
  const handleInitiateGoogleOAuth = async () => {
    if (isRedirecting) return;
    setError(null);
    setIsRedirecting(true);

    try {
      // First check if backend has Google OAuth configured
      const configStatus = await api.getGoogleConfigStatus().catch(() => ({ configured: true }));
      if (configStatus && configStatus.configured === false) {
        setIsRedirecting(false);
        setTab('config_info');
        setError('Google OAuth credentials (GOOGLE_CLIENT_ID & GOOGLE_CLIENT_SECRET) are not configured in backend/.env.');
        return;
      }

      // Redirect browser to backend endpoint that initiates Google OAuth with PKCE & prompt=select_account
      api.initiateGoogleOAuth('select_account', '/');
    } catch (err) {
      setIsRedirecting(false);
      setError(err.message || 'Could not initiate Google Sign-In.');
    }
  };

  // Explicit Account Linking Submission
  const handleAccountLinkSubmit = async (e) => {
    e.preventDefault();
    if (!oauthNotice || !oauthNotice.ticket) {
      setError('Linking session has expired. Please try signing in with Google again.');
      return;
    }
    if (!linkPassword) {
      setError('Please enter your SmartMart account password.');
      return;
    }

    setError(null);
    setLoading(true);
    try {
      await linkAccount(oauthNotice.ticket, linkPassword);
      if (clearOauthNotice) clearOauthNotice();
      if (onSuccess) onSuccess();
      onClose();
    } catch (err) {
      setError(err.message || 'Account linking failed. Please verify your password.');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (clearOauthNotice) clearOauthNotice();
    onClose();
  };

  return (
    <div className="auth-overlay" onClick={handleClose}>
      <div className="auth-modal" onClick={e => e.stopPropagation()}>
        <button className="auth-close-btn" onClick={handleClose} aria-label="Close dialog">
          ✕
        </button>

        {/* ──────────── TAB: CONFIG REQUIRED GUIDANCE ──────────── */}
        {tab === 'config_info' && (
          <div className="auth-config-view">
            <div className="auth-header">
              <div className="auth-brand-badge">
                <span className="auth-logo-icon">⚠️</span>
                <span>Google OAuth Setup Required</span>
              </div>
              <h3>Configuration Needed</h3>
              <p>To enable real Google Sign-In and account chooser, configure your Google Cloud OAuth credentials in your backend environment.</p>
            </div>

            {error && <div className="auth-error-banner">{error}</div>}

            <div className="auth-config-card">
              <h4>Quick Setup Steps:</h4>
              <ol className="auth-config-list">
                <li>Open <strong>Google Cloud Console</strong> &rarr; <em>APIs & Services</em> &rarr; <em>Credentials</em></li>
                <li>Create an <strong>OAuth 2.0 Client ID</strong> (Web application)</li>
                <li>Add to <strong>Authorized redirect URIs</strong>:
                  <code>http://localhost:8000/api/auth/google/callback</code>
                </li>
                <li>Add credentials to your <code>project/backend/.env</code>:
                  <pre>
{`GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback`}
                  </pre>
                </li>
              </ol>
            </div>

            <div className="auth-subview-actions" style={{ marginTop: '18px', display: 'flex', gap: '10px' }}>
              <button
                type="button"
                className="auth-submit-btn"
                style={{ flex: 1 }}
                onClick={() => { setTab('login'); setError(null); }}
              >
                Sign in with Email instead
              </button>
            </div>
          </div>
        )}

        {/* ──────────── TAB: ACCOUNT LINKING REQUIRED (Case 3) ──────────── */}
        {tab === 'link_account' && (
          <div className="auth-linking-view">
            <div className="auth-header">
              <div className="auth-brand-badge">
                <span className="auth-logo-icon">🔗</span>
                <span>Account Linking Required</span>
              </div>
              <h3>Link Google Account</h3>
              <p>
                An account with <strong>{oauthNotice?.email}</strong> is already registered with password authentication.
                To link your Google identity, please enter your existing SmartMart password.
              </p>
            </div>

            {error && <div className="auth-error-banner">{error}</div>}

            <form onSubmit={handleAccountLinkSubmit} className="auth-form">
              <div className="auth-field">
                <label>Registered Email</label>
                <div className="auth-input-wrapper">
                  <span className="auth-field-icon">✉️</span>
                  <input
                    type="email"
                    disabled
                    value={oauthNotice?.email || ''}
                    style={{ opacity: 0.85, cursor: 'not-allowed' }}
                  />
                </div>
              </div>

              <div className="auth-field">
                <label htmlFor="link-password">Your SmartMart Password</label>
                <div className="auth-input-wrapper">
                  <span className="auth-field-icon">🔒</span>
                  <input
                    id="link-password"
                    type={showLinkPassword ? 'text' : 'password'}
                    required
                    autoFocus
                    placeholder="Enter your existing account password"
                    value={linkPassword}
                    onChange={e => setLinkPassword(e.target.value)}
                  />
                  <button
                    type="button"
                    className="auth-password-toggle"
                    onClick={() => setShowLinkPassword(p => !p)}
                    tabIndex="-1"
                    aria-label={showLinkPassword ? 'Hide password' : 'Show password'}
                    title={showLinkPassword ? 'Hide password' : 'Show password'}
                  >
                    <PasswordToggleIcon open={showLinkPassword} />
                  </button>
                </div>
              </div>

              <button
                type="submit"
                className="auth-submit-btn"
                disabled={loading || !linkPassword}
              >
                {loading ? (
                  <span className="auth-btn-spinner">Linking Account...</span>
                ) : (
                  <span>Verify Password & Link Google Account</span>
                )}
              </button>

              <button
                type="button"
                className="auth-btn-secondary"
                onClick={() => {
                  if (clearOauthNotice) clearOauthNotice();
                  setTab('login');
                  setError(null);
                }}
              >
                Cancel and Return to Sign In
              </button>
            </form>
          </div>
        )}

        {/* ──────────── TAB: LOGIN & REGISTER ──────────── */}
        {(tab === 'login' || tab === 'register') && (
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

            {error && <div className="auth-error-banner">{error}</div>}

            {/* Google OAuth Section */}
            <div className="auth-social-section">
              <button
                type="button"
                className="google-auth-btn"
                onClick={handleInitiateGoogleOAuth}
                disabled={loading || isRedirecting}
              >
                {isRedirecting ? (
                  <span className="auth-btn-spinner">Connecting to Google...</span>
                ) : (
                  <>
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
                  </>
                )}
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
                    placeholder={tab === 'register' ? 'Choose a password (min 6 chars)' : 'Enter your password'}
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                  />
                  <button
                    type="button"
                    className="auth-password-toggle"
                    onClick={() => setShowPassword(p => !p)}
                    tabIndex="-1"
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                    title={showPassword ? 'Hide password' : 'Show password'}
                  >
                    <PasswordToggleIcon open={showPassword} />
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
                disabled={loading || isRedirecting}
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
        )}
      </div>
    </div>
  );
}
