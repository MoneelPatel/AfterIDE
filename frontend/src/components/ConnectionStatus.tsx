/**
 * AfterIDE - Connection Status Component
 * 
 * Displays WebSocket connection status with visual indicators.
 */

import React from 'react';
import { useWebSocket } from '../contexts/WebSocketContext';
import { useTheme } from '../contexts/ThemeContext';
import { WifiIcon, ExclamationTriangleIcon, CheckCircleIcon, ClockIcon } from '@heroicons/react/24/outline';

const ConnectionStatus: React.FC = () => {
  const {
    terminalConnected,
    filesConnected,
    terminalConnecting,
    filesConnecting,
    terminalMetadata,
    filesMetadata
  } = useWebSocket();
  
  const { theme } = useTheme();

  const getStatusIcon = (connected: boolean, connecting: boolean) => {
    if (connecting) {
      return <ClockIcon className="w-4 h-4 text-yellow-500 animate-spin" />;
    }
    if (connected) {
      return <CheckCircleIcon className="w-4 h-4 text-green-500" />;
    }
    return <ExclamationTriangleIcon className="w-4 h-4 text-red-500" />;
  };

  const getStatusText = (connected: boolean, connecting: boolean, type: string) => {
    if (connecting) {
      return `${type} Connecting...`;
    }
    if (connected) {
      return `${type} Connected`;
    }
    return `${type} Disconnected`;
  };

  const getStatusColor = (connected: boolean, connecting: boolean) => {
    if (connecting) {
      return theme === 'dark' 
        ? 'text-yellow-400 bg-yellow-900/20 border-yellow-700' 
        : 'text-yellow-600 bg-yellow-50 border-yellow-200';
    }
    if (connected) {
      return theme === 'dark' 
        ? 'text-green-400 bg-green-900/20 border-green-700' 
        : 'text-green-600 bg-green-50 border-green-200';
    }
    return theme === 'dark' 
      ? 'text-red-400 bg-red-900/20 border-red-700' 
      : 'text-red-600 bg-red-50 border-red-200';
  };

  return (
    <div className="flex items-center space-x-2 text-sm connection-status">
      <WifiIcon className={`w-4 h-4 ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`} />
      
      {/* Terminal Status */}
      <div className={`flex items-center space-x-1 px-2 py-1 rounded-md border ${getStatusColor(terminalConnected, terminalConnecting)}`}>
        {getStatusIcon(terminalConnected, terminalConnecting)}
        <span>{getStatusText(terminalConnected, terminalConnecting, 'Terminal')}</span>
      </div>

      {/* Files Status */}
      <div className={`flex items-center space-x-1 px-2 py-1 rounded-md border ${getStatusColor(filesConnected, filesConnecting)}`}>
        {getStatusIcon(filesConnected, filesConnecting)}
        <span>{getStatusText(filesConnected, filesConnecting, 'Files')}</span>
      </div>

      {/* Connection Details (only show when connected) */}
      {(terminalConnected || filesConnected) && (
        <div className={`text-xs ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>
          {terminalMetadata && (
            <div>Terminal ID: {terminalMetadata.connectionId.slice(0, 8)}...</div>
          )}
          {filesMetadata && (
            <div>Files ID: {filesMetadata.connectionId.slice(0, 8)}...</div>
          )}
        </div>
      )}
    </div>
  );
};

export default ConnectionStatus; 