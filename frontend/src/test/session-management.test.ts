/**
 * Session Management Test
 * 
 * Tests for verifying that session IDs are properly managed between
 * frontend and backend to ensure file persistence across login/logout cycles.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { getUserSessionId, getUserSessionIdSync } from '../services/websocket';

// Mock localStorage
const mockLocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
};

Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
});

// Mock fetch
global.fetch = vi.fn();

describe('Session Management', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getUserSessionId', () => {
    it('should return default session when no token is present', async () => {
      mockLocalStorage.getItem.mockReturnValue(null);
      
      const sessionId = await getUserSessionId();
      
      expect(sessionId).toBe('default-session');
      expect(mockLocalStorage.getItem).toHaveBeenCalledWith('authToken');
    });

    it('should fetch session ID from backend when token is present', async () => {
      const mockToken = 'test-token';
      const mockSessionId = 'user-session-123';
      
      mockLocalStorage.getItem.mockReturnValue(mockToken);
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ session_id: mockSessionId }),
      });
      
      const sessionId = await getUserSessionId();
      
      expect(sessionId).toBe(mockSessionId);
      expect(global.fetch).toHaveBeenCalledWith('/api/v1/sessions/current', {
        headers: {
          'Authorization': `Bearer ${mockToken}`,
        },
      });
    });

    it('should return default session when backend request fails', async () => {
      const mockToken = 'test-token';
      
      mockLocalStorage.getItem.mockReturnValue(mockToken);
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 500,
      });
      
      const sessionId = await getUserSessionId();
      
      expect(sessionId).toBe('default-session');
    });

    it('should return default session when backend request throws error', async () => {
      const mockToken = 'test-token';
      
      mockLocalStorage.getItem.mockReturnValue(mockToken);
      (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));
      
      const sessionId = await getUserSessionId();
      
      expect(sessionId).toBe('default-session');
    });
  });

  describe('getUserSessionIdSync', () => {
    it('should return default session when no token is present', () => {
      mockLocalStorage.getItem.mockReturnValue(null);
      
      const sessionId = getUserSessionIdSync();
      
      expect(sessionId).toBe('default-session');
    });

    it('should generate consistent session ID from token hash', () => {
      const mockToken = 'test-token';
      
      mockLocalStorage.getItem.mockReturnValue(mockToken);
      
      const sessionId1 = getUserSessionIdSync();
      const sessionId2 = getUserSessionIdSync();
      
      expect(sessionId1).toBe(sessionId2);
      expect(sessionId1).toMatch(/^user-\d+$/);
    });

    it('should generate different session IDs for different tokens', () => {
      const mockToken1 = 'test-token-1';
      const mockToken2 = 'test-token-2';
      
      mockLocalStorage.getItem.mockReturnValueOnce(mockToken1);
      const sessionId1 = getUserSessionIdSync();
      
      mockLocalStorage.getItem.mockReturnValueOnce(mockToken2);
      const sessionId2 = getUserSessionIdSync();
      
      expect(sessionId1).not.toBe(sessionId2);
    });
  });
}); 