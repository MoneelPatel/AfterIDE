import React, { useEffect, useRef, useState, useCallback } from 'react'
import { useTheme } from '../contexts/ThemeContext'
import { useWebSocket } from '../contexts/WebSocketContext'

interface TerminalProps {
  onCommand?: (command: string) => void
  output?: string
  isConnected?: boolean
}

interface TerminalLine {
  text: string
  type: 'output' | 'error' | 'success' | 'prompt' | 'command'
  timestamp: number
}

const Terminal: React.FC<TerminalProps> = ({ onCommand, output, isConnected = true }) => {
  const [commandHistory, setCommandHistory] = useState<string[]>([])
  const [historyIndex, setHistoryIndex] = useState(-1)
  const [isProcessing, setIsProcessing] = useState(false)
  const [currentInput, setCurrentInput] = useState('')
  const [terminalOutput, setTerminalOutput] = useState<TerminalLine[]>([])
  const [isInitialized, setIsInitialized] = useState(false)
  const initializedRef = useRef(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const outputRef = useRef<HTMLDivElement>(null)
  const { theme } = useTheme()
  const { 
    terminalConnected, 
    sendTerminalMessage, 
    onTerminalMessage, 
    offTerminalMessage 
  } = useWebSocket()

  // Add output to terminal
  const addOutput = useCallback((text: string, type: 'output' | 'error' | 'success' | 'prompt' | 'command' = 'output') => {
    // Split text by line breaks and add each line separately
    const lines = text.split('\n')
    lines.forEach((line) => {
      // Add all lines, including empty ones, to preserve formatting
      setTerminalOutput(prev => [...prev, { text: line, type, timestamp: Date.now() }])
    })
  }, [])

  // Focus input
  const focusInput = useCallback(() => {
    setTimeout(() => {
      if (inputRef.current) {
        inputRef.current.focus()
      }
    }, 100)
  }, [])

  // Handle command responses from backend
  useEffect(() => {
    const handleCommandResponse = (message: any) => {
      if (message.type === 'command_response') {
        setIsProcessing(false)
        
        // Display stdout
        if (message.stdout) {
          addOutput(message.stdout, 'output')
        }
        
        // Display stderr
        if (message.stderr) {
          addOutput(message.stderr, 'error')
        }
        
        // Show prompt
        addOutput('  $ ', 'prompt')
        focusInput()
      }
    }

    const handleError = (message: any) => {
      if (message.type === 'error') {
        setIsProcessing(false)
        addOutput(`Error: ${message.message}`, 'error')
        addOutput('  $ ', 'prompt')
        focusInput()
      }
    }

    // Register message handlers
    onTerminalMessage('command_response', handleCommandResponse)
    onTerminalMessage('error', handleError)

    return () => {
      offTerminalMessage('command_response', handleCommandResponse)
      offTerminalMessage('error', handleError)
    }
  }, [onTerminalMessage, offTerminalMessage, addOutput, focusInput])

  // Handle connection status changes
  useEffect(() => {
    console.log('Terminal connection status changed:', terminalConnected)
    // Removed connection status messages to clean up terminal output
  }, [terminalConnected])

  // Handle command execution
  const executeCommand = useCallback((command: string) => {
    console.log('Executing command:', command)
    if (!command.trim()) return

    // Add to history
    const newHistory = [...commandHistory, command.trim()]
    setCommandHistory(newHistory.slice(-100)) // Keep last 100 commands
    setHistoryIndex(newHistory.length)

    // Show command echo
    addOutput(`  $ ${command}`, 'command')

    // Send command to backend if connected
    if (terminalConnected) {
      console.log('Sending command to backend via WebSocket')
      setIsProcessing(true)
      sendTerminalMessage({
        type: 'command',
        command: command.trim()
      })
    } else {
      console.log('Backend not connected, using local command handling')
      // Fallback to local command handling
      handleLocalCommand(command.trim())
    }
  }, [commandHistory, terminalConnected, sendTerminalMessage, addOutput])

  // Local command handling for when backend is not available
  const handleLocalCommand = (command: string) => {
    const cmd = command.toLowerCase()
    
    if (cmd === 'help') {
      addOutput('  Available commands:', 'output')
      addOutput('    help     - Show this help message', 'output')
      addOutput('    ls       - List files', 'output')
      addOutput('    clear    - Clear terminal', 'output')
      addOutput('    pwd      - Show current directory', 'output')
      addOutput('    python   - Run Python code', 'output')
      addOutput('    cat      - Display file contents', 'output')
      addOutput('    cd       - Change directory', 'output')
      addOutput('', 'output')
    } else if (cmd === 'clear') {
      setTerminalOutput([])
      addOutput('  Welcome to AfterIDE Terminal!', 'output')
      addOutput('  Type "help" for available commands.', 'output')
      addOutput('', 'output')
    } else if (cmd === 'ls') {
      addOutput('  Files in current directory:', 'output')
      addOutput('    main.py', 'output')
      addOutput('    requirements.txt', 'output')
      addOutput('    README.md', 'output')
      addOutput('    src/', 'output')
      addOutput('', 'output')
    } else if (cmd === 'pwd') {
      addOutput('  Current directory: /workspace', 'output')
      addOutput('', 'output')
    } else if (cmd.startsWith('python ') || cmd.startsWith('python3 ')) {
      addOutput('  Running Python code...', 'output')
      addOutput('  (Backend connection required for Python execution)', 'output')
      addOutput('', 'output')
    } else if (cmd.startsWith('cat ')) {
      addOutput('  Displaying file contents...', 'output')
      addOutput('  (Backend connection required for file operations)', 'output')
      addOutput('', 'output')
    } else if (cmd.startsWith('cd ')) {
      addOutput('  Changing directory...', 'output')
      addOutput('  (Backend connection required for directory navigation)', 'output')
      addOutput('', 'output')
    } else {
      addOutput(`  Command not found: ${command}`, 'error')
      addOutput('  Type "help" for available commands.', 'output')
      addOutput('', 'output')
    }

    // Always show prompt after command execution
    addOutput('  $ ', 'prompt')
    focusInput()
  }

  // Handle input submission
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (currentInput.trim()) {
      executeCommand(currentInput.trim())
      setCurrentInput('')
      setHistoryIndex(commandHistory.length)
    }
  }

  // Handle key down for history navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowUp') {
      e.preventDefault()
      if (historyIndex > 0) {
        const newIndex = historyIndex - 1
        setHistoryIndex(newIndex)
        if (commandHistory[newIndex]) {
          setCurrentInput(commandHistory[newIndex])
        }
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      if (historyIndex < commandHistory.length - 1) {
        const newIndex = historyIndex + 1
        setHistoryIndex(newIndex)
        if (commandHistory[newIndex]) {
          setCurrentInput(commandHistory[newIndex])
        }
      } else if (historyIndex === commandHistory.length - 1) {
        setHistoryIndex(commandHistory.length)
        setCurrentInput('')
      }
    }
  }

  // Initialize terminal
  useEffect(() => {
    if (!initializedRef.current) {
      addOutput('  Welcome to AfterIDE Terminal!', 'output')
      addOutput('  Type "help" for available commands.', 'output')
      addOutput('', 'output')
      addOutput('  $ ', 'prompt')
      focusInput()
      initializedRef.current = true
    }
  }, [addOutput, focusInput])

  // Scroll to bottom when output changes
  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight
    }
  }, [terminalOutput])

  // Handle output updates
  useEffect(() => {
    if (output) {
      addOutput(output, 'output')
    }
  }, [output, addOutput])

  const getOutputClass = (type: string) => {
    switch (type) {
      case 'error':
        return 'text-red-500'
      case 'success':
        return 'text-green-500'
      case 'command':
        return 'text-yellow-500'
      case 'prompt':
        return 'text-green-400 font-bold'
      default:
        return 'text-gray-300'
    }
  }

  return (
    <div 
      className={`h-full flex flex-col ${theme === 'dark' ? 'bg-gray-900 text-white' : 'bg-white text-gray-900'}`}
      style={{ 
        border: theme === 'dark' ? '1px solid #1e293b' : '1px solid #e2e8f0',
        borderRadius: '6px'
      }}
    >
      {/* Terminal Output */}
      <div 
        ref={outputRef}
        className="flex-1 p-4 overflow-y-auto font-mono text-sm"
        style={{ 
          backgroundColor: theme === 'dark' ? '#0f1419' : '#ffffff',
          color: theme === 'dark' ? '#e6e6e6' : '#1a202c'
        }}
      >
        {terminalOutput.map((line, index) => (
          <div 
            key={index} 
            className={`${getOutputClass(line.type)} ${line.text.trim() === '' ? 'h-4' : ''}`}
          >
            {line.text}
          </div>
        ))}
      </div>

      {/* Terminal Input */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-gray-600">
        <div className="flex items-center">
          <span className="text-green-400 font-bold mr-2">$</span>
          <input
            ref={inputRef}
            type="text"
            value={currentInput}
            onChange={(e) => setCurrentInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isProcessing}
            className={`flex-1 bg-transparent outline-none font-mono text-sm ${
              theme === 'dark' ? 'text-white' : 'text-gray-900'
            }`}
            placeholder={isProcessing ? 'Processing...' : 'Enter command...'}
            autoFocus
          />
        </div>
      </form>
    </div>
  )
}

export default Terminal 