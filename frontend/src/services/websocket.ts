/**
 * AfterIDE - WebSocket Client Service
 * 
 * Manages WebSocket connections for real-time terminal and file synchronization.
 */

export interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

export interface ConnectionMetadata {
  connectionId: string;
  sessionId: string;
  userId?: string;
  connectionType: 'terminal' | 'files';
  connectedAt: Date;
}

export interface WebSocketConfig {
  url: string;
  sessionId: string;
  token?: string;
  connectionType: 'terminal' | 'files';
  maxReconnectAttempts?: number;
  reconnectDelay?: number;
  heartbeatInterval?: number;
}

export type MessageHandler = (message: WebSocketMessage) => void;
export type ConnectionStatusHandler = (status: 'connecting' | 'connected' | 'disconnected' | 'error') => void;

class WebSocketClient {
  private ws: WebSocket | null = null;
  private config: WebSocketConfig;
  private reconnectAttempts = 0;
  private maxReconnectAttempts: number;
  private reconnectDelay: number;
  private heartbeatInterval: number;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private messageHandlers: Map<string, Set<MessageHandler>> = new Map();
  private connectionStatusHandlers: Set<ConnectionStatusHandler> = new Set();
  private messageQueue: WebSocketMessage[] = [];
  private isConnecting = false;
  private isConnected = false;
  private metadata: ConnectionMetadata | null = null;

  constructor(config: WebSocketConfig) {
    this.config = config;
    this.maxReconnectAttempts = config.maxReconnectAttempts || 5;
    this.reconnectDelay = config.reconnectDelay || 1000;
    this.heartbeatInterval = config.heartbeatInterval || 30000;
  }

  /**
   * Connect to WebSocket server
   */
  async connect(): Promise<void> {
    if (this.isConnecting || this.isConnected) {
      return;
    }

    // Don't attempt to connect if there's no token (user is not authenticated)
    if (!this.config.token) {
      console.log('No token available, skipping WebSocket connection');
      this.notifyConnectionStatus('disconnected');
      return;
    }

    this.isConnecting = true;
    this.notifyConnectionStatus('connecting');

    try {
      // Build WebSocket URL with path parameters
      const baseUrl = this.config.url.replace(/\/$/, ''); // Remove trailing slash if present
      const url = `${baseUrl}/${this.config.sessionId}`;
      
      // Add token as query parameter if provided
      const finalUrl = this.config.token ? `${url}?token=${this.config.token}` : url;

      this.ws = new WebSocket(finalUrl);

      this.ws.onopen = this.handleOpen.bind(this);
      this.ws.onmessage = this.handleMessage.bind(this);
      this.ws.onclose = this.handleClose.bind(this);
      this.ws.onerror = this.handleError.bind(this);

    } catch (error) {
      console.error('WebSocket connection error:', error);
      this.isConnecting = false;
      this.notifyConnectionStatus('error');
      this.scheduleReconnect();
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    this.isConnecting = false;
    this.isConnected = false;
    this.reconnectAttempts = 0;

    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.notifyConnectionStatus('disconnected');
  }

  /**
   * Send message to WebSocket server
   */
  send(message: WebSocketMessage): void {
    if (!this.isConnected) {
      // Queue message for later if not connected
      this.messageQueue.push(message);
      return;
    }

    try {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify(message));
      } else {
        this.messageQueue.push(message);
      }
    } catch (error) {
      console.error('Failed to send WebSocket message:', error);
      this.messageQueue.push(message);
    }
  }

  /**
   * Register message handler for specific message type
   */
  onMessage(type: string, handler: MessageHandler): void {
    if (!this.messageHandlers.has(type)) {
      this.messageHandlers.set(type, new Set());
    }
    this.messageHandlers.get(type)!.add(handler);
  }

  /**
   * Unregister message handler
   */
  offMessage(type: string, handler: MessageHandler): void {
    const handlers = this.messageHandlers.get(type);
    if (handlers) {
      handlers.delete(handler);
      if (handlers.size === 0) {
        this.messageHandlers.delete(type);
      }
    }
  }

  /**
   * Register connection status handler
   */
  onConnectionStatus(handler: ConnectionStatusHandler): void {
    this.connectionStatusHandlers.add(handler);
  }

  /**
   * Unregister connection status handler
   */
  offConnectionStatus(handler: ConnectionStatusHandler): void {
    this.connectionStatusHandlers.delete(handler);
  }

  /**
   * Get connection status
   */
  getConnectionStatus(): { isConnected: boolean; isConnecting: boolean } {
    return {
      isConnected: this.isConnected,
      isConnecting: this.isConnecting
    };
  }

  /**
   * Get connection metadata
   */
  getMetadata(): ConnectionMetadata | null {
    return this.metadata;
  }

  /**
   * Update session ID
   */
  updateSessionId(sessionId: string): void {
    // Only update if the session ID has actually changed
    if (this.config.sessionId !== sessionId) {
      console.log(`Updating session ID from ${this.config.sessionId} to ${sessionId}`);
      this.config.sessionId = sessionId;
    }
  }

  /**
   * Update authentication token
   */
  updateToken(token: string): void {
    const hadToken = !!this.config.token;
    const hasToken = !!token;
    
    this.config.token = token;
    
    // If we had a token but now don't, disconnect
    if (hadToken && !hasToken) {
      console.log('Token cleared, disconnecting WebSocket');
      this.disconnect();
    }
  }

  /**
   * Handle WebSocket open event
   */
  private handleOpen(): void {
    console.log('WebSocket connected');
    this.isConnecting = false;
    this.isConnected = true;
    this.reconnectAttempts = 0;
    this.notifyConnectionStatus('connected');

    // Start heartbeat
    this.startHeartbeat();

    // Send queued messages
    this.flushMessageQueue();
  }

  /**
   * Handle WebSocket message event
   */
  private handleMessage(event: MessageEvent): void {
    try {
      const message: WebSocketMessage = JSON.parse(event.data);
      
      // Handle connection establishment
      if (message.type === 'connection_established') {
        this.metadata = {
          connectionId: message.connection_id,
          sessionId: message.session_id,
          userId: message.user_id,
          connectionType: this.config.connectionType,
          connectedAt: new Date()
        };
        console.log('Connection established:', this.metadata);
      }

      // Handle pong response
      if (message.type === 'pong') {
        // Heartbeat response received
        return;
      }

      // Route message to handlers
      const handlers = this.messageHandlers.get(message.type);
      if (handlers) {
        handlers.forEach(handler => {
          try {
            handler(message);
          } catch (error) {
            console.error('Message handler error:', error);
          }
        });
      }

      // Also call wildcard handlers
      const wildcardHandlers = this.messageHandlers.get('*');
      if (wildcardHandlers) {
        wildcardHandlers.forEach(handler => {
          try {
            handler(message);
          } catch (error) {
            console.error('Wildcard message handler error:', error);
          }
        });
      }

    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
    }
  }

  /**
   * Handle WebSocket close event
   */
  private handleClose(event: CloseEvent): void {
    console.log('WebSocket disconnected:', event.code, event.reason);
    this.isConnecting = false;
    this.isConnected = false;

    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }

    this.notifyConnectionStatus('disconnected');

    // Attempt reconnection if not manually closed
    if (event.code !== 1000) {
      this.scheduleReconnect();
    }
  }

  /**
   * Handle WebSocket error event
   */
  private handleError(event: Event): void {
    console.error('WebSocket error:', event);
    this.isConnecting = false;
    this.isConnected = false;
    this.notifyConnectionStatus('error');
  }

  /**
   * Schedule reconnection attempt
   */
  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }

    // Don't attempt to reconnect if there's no token (user is not authenticated)
    if (!this.config.token) {
      console.log('No token available, skipping reconnection attempt');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1); // Exponential backoff

    console.log(`Scheduling reconnection attempt ${this.reconnectAttempts} in ${delay}ms`);

    setTimeout(() => {
      if (!this.isConnected && !this.isConnecting) {
        this.connect();
      }
    }, delay);
  }

  /**
   * Start heartbeat to keep connection alive
   */
  private startHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
    }

    this.heartbeatTimer = setInterval(() => {
      if (this.isConnected) {
        this.send({ type: 'ping' });
      }
    }, this.heartbeatInterval);
  }

  /**
   * Flush queued messages
   */
  private flushMessageQueue(): void {
    while (this.messageQueue.length > 0) {
      const message = this.messageQueue.shift();
      if (message) {
        this.send(message);
      }
    }
  }

  /**
   * Notify connection status handlers
   */
  private notifyConnectionStatus(status: 'connecting' | 'connected' | 'disconnected' | 'error'): void {
    this.connectionStatusHandlers.forEach(handler => {
      try {
        handler(status);
      } catch (error) {
        console.error('Connection status handler error:', error);
      }
    });
  }
}

// WebSocket manager instances
const getWebSocketUrl = (endpoint: string) => {
  // Check if we have a production WebSocket URL configured
  const wsBaseUrl = import.meta.env.VITE_WS_URL;
  
  if (wsBaseUrl) {
    // Use the configured WebSocket URL for production
    return `${wsBaseUrl}${endpoint}`;
  }
  
  // Check if we're running on Railway (production)
  if (window.location.hostname.includes('railway.app')) {
    // Use the backend Railway URL for WebSocket connections
    return `wss://sad-chess-production.up.railway.app${endpoint}`;
  }
  
  // Check if we're in development mode
  if (import.meta.env.DEV) {
    // In development, use the current window location to build WebSocket URL
    // This will use the Vite dev server proxy to forward to the backend
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host; // This includes port
    return `${protocol}//${host}${endpoint}`;
  }
  
  // Fallback for production without environment variable
  // Use the backend Railway URL as default
  const url = `wss://sad-chess-production.up.railway.app${endpoint}`;
  console.log('Using fallback URL:', url);
  return url;
};

// Get user session ID from auth store
const getUserSessionId = async (): Promise<string> => {
  const token = localStorage.getItem('authToken');
  if (!token) {
    console.log('No auth token found, using default session');
    return 'default-session';
  }
  
  try {
    console.log('Fetching session ID from backend...');
    
    // Build the URL properly for different environments
    let url = '/api/v1/sessions/current';
    if (typeof window !== 'undefined' && window.location) {
      // In browser environment, use relative URL
      url = '/api/v1/sessions/current';
    } else {
      // In test environment, use a mock URL
      url = 'http://localhost:8000/api/v1/sessions/current';
    }
    
    // Get the actual session ID from the backend
    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Accept': 'application/json'
      }
    });
    
    if (response.ok) {
      // Check if the response is actually JSON
      const contentType = response.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        console.warn('Backend returned non-JSON response, server may not be running');
        return 'default-session';
      }
      
      const data = await response.json();
      const sessionId = data.session_id || 'default-session';
      console.log('Successfully fetched session ID from backend:', sessionId);
      return sessionId;
    } else if (response.status === 401) {
      console.warn('Authentication failed when fetching session ID, user may need to re-authenticate');
      // Clear the invalid token
      localStorage.removeItem('authToken');
      return 'default-session';
    } else {
      console.warn('Failed to get session ID from backend, using fallback. Status:', response.status);
      return 'default-session';
    }
  } catch (error) {
    console.error('Error fetching session ID:', error);
    
    // Handle specific error types
    if (error instanceof TypeError && error.message.includes('Invalid URL')) {
      console.warn('Invalid URL in fetch, clearing token and using default session');
      localStorage.removeItem('authToken');
    } else if (error instanceof SyntaxError && error.message.includes('Unexpected token')) {
      console.warn('Backend returned invalid JSON (possibly HTML), server may not be running');
      // Don't clear the token in this case, as it might be a temporary server issue
    } else if (error instanceof TypeError && error.message.includes('fetch')) {
      console.warn('Network error when fetching session ID, backend may not be running');
    }
    
    return 'default-session';
  }
};

// Synchronous version for backward compatibility (returns a promise)
const getUserSessionIdSync = (): string => {
  const token = localStorage.getItem('authToken');
  if (!token) {
    return 'default-session';
  }
  
  // For backward compatibility, use a simple hash but this should be replaced
  // with the async version that gets the real session ID from the backend
  let hash = 0;
  for (let i = 0; i < token.length; i++) {
    const char = token.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32-bit integer
  }
  return `user-${Math.abs(hash)}`;
};

// Get authentication token
const getAuthToken = (): string | null => {
  return localStorage.getItem('authToken');
};

const terminalWebSocket = new WebSocketClient({
  url: getWebSocketUrl('/ws/terminal'),
  sessionId: getUserSessionIdSync(),
  token: getAuthToken() || undefined,
  connectionType: 'terminal',
  maxReconnectAttempts: 5,
  reconnectDelay: 1000,
  heartbeatInterval: 30000
});

const filesWebSocket = new WebSocketClient({
  url: getWebSocketUrl('/ws/files'),
  sessionId: getUserSessionIdSync(),
  token: getAuthToken() || undefined,
  connectionType: 'files',
  maxReconnectAttempts: 5,
  reconnectDelay: 1000,
  heartbeatInterval: 30000
});

// Function to update WebSocket sessions when user logs in/out
export const updateWebSocketSessions = async () => {
  const newToken = getAuthToken();
  
  console.log('🔄 updateWebSocketSessions called with token:', newToken ? 'present' : 'none');
  
  // Get current connection status
  const terminalStatus = terminalWebSocket.getConnectionStatus();
  const filesStatus = filesWebSocket.getConnectionStatus();
  
  console.log('📊 Current connection status - Terminal:', terminalStatus.isConnected, 'Files:', filesStatus.isConnected);
  
  // If user has logged out (no token), disconnect and don't reconnect
  if (!newToken) {
    console.log('🚫 No token found, disconnecting WebSockets');
    if (terminalStatus.isConnected) {
      terminalWebSocket.disconnect();
    }
    if (filesStatus.isConnected) {
      filesWebSocket.disconnect();
    }
    return;
  }
  
  try {
    // Get the actual session ID from the backend
    const newSessionId = await getUserSessionId();
    console.log('✅ Got session ID from backend:', newSessionId);
    
    // If we got the default session ID, it means authentication failed or backend is not available
    if (newSessionId === 'default-session') {
      console.log('⚠️ Backend not available or authentication failed, using fallback session ID');
      // Use the synchronous fallback for authenticated users
      const fallbackSessionId = getUserSessionIdSync();
      console.log('🔄 Using fallback session ID:', fallbackSessionId);
      
      // Update session and token
      terminalWebSocket.updateSessionId(fallbackSessionId);
      terminalWebSocket.updateToken(newToken);
      
      filesWebSocket.updateSessionId(fallbackSessionId);
      filesWebSocket.updateToken(newToken);
      
      // Only reconnect if currently connected and session/token changed
      const currentTerminalSession = terminalWebSocket.getMetadata()?.sessionId;
      const currentFilesSession = filesWebSocket.getMetadata()?.sessionId;
      
      if (terminalStatus.isConnected && currentTerminalSession !== fallbackSessionId) {
        console.log('🔄 Reconnecting terminal WebSocket with fallback session');
        terminalWebSocket.disconnect();
        setTimeout(() => terminalWebSocket.connect(), 100);
      }
      
      if (filesStatus.isConnected && currentFilesSession !== fallbackSessionId) {
        console.log('🔄 Reconnecting files WebSocket with fallback session');
        filesWebSocket.disconnect();
        setTimeout(() => filesWebSocket.connect(), 100);
      }
      return;
    }
    
    // Get current session IDs for comparison
    const currentTerminalSession = terminalWebSocket.getMetadata()?.sessionId;
    const currentFilesSession = filesWebSocket.getMetadata()?.sessionId;
    
    console.log('🔄 Session ID comparison - Terminal:', currentTerminalSession, '->', newSessionId);
    console.log('🔄 Session ID comparison - Files:', currentFilesSession, '->', newSessionId);
    
    // Update session and token
    terminalWebSocket.updateSessionId(newSessionId);
    terminalWebSocket.updateToken(newToken);
    
    filesWebSocket.updateSessionId(newSessionId);
    filesWebSocket.updateToken(newToken);
    
    // Only reconnect if currently connected and session/token changed
    if (terminalStatus.isConnected && currentTerminalSession !== newSessionId) {
      console.log('🔄 Reconnecting terminal WebSocket with new session');
      terminalWebSocket.disconnect();
      setTimeout(() => terminalWebSocket.connect(), 100); // Small delay to prevent race conditions
    }
    
    if (filesStatus.isConnected && currentFilesSession !== newSessionId) {
      console.log('🔄 Reconnecting files WebSocket with new session');
      filesWebSocket.disconnect();
      setTimeout(() => filesWebSocket.connect(), 100); // Small delay to prevent race conditions
    }
  } catch (error) {
    console.error('❌ Failed to update WebSocket sessions:', error);
    // Fallback to synchronous version
    const fallbackSessionId = getUserSessionIdSync();
    console.log('🔄 Using fallback session ID:', fallbackSessionId);
    terminalWebSocket.updateSessionId(fallbackSessionId);
    terminalWebSocket.updateToken(newToken);
    filesWebSocket.updateSessionId(fallbackSessionId);
    filesWebSocket.updateToken(newToken);
  }
};

export { WebSocketClient, terminalWebSocket, filesWebSocket, getUserSessionId, getUserSessionIdSync, getAuthToken }; 