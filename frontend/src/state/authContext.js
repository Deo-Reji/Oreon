import React, { createContext, useContext, useEffect, useState } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { apiRequest, setAuthToken } from '../services/apiClient';

const TOKEN_KEY = '@oreon_token';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(null);
  const [user, setUser] = useState(null);
  // `loading` covers the initial token-restore on app start so screens can
  // show a splash instead of flashing the login screen.
  const [loading, setLoading] = useState(true);

  // On mount, restore any saved token and fetch the current user.
  useEffect(() => {
    (async () => {
      try {
        const saved = await AsyncStorage.getItem(TOKEN_KEY);
        if (saved) {
          setAuthToken(saved);
          setToken(saved);
          try {
            const me = await apiRequest('/api/users/me');
            setUser(me);
          } catch {
            // Token expired or invalid — clear it.
            await AsyncStorage.removeItem(TOKEN_KEY);
            setAuthToken(null);
            setToken(null);
          }
        }
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  async function persistToken(newToken) {
    setAuthToken(newToken);
    setToken(newToken);
    await AsyncStorage.setItem(TOKEN_KEY, newToken);
  }

  async function signUp(email, password) {
    const res = await apiRequest('/api/auth/register', {
      method: 'POST',
      body: { email, password },
    });
    await persistToken(res.token);
    const me = await apiRequest('/api/users/me');
    setUser(me);
  }

  async function signIn(email, password) {
    const res = await apiRequest('/api/auth/login', {
      method: 'POST',
      body: { email, password },
    });
    await persistToken(res.token);
    const me = await apiRequest('/api/users/me');
    setUser(me);
  }

  async function signOut() {
    await AsyncStorage.removeItem(TOKEN_KEY);
    setAuthToken(null);
    setToken(null);
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ token, user, loading, signIn, signUp, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return ctx;
}
