import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { login as apiLogin, getMe as apiGetMe } from '../api/auth';
import { DEMO_PERSONAS } from '../types/constants';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [currentUser, setCurrentUser] = useState(null);
  const [activePersona, setActivePersona] = useState(DEMO_PERSONAS[0]); // default Arun (L1)
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Authenticate as a specific persona by calling real backend login
  const switchPersona = useCallback(async (persona) => {
    setLoading(true);
    setError(null);
    try {
      // Call real backend authentication endpoint
      const loginRes = await apiLogin(persona.email, 'OpsPilot@123');
      localStorage.setItem('opspilot_token', loginRes.access_token);

      // Verify token with backend /auth/me
      const meRes = await apiGetMe();
      setCurrentUser(meRes);
      setActivePersona(persona);
      return meRes;
    } catch (err) {
      console.error('Failed to authenticate persona:', err);
      setError(err.message || 'Authentication failed');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  // Initialize with Arun (L1) or existing token on initial mount
  useEffect(() => {
    const initAuth = async () => {
      try {
        await switchPersona(DEMO_PERSONAS[0]);
      } catch (err) {
        console.warn('Initial auth check warning:', err);
      }
    };
    initAuth();
  }, [switchPersona]);

  // Check if current user has a specific permission
  const hasPermission = useCallback((permCode) => {
    if (!currentUser || !currentUser.permissions) return false;
    // Admin role has all permissions
    if (currentUser.role_id === 4) return true;
    return currentUser.permissions.includes(permCode);
  }, [currentUser]);

  return (
    <AuthContext.Provider
      value={{
        currentUser,
        activePersona,
        loading,
        error,
        switchPersona,
        hasPermission,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
