import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';

const AuthContext = createContext({
  user: null,
  token: null,
  isLoggedIn: false,
  loading: true,
  login: async () => {},
  register: async () => {},
  loginWithGoogle: async () => {},
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

  // Validate session on mount
  useEffect(() => {
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
  }, []);

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

  const loginWithGoogle = useCallback(async (email, name, avatarUrl) => {
    const res = await api.loginGoogle(email, name, avatarUrl);
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
        login,
        register,
        loginWithGoogle,
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
