/**
 * AfterIDE - Authentication Reset Button
 * 
 * Component that provides a button for users to reset their authentication
 * when they encounter authentication issues.
 */

import React from 'react';
import { clearAuthData } from '../utils/auth';

interface AuthResetButtonProps {
  className?: string;
}

const AuthResetButton: React.FC<AuthResetButtonProps> = ({ className = '' }) => {
  const handleReset = () => {
    if (confirm('This will clear your authentication data and redirect you to the login page. Continue?')) {
      clearAuthData();
    }
  };

  return (
    <button
      onClick={handleReset}
      className={`fixed bottom-4 right-4 bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg shadow-lg transition-colors duration-200 z-50 ${className}`}
      title="Reset authentication data"
    >
      Reset Auth
    </button>
  );
};

export default AuthResetButton; 