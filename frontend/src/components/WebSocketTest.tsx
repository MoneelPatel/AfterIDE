/**
 * AfterIDE - WebSocket Test Component
 * 
 * Test component to demonstrate WebSocket functionality.
 */

import React, { useState, useEffect } from 'react';
import { useWebSocket } from '../contexts/WebSocketContext';
import { WebSocketMessage } from '../services/websocket';

const WebSocketTest: React.FC = () => {
  const {
    terminalConnected,
    filesConnected,
    terminalConnecting,
    filesConnecting,
    connectTerminal,
    connectFiles,
    disconnectTerminal,
    disconnectFiles,
    sendTerminalMessage,
    sendFilesMessage,
    onTerminalMessage,
    offTerminalMessage,
    onFilesMessage,
    offFilesMessage,
  } = useWebSocket();

  const [terminalMessages, setTerminalMessages] = useState<WebSocketMessage[]>([]);
  const [filesMessages, setFilesMessages] = useState<WebSocketMessage[]>([]);
  const [testCommand, setTestCommand] = useState('echo "Hello, WebSocket!"');
  const [testFileContent, setTestFileContent] = useState('print("Hello, World!")');

  // Terminal message handler
  useEffect(() => {
    const handleTerminalMessage = (message: WebSocketMessage) => {
      setTerminalMessages(prev => [...prev, message]);
    };

    onTerminalMessage('*', handleTerminalMessage);

    return () => {
      offTerminalMessage('*', handleTerminalMessage);
    };
  }, [onTerminalMessage, offTerminalMessage]);

  // Files message handler
  useEffect(() => {
    const handleFilesMessage = (message: WebSocketMessage) => {
      setFilesMessages(prev => [...prev, message]);
    };

    onFilesMessage('*', handleFilesMessage);

    return () => {
      offFilesMessage('*', handleFilesMessage);
    };
  }, [onFilesMessage, offFilesMessage]);

  const handleConnectTerminal = () => {
    connectTerminal('test-session', 'test-token');
  };

  const handleConnectFiles = () => {
    connectFiles('test-session', 'test-token');
  };

  const handleSendTerminalCommand = () => {
    sendTerminalMessage({
      type: 'command',
      command: testCommand,
    });
  };

  const handleSendFileUpdate = () => {
    sendFilesMessage({
      type: 'file_update',
      filename: 'test.py',
      content: testFileContent,
      language: 'python',
    });
  };

  const handleRequestFile = () => {
    sendFilesMessage({
      type: 'file_request',
      filename: 'test.py',
    });
  };

  const handleRequestFileList = () => {
    sendFilesMessage({
      type: 'file_list',
      directory: '/',
    });
  };

  const clearMessages = (type: 'terminal' | 'files') => {
    if (type === 'terminal') {
      setTerminalMessages([]);
    } else {
      setFilesMessages([]);
    }
  };

  return (
    <div className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow-lg">
      <h2 className="text-2xl font-bold mb-6 text-gray-900 dark:text-white">
        WebSocket Test Panel
      </h2>

      {/* Connection Controls */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        {/* Terminal Connection */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Terminal Connection
          </h3>
          <div className="flex space-x-2">
            <button
              onClick={handleConnectTerminal}
              disabled={terminalConnecting || terminalConnected}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {terminalConnecting ? 'Connecting...' : terminalConnected ? 'Connected' : 'Connect'}
            </button>
            <button
              onClick={disconnectTerminal}
              disabled={!terminalConnected}
              className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Disconnect
            </button>
          </div>
        </div>

        {/* Files Connection */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Files Connection
          </h3>
          <div className="flex space-x-2">
            <button
              onClick={handleConnectFiles}
              disabled={filesConnecting || filesConnected}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {filesConnecting ? 'Connecting...' : filesConnected ? 'Connected' : 'Connect'}
            </button>
            <button
              onClick={disconnectFiles}
              disabled={!filesConnected}
              className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Disconnect
            </button>
          </div>
        </div>
      </div>

      {/* Test Controls */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        {/* Terminal Tests */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Terminal Tests
          </h3>
          <div className="space-y-2">
            <input
              type="text"
              value={testCommand}
              onChange={(e) => setTestCommand(e.target.value)}
              placeholder="Enter command to test"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
            <button
              onClick={handleSendTerminalCommand}
              disabled={!terminalConnected}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Send Command
            </button>
          </div>
        </div>

        {/* Files Tests */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Files Tests
          </h3>
          <div className="space-y-2">
            <textarea
              value={testFileContent}
              onChange={(e) => setTestFileContent(e.target.value)}
              placeholder="Enter file content to test"
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
            <div className="flex space-x-2">
              <button
                onClick={handleSendFileUpdate}
                disabled={!filesConnected}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Update File
              </button>
              <button
                onClick={handleRequestFile}
                disabled={!filesConnected}
                className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Request File
              </button>
            </div>
            <button
              onClick={handleRequestFileList}
              disabled={!filesConnected}
              className="w-full px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Request File List
            </button>
          </div>
        </div>
      </div>

      {/* Message Logs */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Terminal Messages */}
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Terminal Messages
            </h3>
            <button
              onClick={() => clearMessages('terminal')}
              className="px-2 py-1 text-sm bg-gray-600 text-white rounded hover:bg-gray-700"
            >
              Clear
            </button>
          </div>
          <div className="h-64 overflow-y-auto bg-gray-100 dark:bg-gray-900 rounded-md p-4">
            {terminalMessages.length === 0 ? (
              <p className="text-gray-500 dark:text-gray-400 text-sm">No messages yet</p>
            ) : (
              terminalMessages.map((msg, index) => (
                <div key={index} className="mb-2 p-2 bg-white dark:bg-gray-800 rounded border">
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    {msg.type} - {new Date().toLocaleTimeString()}
                  </div>
                  <pre className="text-sm text-gray-900 dark:text-white mt-1">
                    {JSON.stringify(msg, null, 2)}
                  </pre>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Files Messages */}
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Files Messages
            </h3>
            <button
              onClick={() => clearMessages('files')}
              className="px-2 py-1 text-sm bg-gray-600 text-white rounded hover:bg-gray-700"
            >
              Clear
            </button>
          </div>
          <div className="h-64 overflow-y-auto bg-gray-100 dark:bg-gray-900 rounded-md p-4">
            {filesMessages.length === 0 ? (
              <p className="text-gray-500 dark:text-gray-400 text-sm">No messages yet</p>
            ) : (
              filesMessages.map((msg, index) => (
                <div key={index} className="mb-2 p-2 bg-white dark:bg-gray-800 rounded border">
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    {msg.type} - {new Date().toLocaleTimeString()}
                  </div>
                  <pre className="text-sm text-gray-900 dark:text-white mt-1">
                    {JSON.stringify(msg, null, 2)}
                  </pre>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default WebSocketTest; 