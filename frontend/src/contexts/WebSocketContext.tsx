/**
 * AfterIDE - WebSocket Context
 * 
 * React context for managing WebSocket connections and state.
 */

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { terminalWebSocket, filesWebSocket, WebSocketMessage, ConnectionMetadata } from '../services/websocket';

interface WebSocketContextType {
  // Connection status
  terminalConnected: boolean;
  filesConnected: boolean;
  terminalConnecting: boolean;
  filesConnecting: boolean;
  
  // Connection metadata
  terminalMetadata: ConnectionMetadata | null;
  filesMetadata: ConnectionMetadata | null;
  
  // Connection methods
  connectTerminal: (sessionId: string, token?: string) => Promise<void>;
  connectFiles: (sessionId: string, token?: string) => Promise<void>;
  disconnectTerminal: () => void;
  disconnectFiles: () => void;
  
  // Message methods
  sendTerminalMessage: (message: WebSocketMessage) => void;
  sendFilesMessage: (message: WebSocketMessage) => void;
  
  // Event handlers
  onTerminalMessage: (type: string, handler: (message: WebSocketMessage) => void) => void;
  onFilesMessage: (type: string, handler: (message: WebSocketMessage) => void) => void;
  offTerminalMessage: (type: string, handler: (message: WebSocketMessage) => void) => void;
  offFilesMessage: (type: string, handler: (message: WebSocketMessage) => void) => void;
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

interface WebSocketProviderProps {
  children: ReactNode;
}

export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({ children }) => {
  const [terminalConnected, setTerminalConnected] = useState(false);
  const [filesConnected, setFilesConnected] = useState(false);
  const [terminalConnecting, setTerminalConnecting] = useState(false);
  const [filesConnecting, setFilesConnecting] = useState(false);
  const [terminalMetadata, setTerminalMetadata] = useState<ConnectionMetadata | null>(null);
  const [filesMetadata, setFilesMetadata] = useState<ConnectionMetadata | null>(null);

  // Terminal WebSocket event handlers
  useEffect(() => {
    const handleTerminalStatus = (status: 'connecting' | 'connected' | 'disconnected' | 'error') => {
      console.log('Terminal WebSocket status changed:', status)
      setTerminalConnecting(status === 'connecting');
      setTerminalConnected(status === 'connected');
      
      if (status === 'connected') {
        setTerminalMetadata(terminalWebSocket.getMetadata());
      } else if (status === 'disconnected' || status === 'error') {
        setTerminalMetadata(null);
      }
    };

    const handleFilesStatus = (status: 'connecting' | 'connected' | 'disconnected' | 'error') => {
      console.log('Files WebSocket status changed:', status)
      setFilesConnecting(status === 'connecting');
      setFilesConnected(status === 'connected');
      
      if (status === 'connected') {
        setFilesMetadata(filesWebSocket.getMetadata());
      } else if (status === 'disconnected' || status === 'error') {
        setFilesMetadata(null);
      }
    };

    // Register status handlers
    terminalWebSocket.onConnectionStatus(handleTerminalStatus);
    filesWebSocket.onConnectionStatus(handleFilesStatus);

    // Cleanup on unmount
    return () => {
      terminalWebSocket.offConnectionStatus(handleTerminalStatus);
      filesWebSocket.offConnectionStatus(handleFilesStatus);
      terminalWebSocket.disconnect();
      filesWebSocket.disconnect();
    };
  }, []);

  // Connection methods
  const connectTerminal = async (sessionId: string, token?: string) => {
    console.log('Connecting terminal WebSocket with session:', sessionId);
    terminalWebSocket.updateSessionId(sessionId);
    if (token) {
      terminalWebSocket.updateToken(token);
    }
    await terminalWebSocket.connect();
  };

  const connectFiles = async (sessionId: string, token?: string) => {
    console.log('Connecting files WebSocket with session:', sessionId);
    filesWebSocket.updateSessionId(sessionId);
    if (token) {
      filesWebSocket.updateToken(token);
    }
    await filesWebSocket.connect();
  };

  const disconnectTerminal = () => {
    terminalWebSocket.disconnect();
  };

  const disconnectFiles = () => {
    filesWebSocket.disconnect();
  };

  // Message methods
  const sendTerminalMessage = (message: WebSocketMessage) => {
    console.log('Sending terminal message:', message)
    terminalWebSocket.send(message);
  };

  const sendFilesMessage = (message: WebSocketMessage) => {
    console.log('Sending files message:', message)
    filesWebSocket.send(message);
  };

  // Event handler methods
  const onTerminalMessage = (type: string, handler: (message: WebSocketMessage) => void) => {
    terminalWebSocket.onMessage(type, handler);
  };

  const onFilesMessage = (type: string, handler: (message: WebSocketMessage) => void) => {
    filesWebSocket.onMessage(type, handler);
  };

  const offTerminalMessage = (type: string, handler: (message: WebSocketMessage) => void) => {
    terminalWebSocket.offMessage(type, handler);
  };

  const offFilesMessage = (type: string, handler: (message: WebSocketMessage) => void) => {
    filesWebSocket.offMessage(type, handler);
  };

  const value: WebSocketContextType = {
    terminalConnected,
    filesConnected,
    terminalConnecting,
    filesConnecting,
    terminalMetadata,
    filesMetadata,
    connectTerminal,
    connectFiles,
    disconnectTerminal,
    disconnectFiles,
    sendTerminalMessage,
    sendFilesMessage,
    onTerminalMessage,
    onFilesMessage,
    offTerminalMessage,
    offFilesMessage,
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocket = (): WebSocketContextType => {
  const context = useContext(WebSocketContext);
  if (context === undefined) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
}; 