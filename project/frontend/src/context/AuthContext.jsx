import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';

const AuthContext = createContext({
  user: null,
  token: null,
  isLoggedIn: false,
  loading: true,
  oauthNotice: null,
  login: async () => {},
  register: async () => {},
  loginWithGoogle: async () => {},
  linkAccount: async () => {},
  clearOauthNotice: () => {},
  logout: async () => {},
  updateUserState: async () => {},
});

const TOKEN_KEY = 'smartmart_token';
const USER_KEY = 'smartmart_user';

export function AuthProvider({ children, onAuthStateChange }) {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState(() => {
    try {
      const stored = localStorage.getItem(USER_KEY);
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });
  const [loading, setLoading] = useState(true);
  const [oauthNotice, setOauthNotice] = useState(null);

  // Validate session on mount and handle incoming OAuth callback parameters
  useEffect(() => {
    // 1. Check for incoming OAuth redirect parameters in URL
    const searchParams = new URLSearchParams(window.location.search);
    const authStatus = searchParams.get('auth_status');
    const authToken = searchParams.get('auth_token');
    const authMessage = searchParams.get('message');
    const authEmail = searchParams.get('email');
    const authTicket = searchParams.get('ticket');

    if (authStatus) {
      // Clean up sensitive tokens and parameters from the address bar
      const cleanUrl = window.location.pathname;
      window.history.replaceState({}, document.title, cleanUrl);

      if (authStatus === 'success' && authToken) {
        setToken(authToken);
        localStorage.setItem(TOKEN_KEY, authToken);
        api.getMe(authToken)
          .then(res => {
            if (res.user) {
              setUser(res.user);
              localStorage.setItem(USER_KEY, JSON.stringify(res.user));
              if (onAuthStateChange) onAuthStateChange('login', res.user);
            }
          })
          .catch(() => {
            localStorage.removeItem(TOKEN_KEY);
            localStorage.removeItem(USER_KEY);
            setToken(null);
            setUser(null);
          })
          .finally(() => {
            setLoading(false);
          });
        return;
      } else if (authStatus === 'linking_required') {
        setOauthNotice({
          type: 'linking_required',
          email: authEmail || '',
          ticket: authTicket || '',
        });
        setLoading(false);
        return;
      } else if (authStatus === 'config_required') {
        setOauthNotice({
          type: 'config_required',
          message: authMessage || 'Google OAuth is not configured on the backend. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in backend/.env.',
        });
        setLoading(false);
        return;
      } else if (authStatus === 'error') {
        setOauthNotice({
          type: 'error',
          message: authMessage || 'Google authentication failed. Please try again.',
        });
        setLoading(false);
        return;
      }
    }

    // 2. Normal session check from stored token
    const savedToken = localStorage.getItem(TOKEN_KEY);
    if (!savedToken) {
      setLoading(false);
      return;
    }

    api.getMe(savedToken)
      .then(res => {
        if (res.user) {
          setUser(res.user);
          localStorage.setItem(USER_KEY, JSON.stringify(res.user));
          if (onAuthStateChange) onAuthStateChange('login', res.user);
        }
      })
      .catch(() => {
        // Token expired or invalid
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(USER_KEY);
        setToken(null);
        setUser(null);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [onAuthStateChange]);

  const login = useCallback(async (email, password) => {
    const res = await api.login(email, password);
    if (res.token && res.user) {
      setToken(res.token);
      setUser(res.user);
      localStorage.setItem(TOKEN_KEY, res.token);
      localStorage.setItem(USER_KEY, JSON.stringify(res.user));
      if (onAuthStateChange) onAuthStateChange('login', res.user);
      return res.user;
    }
    throw new Error(res.message || 'Login failed');
  }, [onAuthStateChange]);

  const register = useCallback(async (name, email, password) => {
    const res = await api.register(name, email, password);
    if (res.token && res.user) {
      setToken(res.token);
      setUser(res.user);
      localStorage.setItem(TOKEN_KEY, res.token);
      localStorage.setItem(USER_KEY, JSON.stringify(res.user));
      if (onAuthStateChange) onAuthStateChange('register', res.user);
      return res.user;
    }
    throw new Error(res.message || 'Registration failed');
  }, [onAuthStateChange]);

  const loginWithGoogle = useCallback(async (email, name, avatarUrl, idToken) => {
    const res = await api.loginGoogle(email, name, avatarUrl, idToken);
    if (res.token && res.user) {
      setToken(res.token);
      setUser(res.user);
      localStorage.setItem(TOKEN_KEY, res.token);
      localStorage.setItem(USER_KEY, JSON.stringify(res.user));
      if (onAuthStateChange) onAuthStateChange('login', res.user);
      return res.user;
    }
    throw new Error(res.message || 'Google Sign-In failed');
  }, [onAuthStateChange]);

  const linkAccount = useCallback(async (ticket, password) => {
    const res = await api.linkGoogleAccount(ticket, password);
    if (res.token && res.user) {
      setToken(res.token);
      setUser(res.user);
      localStorage.setItem(TOKEN_KEY, res.token);
      localStorage.setItem(USER_KEY, JSON.stringify(res.user));
      setOauthNotice(null);
      if (onAuthStateChange) onAuthStateChange('login', res.user);
      return res.user;
    }
    throw new Error(res.message || 'Account linking failed');
  }, [onAuthStateChange]);

  const clearOauthNotice = useCallback(() => {
    setOauthNotice(null);
  }, []);

  const logout = useCallback(async () => {
    try {
      if (token) {
        await api.logout(token).catch(() => {});
      }
    } finally {
      setToken(null);
      setUser(null);
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
      if (onAuthStateChange) onAuthStateChange('logout', null);
    }
  }, [token, onAuthStateChange]);

  const updateUserState = useCallback(async (partialState) => {
    if (!user || !token) return;
    try {
      const res = await api.saveUserState(partialState, token);
      if (res.state_data) {
        const updatedUser = { ...user, state_data: res.state_data };
        setUser(updatedUser);
        localStorage.setItem(USER_KEY, JSON.stringify(updatedUser));
      }
    } catch (err) {
      console.warn('Could not save user state remotely:', err);
    }
  }, [user, token]);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoggedIn: Boolean(user && token),
        loading,
        oauthNotice,
        login,
        register,
        loginWithGoogle,
        linkAccount,
        clearOauthNotice,
        logout,
        updateUserState,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}

export default AuthContext;
