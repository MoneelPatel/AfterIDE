/**
 * AfterIDE - Authentication Reset Component
 * 
 * Component to help users clear authentication issues and force re-login.
 */

import React from 'react';
import { useAuthStore } from '../store/authStore';

const AuthReset: React.FC = () => {
  const { clearAuth } = useAuthStore();

  const handleReset = () => {
    if (window.confirm('This will clear your authentication and redirect you to the login page. Continue?')) {
      clearAuth();
    }
  };

  return (
    <div className="fixed bottom-4 right-4 z-50">
      <button
        onClick={handleReset}
        className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md shadow-lg transition-colors text-sm"
        title="Clear authentication and re-login"
      >
        Reset Auth
      </button>
    </div>
  );
};

export default AuthReset; 