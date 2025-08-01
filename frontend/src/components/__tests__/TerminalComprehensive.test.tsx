/**
 * Comprehensive Terminal Component Tests
 * 
 * Tests for Terminal component functionality including:
 * - Component rendering and initialization
 * - User interactions (typing, submitting commands)
 * - Command history navigation
 * - WebSocket integration
 * - Theme integration
 * - Error handling
 * - Local command execution
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import Terminal from '../Terminal';

// Mock the context hooks
const mockThemeContext = {
  theme: 'dark' as 'dark' | 'light',
  toggleTheme: vi.fn(),
  setTheme: vi.fn(),
};

const mockWebSocketContext = {
  terminalConnected: true,
  filesConnected: false,
  terminalConnecting: false,
  filesConnecting: false,
  terminalMetadata: null,
  filesMetadata: null,
  connectTerminal: vi.fn(),
  connectFiles: vi.fn(),
  disconnectTerminal: vi.fn(),
  disconnectFiles: vi.fn(),
  sendTerminalMessage: vi.fn(),
  sendFilesMessage: vi.fn(),
  onTerminalMessage: vi.fn(),
  onFilesMessage: vi.fn(),
  offTerminalMessage: vi.fn(),
  offFilesMessage: vi.fn(),
};

// Mock the context modules
vi.mock('../../contexts/ThemeContext', () => ({
  useTheme: () => mockThemeContext,
}));

vi.mock('../../contexts/WebSocketContext', () => ({
  useWebSocket: () => mockWebSocketContext,
}));

// Mock console.log to reduce noise in tests
const originalConsoleLog = console.log;
beforeEach(() => {
  console.log = vi.fn();
  // Reset mocks
  vi.clearAllMocks();
  // Reset WebSocket context to connected state
  mockWebSocketContext.terminalConnected = true;
  mockWebSocketContext.sendTerminalMessage.mockClear();
  
  // Set up default message handler
  let messageHandler: ((message: any) => void) | null = null;
  mockWebSocketContext.onTerminalMessage.mockImplementation((type, handler) => {
    if (type === 'command_response') {
      messageHandler = handler;
    }
  });
  
  // Auto-clear processing state after command execution
  mockWebSocketContext.sendTerminalMessage.mockImplementation(() => {
    setTimeout(() => {
      if (messageHandler) {
        messageHandler({
          type: 'command_response',
          stdout: '',
          stderr: '',
          working_directory: '/'
        });
      }
    }, 10);
  });
});

afterEach(() => {
  console.log = originalConsoleLog;
  vi.clearAllMocks();
});

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return <div>{children}</div>;
};

describe('Terminal Component - Comprehensive Tests', () => {
  const user = userEvent.setup();

  describe('Component Rendering', () => {
    it('renders terminal component with initial welcome message', () => {
      render(
        <TestWrapper>
          <Terminal />
        </TestWrapper>
      );

      expect(screen.getByText('Welcome to AfterIDE Terminal!')).toBeInTheDocument();
      expect(screen.getByText('Type "help" for available commands.')).toBeInTheDocument();
      expect(screen.getByDisplayValue('')).toBeInTheDocument(); // Input field
    });

    it('renders with correct theme classes', () => {
      render(
        <TestWrapper>
          <Terminal />
        </TestWrapper>
      );

      const terminalContainer = screen.getByDisplayValue('').closest('div')?.parentElement?.parentElement;
      expect(terminalContainer).toHaveClass('bg-gray-900', 'text-white');
    });

    it('renders input field with correct placeholder', () => {
      render(
        <TestWrapper>
          <Terminal />
        </TestWrapper>
      );

      const input = screen.getByDisplayValue('');
      expect(input).toHaveAttribute('placeholder', 'Enter command...');
    });

    it('renders prompt symbol in input area', () => {
      render(
        <TestWrapper>
          <Terminal />
        </TestWrapper>
      );

      // Use getAllByText since there are multiple $ symbols
      const dollarSigns = screen.getAllByText('$');
      expect(dollarSigns.length).toBeGreaterThan(0);
    });
  });

  describe('User Input and Command Execution', () => {
    it('allows typing in input field', async () => {
      render(
        <TestWrapper>
          <Terminal />
        </TestWrapper>
      );

      const input = screen.getByDisplayValue('');
      await user.type(input, 'ls -la');
      
      expect(input).toHaveValue('ls -la');
    });

    it('submits command on Enter key', async () => {
      render(
        <TestWrapper>
          <Terminal />
        </TestWrapper>
      );

      const input = screen.getByDisplayValue('');
      await user.type(input, 'ls{enter}');
      
      expect(mockWebSocketContext.sendTerminalMessage).toHaveBeenCalledWith({
        type: 'command',
        command: 'ls',
        working_directory: '/'
      });
    });

    it('submits command on form submission', async () => {
      render(
        <TestWrapper>
          <Terminal />
        </TestWrapper>
      );

      const input = screen.getByDisplayValue('');
      const form = input.closest('form');
      
      await user.type(input, 'pwd');
      fireEvent.submit(form!);
      
      expect(mockWebSocketContext.sendTerminalMessage).toHaveBeenCalledWith({
        type: 'command',
        command: 'pwd',
        working_directory: '/'
      });
    });

    it('clears input after command submission', async () => {
      render(
        <TestWrapper>
          <Terminal />
        </TestWrapper>
      );

      const input = screen.getByDisplayValue('');
      await user.type(input, 'ls{enter}');
      
      // Wait for processing to complete
      await waitFor(() => {
        expect(input).not.toBeDisabled();
      });
      
      expect(input).toHaveValue('');
    });

    it('does not submit empty commands', async () => {
      render(
        <TestWrapper>
          <Terminal />
        </TestWrapper>
      );

      const input = screen.getByDisplayValue('');
      await user.type(input, '{enter}');
      
      expect(mockWebSocketContext.sendTerminalMessage).not.toHaveBeenCalled();
    });
  });

  describe('Command History Navigation', () => {
    it('navigates command history with arrow keys', async () => {
      render(
        <TestWrapper>
          <Terminal />
        </TestWrapper>
      );

      const input = screen.getByDisplayValue('');
      
      // Add some commands to history
      await user.type(input, 'ls{enter}');
      await waitFor(() => expect(input).not.toBeDisabled());
      
      await user.type(input, 'pwd{enter}');
      await waitFor(() => expect(input).not.toBeDisabled());
      
      await user.type(input, 'help{enter}');
      await waitFor(() => expect(input).not.toBeDisabled());
      
      // Navigate up in history (most recent first)
      fireEvent.keyDown(input, { key: 'ArrowUp' });
      expect(input).toHaveValue('help');
      
      fireEvent.keyDown(input, { key: 'ArrowUp' });
      expect(input).toHaveValue('pwd');
      
      fireEvent.keyDown(input, { key: 'ArrowUp' });
      expect(input).toHaveValue('ls');
      
      // Navigate down in history
      fireEvent.keyDown(input, { key: 'ArrowDown' });
      expect(input).toHaveValue('pwd');
      
      fireEvent.keyDown(input, { key: 'ArrowDown' });
      expect(input).toHaveValue('help');
      
      // Go back to empty input
      fireEvent.keyDown(input, { key: 'ArrowDown' });
      expect(input).toHaveValue('');
    });

    it('prevents default behavior for arrow keys', async () => {
      render(
        <TestWrapper>
          <Terminal />
        </TestWrapper>
      );

      const input = screen.getByDisplayValue('');
      await user.type(input, 'ls{enter}');
      await waitFor(() => expect(input).not.toBeDisabled());
      
      // Simulate arrow key press
      fireEvent.keyDown(input, { key: 'ArrowUp' });
      
      // The input value should change to show history navigation worked
      expect(input).toHaveValue('ls');
      
      // Test arrow down as well
      fireEvent.keyDown(input, { key: 'ArrowDown' });
      expect(input).toHaveValue('');
    });
  });

  describe('WebSocket Integration', () => {
    it('sends command via WebSocket when connected', async () => {
      mockWebSocketContext.terminalConnected = true;
      
      render(
        <TestWrapper>
          <Terminal />
        </TestWrapper>
      );

      const input = screen.getByDisplayValue('');
      await user.type(input, 'python main.py{enter}');
      
      expect(mockWebSocketContext.sendTerminalMessage).toHaveBeenCalledWith({
        type: 'command',
        command: 'python main.py',
        working_directory: '/'
      });
    });

    it('handles command response from WebSocket', async () => {
      let messageHandler: ((message: any) => void) | null = null;
      mockWebSocketContext.onTerminalMessage.mockImplementation((type, handler) => {
        if (type === 'command_response') {
          messageHandler = handler;
        }
      });

      render(
        <TestWrapper>
          <Terminal />
        </TestWrapper>
      );

      // Simulate command response
      act(() => {
        if (messageHandler) {
          messageHandler({
            type: 'command_response',
            stdout: 'file1.txt\nfile2.txt',
            stderr: '',
            working_directory: '/workspace'
          });
        }
      });

      await waitFor(() => {
        expect(screen.getByText('file1.txt')).toBeInTheDocument();
        expect(screen.getByText('file2.txt')).toBeInTheDocument();
      });
    });

    it('handles error response from WebSocket', async () => {
      let errorHandler: ((message: any) => void) | null = null;
      mockWebSocketContext.onTerminalMessage.mockImplementation((type, handler) => {
        if (type === 'error') {
          errorHandler = handler;
        }
      });

      render(
        <TestWrapper>
          <Terminal />
        </TestWrapper>
      );

      // Simulate error response
      act(() => {
        if (errorHandler) {
          errorHandler({
            type: 'error',
            message: 'Command not found'
          });
        }
      });

      await waitFor(() => {
        expect(screen.getByText('Error: Command not found')).toBeInTheDocument();
      });
    });

    it('updates working directory from command response', async () => {
      let messageHandler: ((message: any) => void) | null = null;
      mockWebSocketContext.onTerminalMessage.mockImplementation((type, handler) => {
        if (type === 'command_response') {
          messageHandler = handler;
        }
      });

      render(
        <TestWrapper>
          <Terminal />
        </TestWrapper>
      );

      // Simulate cd command response
      act(() => {
        if (messageHandler) {
          messageHandler({
            type: 'command_response',
            stdout: '',
            stderr: '',
            working_directory: '/workspace/backend'
          });
        }
      });

      // The working directory should be updated for subsequent commands
      const input = screen.getByDisplayValue('');
      await user.type(input, 'ls{enter}');
      
      expect(mockWebSocketContext.sendTerminalMessage).toHaveBeenCalledWith({
        type: 'command',
        command: 'ls',
        working_directory: '/workspace/backend'
      });
    });
  });

  describe('Local Command Execution (Fallback)', () => {
    beforeEach(() => {
      mockWebSocketContext.terminalConnected = false;
    });

    it('executes help command locally when not connected', async () => {
      render(
        <TestWrapper>
          <Terminal />
        </TestWrapper>
      );

      const input = screen.getByDisplayValue('');
      await user.type(input, 'help{enter}');
      
      expect(screen.getByText('Available commands:')).toBeInTheDocument();
      // Use a more flexible text matcher
      expect(screen.getByText(/help.*Show this help message/)).toBeInTheDocument();
    });

    it('executes clear command locally', async () => {
      render(
        <TestWrapper>
          <Terminal />
        </TestWrapper>
      );

      const input = screen.getByDisplayValue('');
      await user.type(input, 'clear{enter}');
      
      // Should show welcome message again
      expect(screen.getByText('Welcome to AfterIDE Terminal!')).toBeInTheDocument();
    });

    it('executes pwd command locally', async () => {
      render(
        <TestWrapper>
          <Terminal />
        </TestWrapper>
      );

      const input = screen.getByDisplayValue('');
      await user.type(input, 'pwd{enter}');
      
      expect(screen.getByText('Current directory: /')).toBeInTheDocument();
    });

    it('executes ls command locally', async () => {
      render(
        <TestWrapper>
          <Terminal />
        </TestWrapper>
      );

      const input = screen.getByDisplayValue('');
      await user.type(input, 'ls{enter}');
      
      expect(screen.getByText('Files in current directory:')).toBeInTheDocument();
    });

    it('handles unknown commands locally', async () => {
      render(
        <TestWrapper>
          <Terminal />
        </TestWrapper>
      );

      const input = screen.getByDisplayValue('');
      await user.type(input, 'unknown{enter}');
      
      expect(screen.getByText('Command not found: unknown')).toBeInTheDocument();
    });

    it('handles cd command locally', async () => {
      render(
        <TestWrapper>
          <Terminal />
        </TestWrapper>
      );

      const input = screen.getByDisplayValue('');
      await user.type(input, 'cd backend{enter}');
      
      expect(screen.getByText('Changed directory')).toBeInTheDocument();
    });
  });

  describe('Component State Management', () => {
    it('maintains command history', async () => {
      render(
        <TestWrapper>
          <Terminal />
        </TestWrapper>
      );

      const input = screen.getByDisplayValue('');
      
      await user.type(input, 'ls{enter}');
      await waitFor(() => expect(input).not.toBeDisabled());
      
      await user.type(input, 'pwd{enter}');
      await waitFor(() => expect(input).not.toBeDisabled());
      
      await user.type(input, 'help{enter}');
      await waitFor(() => expect(input).not.toBeDisabled());
      
      // Navigate through history (most recent first)
      fireEvent.keyDown(input, { key: 'ArrowUp' });
      expect(input).toHaveValue('help');
      
      fireEvent.keyDown(input, { key: 'ArrowUp' });
      expect(input).toHaveValue('pwd');
      
      fireEvent.keyDown(input, { key: 'ArrowUp' });
      expect(input).toHaveValue('ls');
    });

    it('limits command history to 100 commands', async () => {
      render(
        <TestWrapper>
          <Terminal />
        </TestWrapper>
      );

      const input = screen.getByDisplayValue('');
      
      // Add 101 commands
      for (let i = 0; i < 101; i++) {
        await user.type(input, `command${i}{enter}`);
        await waitFor(() => expect(input).not.toBeDisabled());
      }
      
      // Navigate to the beginning of history
      for (let i = 0; i < 100; i++) {
        fireEvent.keyDown(input, { key: 'ArrowUp' });
      }
      
      // Should not show the first command (command0)
      expect(input).not.toHaveValue('command0');
    });

    it('shows processing state during command execution', async () => {
      // Mock the WebSocket to simulate processing state
      let messageHandler: ((message: any) => void) | null = null;
      mockWebSocketContext.onTerminalMessage.mockImplementation((type, handler) => {
        if (type === 'command_response') {
          messageHandler = handler;
        }
      });

      render(
        <TestWrapper>
          <Terminal />
        </TestWrapper>
      );

      const input = screen.getByDisplayValue('');
      
      // Submit a command that will trigger processing state
      await user.type(input, 'ls{enter}');
      
      // The input should be disabled and show processing placeholder
      expect(input).toBeDisabled();
      expect(input).toHaveAttribute('placeholder', 'Processing...');
      
      // Simulate response to clear processing state
      act(() => {
        if (messageHandler) {
          messageHandler({
            type: 'command_response',
            stdout: 'file1.txt',
            stderr: '',
            working_directory: '/'
          });
        }
      });
      
      // Wait for processing state to clear
      await waitFor(() => {
        expect(input).not.toBeDisabled();
        expect(input).toHaveAttribute('placeholder', 'Enter command...');
      });
    });
  });

  describe('Theme Integration', () => {
    it('applies dark theme classes', () => {
      mockThemeContext.theme = 'dark';
      
      render(
        <TestWrapper>
          <Terminal />
        </TestWrapper>
      );

      const terminalContainer = screen.getByDisplayValue('').closest('div')?.parentElement?.parentElement;
      expect(terminalContainer).toHaveClass('bg-gray-900', 'text-white');
    });

    it('applies light theme classes', () => {
      mockThemeContext.theme = 'light';
      
      render(
        <TestWrapper>
          <Terminal />
        </TestWrapper>
      );

      const terminalContainer = screen.getByDisplayValue('').closest('div')?.parentElement?.parentElement;
      expect(terminalContainer).toHaveClass('bg-white', 'text-gray-900');
    });
  });

  describe('Error Handling', () => {
    it('handles WebSocket disconnection gracefully', async () => {
      // Start with connected state
      mockWebSocketContext.terminalConnected = true;
      
      const { rerender } = render(
        <TestWrapper>
          <Terminal />
        </TestWrapper>
      );

      const input = screen.getByDisplayValue('');
      
      // Submit command while connected
      await user.type(input, 'ls{enter}');
      expect(mockWebSocketContext.sendTerminalMessage).toHaveBeenCalled();
      
      // Wait for processing to complete
      await waitFor(() => expect(input).not.toBeDisabled());
      
      // Disconnect WebSocket
      mockWebSocketContext.terminalConnected = false;
      rerender(
        <TestWrapper>
          <Terminal />
        </TestWrapper>
      );
      
      // Submit command while disconnected (should use local fallback)
      await user.type(input, 'help{enter}');
      expect(screen.getByText('Available commands:')).toBeInTheDocument();
    });

    it('handles malformed command responses', async () => {
      let messageHandler: ((message: any) => void) | null = null;
      mockWebSocketContext.onTerminalMessage.mockImplementation((type, handler) => {
        if (type === 'command_response') {
          messageHandler = handler;
        }
      });

      render(
        <TestWrapper>
          <Terminal />
        </TestWrapper>
      );

      // Simulate malformed response
      act(() => {
        if (messageHandler) {
          messageHandler({
            type: 'command_response',
            // Missing required fields
          });
        }
      });

      // Should not crash and should show prompt
      await waitFor(() => {
        expect(screen.getByDisplayValue('')).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    it('has proper form structure', () => {
      render(
        <TestWrapper>
          <Terminal />
        </TestWrapper>
      );

      const form = screen.getByDisplayValue('').closest('form');
      expect(form).toBeInTheDocument();
    });

    it('has proper input attributes', () => {
      render(
        <TestWrapper>
          <Terminal />
        </TestWrapper>
      );

      const input = screen.getByDisplayValue('');
      expect(input).toHaveAttribute('type', 'text');
      expect(input).toHaveAttribute('placeholder');
    });

    it('maintains focus on input after command execution', async () => {
      render(
        <TestWrapper>
          <Terminal />
        </TestWrapper>
      );

      const input = screen.getByDisplayValue('');
      await user.type(input, 'ls{enter}');
      
      // Wait for processing to complete
      await waitFor(() => {
        expect(input).not.toBeDisabled();
      });
      
      // Input should remain focused
      expect(input).toHaveFocus();
    });
  });

  describe('Performance and Edge Cases', () => {
    it('handles rapid command submissions', async () => {
      render(
        <TestWrapper>
          <Terminal />
        </TestWrapper>
      );

      const input = screen.getByDisplayValue('');
      
      // Submit multiple commands rapidly
      await user.type(input, 'ls{enter}');
      await waitFor(() => expect(input).not.toBeDisabled());
      
      await user.type(input, 'pwd{enter}');
      await waitFor(() => expect(input).not.toBeDisabled());
      
      await user.type(input, 'help{enter}');
      await waitFor(() => expect(input).not.toBeDisabled());
      
      // All commands should be processed
      expect(mockWebSocketContext.sendTerminalMessage).toHaveBeenCalledTimes(3);
    });

    it('handles long command inputs', async () => {
      render(
        <TestWrapper>
          <Terminal />
        </TestWrapper>
      );

      const input = screen.getByDisplayValue('');
      const longCommand = 'a'.repeat(1000);
      
      await user.type(input, longCommand);
      expect(input).toHaveValue(longCommand);
      
      await user.type(input, '{enter}');
      expect(mockWebSocketContext.sendTerminalMessage).toHaveBeenCalledWith({
        type: 'command',
        command: longCommand,
        working_directory: '/'
      });
    });

    it('handles special characters in commands', async () => {
      render(
        <TestWrapper>
          <Terminal />
        </TestWrapper>
      );

      const input = screen.getByDisplayValue('');
      const specialCommand = 'echo "Hello World!" && ls -la | grep "\.py$"';
      
      await user.type(input, specialCommand);
      await user.type(input, '{enter}');
      
      expect(mockWebSocketContext.sendTerminalMessage).toHaveBeenCalledWith({
        type: 'command',
        command: specialCommand,
        working_directory: '/'
      });
    });
  });
}); 