import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';

const SAVED_GOOGLE_ACCOUNTS_KEY = 'smartmart_saved_google_accounts';

const DEFAULT_ACCOUNTS = [
  {
    name: 'Ritee Ritee',
    email: 'riteeritee251@gmail.com',
    avatarBg: 'linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)',
    avatarInitial: 'R',
  },
  {
    name: 'darshan darshan',
    email: 'darshandarshu3013@gmail.com',
    avatarBg: '#00897b',
    avatarInitial: 'd',
  },
];

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

  // Google Account Chooser modal states
  const [showGooglePicker, setShowGooglePicker] = useState(false);
  const [googleView, setGoogleView] = useState('accounts'); // 'accounts' | 'enter-another' | 'confirm-username'
  const [selectedAccount, setSelectedAccount] = useState(null);
  const [customEmail, setCustomEmail] = useState('');
  const [googleUsername, setGoogleUsername] = useState('');

  // Remembered accounts on this browser
  const [googleAccounts, setGoogleAccounts] = useState(() => {
    try {
      const stored = localStorage.getItem(SAVED_GOOGLE_ACCOUNTS_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed) && parsed.length > 0) return parsed;
      }
    } catch {}
    return DEFAULT_ACCOUNTS;
  });

  useEffect(() => {
    if (isOpen) {
      setTab(initialTab);
      setError(null);
      setShowGooglePicker(false);
      setGoogleView('accounts');
      setSelectedAccount(null);
      setCustomEmail('');
      setGoogleUsername('');
    }
  }, [isOpen, initialTab]);

  if (!isOpen) return null;

  // Persist google accounts to localStorage
  const saveGoogleAccounts = (updatedList) => {
    setGoogleAccounts(updatedList);
    try {
      localStorage.setItem(SAVED_GOOGLE_ACCOUNTS_KEY, JSON.stringify(updatedList));
    } catch {}
  };

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

  // Regular Email + Password submission
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

  // Open Google Account Chooser
  const handleOpenGooglePicker = () => {
    setError(null);
    setGoogleView('accounts');
    setSelectedAccount(null);
    setShowGooglePicker(true);
  };

  // User clicked an account from the Google list
  const handleSelectGoogleAccount = async (account) => {
    setError(null);
    setLoading(true);
    try {
      // Check if account already exists in database
      const check = await api.checkEmail(account.email);
      if (check.exists) {
        // Account exists! Log in directly without password
        await loginWithGoogle(account.email, check.name || account.name);
        setShowGooglePicker(false);
        if (onSuccess) onSuccess();
        onClose();
      } else {
        // Account does not exist yet: ask for user name (no password required)
        setSelectedAccount(account);
        setGoogleUsername(check.suggested_name || account.name || 'User');
        setGoogleView('confirm-username');
      }
    } catch (err) {
      setError(err.message || 'Error verifying account.');
    } finally {
      setLoading(false);
    }
  };

  // Submit custom/new Google account from "Use another account"
  const handleCustomEmailNext = async (e) => {
    e.preventDefault();
    const cleanEmail = customEmail.trim().toLowerCase();
    if (!cleanEmail || !cleanEmail.includes('@')) {
      setError('Please enter a valid Google email address.');
      return;
    }

    setError(null);
    setLoading(true);
    try {
      const check = await api.checkEmail(cleanEmail);
      const derivedName = check.name || check.suggested_name || cleanEmail.split('@')[0];
      const newAcc = {
        name: derivedName,
        email: cleanEmail,
        avatarBg: '#1a73e8',
        avatarInitial: derivedName.charAt(0).toUpperCase(),
      };

      // Add to remembered list if not already present
      if (!googleAccounts.some(a => a.email.toLowerCase() === cleanEmail)) {
        saveGoogleAccounts([newAcc, ...googleAccounts]);
      }

      if (check.exists) {
        // Account exists -> log in directly without password
        await loginWithGoogle(cleanEmail, check.name || derivedName);
        setShowGooglePicker(false);
        if (onSuccess) onSuccess();
        onClose();
      } else {
        // Account does not exist -> ask for user name without password
        setSelectedAccount(newAcc);
        setGoogleUsername(derivedName);
        setGoogleView('confirm-username');
      }
    } catch (err) {
      setError(err.message || 'Error verifying Google account.');
    } finally {
      setLoading(false);
    }
  };

  // Complete Google sign-in after user name confirmation (NO password needed)
  const handleConfirmGoogleUsername = async (e) => {
    e.preventDefault();
    if (!selectedAccount) return;
    setError(null);
    setLoading(true);
    try {
      const finalName = googleUsername.trim() || selectedAccount.name;
      // Ensure saved to browser accounts list
      if (!googleAccounts.some(a => a.email.toLowerCase() === selectedAccount.email.toLowerCase())) {
        saveGoogleAccounts([...googleAccounts, { ...selectedAccount, name: finalName }]);
      }
      await loginWithGoogle(selectedAccount.email, finalName);
      setShowGooglePicker(false);
      if (onSuccess) onSuccess();
      onClose();
    } catch (err) {
      setError(err.message || 'Google registration failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-overlay" onClick={onClose}>
      <div
        className={`auth-modal ${showGooglePicker ? 'google-oauth-mode' : ''}`}
        onClick={e => e.stopPropagation()}
      >
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
          /* ════════════════════════════════════════════════════════════════
             AUTHENTIC GOOGLE ACCOUNT CHOOSER (Matching browser Google screen)
             ════════════════════════════════════════════════════════════════ */
          <div className="google-oauth-window">
            {/* Top Google Header */}
            <div className="google-oauth-topbar">
              <div className="google-brand-header">
                <svg viewBox="0 0 24 24" width="22" height="22">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
                </svg>
                <span>Sign in with Google</span>
              </div>
            </div>

            {error && <div className="auth-error-banner" style={{ margin: '12px 20px 0 20px' }}>{error}</div>}

            {googleView === 'accounts' && (
              <div className="google-oauth-body">
                {/* Left Side: Brand & Heading */}
                <div className="google-oauth-left">
                  <div className="google-app-badge">
                    <div className="google-app-icon">
                      <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                        <rect x="4" y="11" width="3.5" height="9" rx="1.5" fill="#a8f09d" />
                        <rect x="10.25" y="5" width="3.5" height="15" rx="1.5" fill="#a8f09d" />
                        <rect x="16.5" y="8" width="3.5" height="12" rx="1.5" fill="#a8f09d" />
                      </svg>
                    </div>
                  </div>
                  <h2>Choose an account</h2>
                  <p className="google-app-dest">to continue to <span>SmartMart AI</span></p>
                </div>

                {/* Right Side: Accounts List */}
                <div className="google-oauth-right">
                  <div className="google-accounts-scroll">
                    {googleAccounts.map((acc, index) => (
                      <div
                        key={acc.email}
                        className="google-acc-row"
                        onClick={() => handleSelectGoogleAccount(acc)}
                      >
                        <div
                          className="google-acc-avatar"
                          style={{ background: acc.avatarBg || '#1a73e8' }}
                        >
                          {acc.avatarInitial || acc.name.charAt(0).toUpperCase()}
                        </div>
                        <div className="google-acc-text">
                          <div className="google-acc-name">{acc.name}</div>
                          <div className="google-acc-email">{acc.email}</div>
                        </div>
                      </div>
                    ))}

                    {/* Use Another Account Option */}
                    <div
                      className="google-acc-row use-another"
                      onClick={() => {
                        setGoogleView('enter-another');
                        setError(null);
                      }}
                    >
                      <div className="google-acc-avatar outline">
                        <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                          <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z" />
                        </svg>
                      </div>
                      <div className="google-acc-text">
                        <div className="google-acc-name">Use another account</div>
                      </div>
                    </div>
                  </div>

                  <div className="google-oauth-disclaimer">
                    Before using this app, you can review SmartMart AI's{' '}
                    <a href="#privacy" onClick={e => e.preventDefault()}>Privacy Policy</a> and{' '}
                    <a href="#terms" onClick={e => e.preventDefault()}>Terms of Service</a>.
                  </div>
                </div>
              </div>
            )}

            {/* View: Enter Another Gmail Address */}
            {googleView === 'enter-another' && (
              <div className="google-oauth-subview">
                <div className="google-subview-header">
                  <div className="google-app-icon small">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                      <rect x="4" y="11" width="3.5" height="9" rx="1.5" fill="#a8f09d" />
                      <rect x="10.25" y="5" width="3.5" height="15" rx="1.5" fill="#a8f09d" />
                      <rect x="16.5" y="8" width="3.5" height="12" rx="1.5" fill="#a8f09d" />
                    </svg>
                  </div>
                  <h3>Sign in with another Google account</h3>
                  <p>Enter your Gmail address to continue</p>
                </div>

                <form onSubmit={handleCustomEmailNext} className="google-another-form">
                  <div className="google-input-box">
                    <label>Email or phone</label>
                    <input
                      type="email"
                      autoFocus
                      required
                      placeholder="e.g. name@gmail.com"
                      value={customEmail}
                      onChange={e => setCustomEmail(e.target.value)}
                    />
                  </div>

                  <div className="google-subview-actions">
                    <button
                      type="button"
                      className="google-btn-back"
                      onClick={() => { setGoogleView('accounts'); setError(null); }}
                    >
                      Back
                    </button>
                    <button
                      type="submit"
                      className="google-btn-next"
                      disabled={loading || !customEmail.includes('@')}
                    >
                      {loading ? 'Verifying...' : 'Next'}
                    </button>
                  </div>
                </form>
              </div>
            )}

            {/* View: Confirm User Name for New Google Users (NO password needed!) */}
            {googleView === 'confirm-username' && selectedAccount && (
              <div className="google-oauth-subview">
                <div className="google-subview-header">
                  <div
                    className="google-acc-avatar"
                    style={{ background: selectedAccount.avatarBg || '#1a73e8', margin: '0 auto 10px auto' }}
                  >
                    {selectedAccount.avatarInitial || selectedAccount.name.charAt(0).toUpperCase()}
                  </div>
                  <h3>Confirm your User Name</h3>
                  <p>Welcome! Set your display username to complete sign in with <strong>{selectedAccount.email}</strong></p>
                </div>

                <form onSubmit={handleConfirmGoogleUsername} className="google-another-form">
                  <div className="google-input-box">
                    <label>User Name</label>
                    <input
                      type="text"
                      autoFocus
                      required
                      placeholder="Enter user name"
                      value={googleUsername}
                      onChange={e => setGoogleUsername(e.target.value)}
                    />
                  </div>

                  <div className="google-no-password-note">
                    🔒 No password needed when signing in with Google.
                  </div>

                  <div className="google-subview-actions">
                    <button
                      type="button"
                      className="google-btn-back"
                      onClick={() => { setGoogleView('accounts'); setError(null); }}
                    >
                      Back
                    </button>
                    <button
                      type="submit"
                      className="google-btn-next"
                      disabled={loading || !googleUsername.trim()}
                    >
                      {loading ? 'Signing In...' : 'Complete Sign In'}
                    </button>
                  </div>
                </form>
              </div>
            )}

            {/* Bottom Google Footer */}
            <div className="google-oauth-footer">
              <span className="google-lang">
                English (United Kingdom) <span style={{ fontSize: '9px', marginLeft: '4px', opacity: 0.8 }}>▼</span>
              </span>
              <div className="google-footer-links">
                <a href="#help" onClick={e => e.preventDefault()}>Help</a>
                <a href="#privacy" onClick={e => e.preventDefault()}>Privacy</a>
                <a href="#terms" onClick={e => e.preventDefault()}>Terms</a>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
