import React, { useEffect, useRef, useState, useCallback } from 'react'
import { Terminal } from 'xterm'
import { FitAddon } from 'xterm-addon-fit'
import { WebLinksAddon } from 'xterm-addon-web-links'
import 'xterm/css/xterm.css'
import { useTheme } from '../contexts/ThemeContext'
import { useWebSocket } from '../contexts/WebSocketContext'

interface XTerminalProps {
  onCommand?: (command: string) => void
  isConnected?: boolean
}

const XTerminal: React.FC<XTerminalProps> = () => {
  const terminalRef = useRef<HTMLDivElement>(null)
  const xtermRef = useRef<Terminal | null>(null)
  const fitAddonRef = useRef<FitAddon | null>(null)
  
  // Use refs for frequently changing values to avoid re-renders
  const currentLineRef = useRef('')
  const commandHistoryRef = useRef<string[]>([])
  const historyIndexRef = useRef(-1)
  const isProcessingRef = useRef(false)
  const workingDirectoryRef = useRef('/')
  const terminalConnectedRef = useRef(false)
  const cursorPositionRef = useRef(0) // Track cursor position for tab completion
  const completionSuggestionsRef = useRef<string[]>([])
  const completionIndexRef = useRef(-1)
  const waitingForInputRef = useRef(false) // Track if we're waiting for user input
  const inputPromptRef = useRef('') // Store the input prompt
  
  const [isInitialized, setIsInitialized] = useState(false)
  const [fileSuggestions, setFileSuggestions] = useState<string[]>([])
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false)
  const { theme } = useTheme()
  const { 
    terminalConnected, 
    sendTerminalMessage, 
    onTerminalMessage, 
    offTerminalMessage 
  } = useWebSocket()

  // Tab completion functions
  const getFileSuggestions = useCallback(async (partial: string): Promise<string[]> => {
    if (!terminalConnectedRef.current) {
      // Fallback to common files if not connected
      const commonFiles = [
        'main.py', 'app.py', 'index.js', 'package.json', 'README.md', 'requirements.txt',
        'src/', 'dist/', 'node_modules/', 'public/', 'static/', 'templates/', 'views/',
        'models/', 'controllers/', 'utils/', 'config/', 'tests/', 'docs/',
        '.gitignore', '.env', 'Dockerfile', 'docker-compose.yml', 'Makefile'
      ]
      
      if (!partial) return commonFiles
      return commonFiles.filter(file => 
        file.toLowerCase().startsWith(partial.toLowerCase())
      )
    }

    // Use existing file suggestions from state if available
    if (fileSuggestions.length > 0) {
      if (!partial) return fileSuggestions
      return fileSuggestions.filter(file => 
        file.toLowerCase().startsWith(partial.toLowerCase())
      )
    }

    // Request file list from backend via WebSocket
    setIsLoadingSuggestions(true)
    
    return new Promise((resolve) => {
      const timeout = setTimeout(() => {
        setIsLoadingSuggestions(false)
        resolve([])
      }, 2000) // 2 second timeout

      // Send file list request via WebSocket
      sendTerminalMessage({
        type: 'file_list_request',
        directory: workingDirectoryRef.current
      })

      // Set up one-time handler for file list response
      const handleFileListResponse = (message: any) => {
        if (message.type === 'file_list_response') {
          clearTimeout(timeout)
          setIsLoadingSuggestions(false)
          
          const files = message.files || []
          const fileNames = files.map((file: { name?: string; path?: string; type?: string }) => {
            const name = file.name || file.path?.split('/').pop() || ''
            return file.type === 'directory' ? name + '/' : name
          })
          
          setFileSuggestions(fileNames)
          
          // Remove the handler
          offTerminalMessage('file_list_response', handleFileListResponse)
          
          // Return filtered results
          if (!partial) resolve(fileNames)
          else resolve(fileNames.filter((file: string) => 
            file.toLowerCase().startsWith(partial.toLowerCase())
          ))
        }
      }
      
      onTerminalMessage('file_list_response', handleFileListResponse)
    })
  }, [fileSuggestions, sendTerminalMessage, onTerminalMessage, offTerminalMessage])

  const handleTabCompletion = useCallback(async () => {
    const terminal = xtermRef.current
    if (!terminal) return
    
    const currentLine = currentLineRef.current
    const cursorPos = cursorPositionRef.current
    
    // Find the word at cursor position
    const beforeCursor = currentLine.slice(0, cursorPos)
    const words = beforeCursor.split(/\s+/)
    const currentWord = words[words.length - 1] || ''
    
    // Get suggestions for the current word
    const suggestions = await getFileSuggestions(currentWord)
    
    if (suggestions.length === 0) {
      // No suggestions - just beep
      terminal.write('\x07')
      return
    }
    
    if (suggestions.length === 1) {
      // Single suggestion - complete it
      const completion = suggestions[0]
      const completionSuffix = completion.slice(currentWord.length)
      
      // Update the line and cursor position
      const afterCursor = currentLine.slice(cursorPos)
      const newLine = beforeCursor + completionSuffix + afterCursor
      const newCursorPos = cursorPos + completionSuffix.length
      
      // Clear the current line and rewrite it
      terminal.write('\r$ ' + ' '.repeat(currentLine.length) + '\r$ ')
      terminal.write(newLine)
      
      // Update refs
      currentLineRef.current = newLine
      cursorPositionRef.current = newCursorPos
      
      // Position cursor correctly
      const remainingChars = newLine.length - newCursorPos
      if (remainingChars > 0) {
        terminal.write('\x1b[' + remainingChars + 'D')
      }
    } else {
      // Multiple suggestions - show them
      terminal.write('\r\n')
      suggestions.forEach((suggestion: string) => {
        terminal.write(suggestion + '  ')
      })
      terminal.write('\r\n$ ' + currentLine)
      
      // Reset completion state
      completionSuggestionsRef.current = suggestions
      completionIndexRef.current = 0
    }
  }, [getFileSuggestions])

  const cycleTabCompletion = useCallback(() => {
    const terminal = xtermRef.current
    if (!terminal || completionSuggestionsRef.current.length === 0) return
    
    const suggestions = completionSuggestionsRef.current
    const currentIndex = completionIndexRef.current
    
    // Cycle to next suggestion
    const nextIndex = (currentIndex + 1) % suggestions.length
    completionIndexRef.current = nextIndex
    
    const currentLine = currentLineRef.current
    const cursorPos = cursorPositionRef.current
    const beforeCursor = currentLine.slice(0, cursorPos)
    const words = beforeCursor.split(/\s+/)
    const currentWord = words[words.length - 1] || ''
    
    const suggestion = suggestions[nextIndex]
    const completionSuffix = suggestion.slice(currentWord.length)
    
    // Update the line and cursor position
    const afterCursor = currentLine.slice(cursorPos)
    const newLine = beforeCursor + completionSuffix + afterCursor
    const newCursorPos = cursorPos + completionSuffix.length
    
    // Clear the current line and rewrite it
    terminal.write('\r$ ' + ' '.repeat(currentLine.length) + '\r$ ')
    terminal.write(newLine)
    
    // Update refs
    currentLineRef.current = newLine
    cursorPositionRef.current = newCursorPos
    
    // Position cursor correctly
    const remainingChars = newLine.length - newCursorPos
    if (remainingChars > 0) {
      terminal.write('\x1b[' + remainingChars + 'D')
    }
  }, [])

  // Clear file suggestions when working directory changes
  useEffect(() => {
    setFileSuggestions([])
  }, [workingDirectoryRef.current])

  // Debug connection status changes and keep ref in sync
  useEffect(() => {
    console.log('XTerminal: Connection status changed:', terminalConnected)
    terminalConnectedRef.current = terminalConnected
  }, [terminalConnected])

  const prompt = useCallback(() => {
    if (xtermRef.current && !isProcessingRef.current) {
      xtermRef.current.write('\r\n$ ')
    }
  }, [])

  const writeOutput = useCallback((text: string, color?: 'red' | 'green' | 'yellow' | 'blue') => {
    if (!xtermRef.current) return
    
    let colorCode = ''
    let resetCode = '\x1b[0m'
    
    switch (color) {
      case 'red':
        colorCode = '\x1b[31m'
        break
      case 'green':
        colorCode = '\x1b[32m'
        break
      case 'yellow':
        colorCode = '\x1b[33m'
        break
      case 'blue':
        colorCode = '\x1b[34m'
        break
      default:
        colorCode = ''
        resetCode = ''
    }
    
    xtermRef.current.write(`${colorCode}${text}${resetCode}`)
  }, [])

  const executeCommand = useCallback((command: string) => {
    if (!command.trim()) {
      prompt()
      return
    }

    // Add to history
    const newHistory = [...commandHistoryRef.current, command.trim()]
    commandHistoryRef.current = newHistory.slice(-100)
    historyIndexRef.current = newHistory.length

    console.log('XTerminal: Executing command:', command.trim(), 'Connected:', terminalConnectedRef.current)

    // Send command to backend if connected
    if (terminalConnectedRef.current) {
      isProcessingRef.current = true
      console.log('XTerminal: Sending command to backend')
      sendTerminalMessage({
        type: 'command',
        command: command.trim(),
        working_directory: workingDirectoryRef.current
      })
    } else {
      console.log('XTerminal: Using local command handling - not connected')
      // Local command handling
      handleLocalCommand(command.trim())
    }
  }, [prompt, sendTerminalMessage])

  const handleLocalCommand = useCallback((command: string) => {
    const cmd = command.toLowerCase()
    
    if (cmd === 'help') {
      writeOutput('\r\nAvailable commands:')
      writeOutput('\r\n  help     - Show this help message')
      writeOutput('\r\n  ls       - List files')
      writeOutput('\r\n  clear    - Clear terminal')
      writeOutput('\r\n  pwd      - Show current directory')
      writeOutput('\r\n  python   - Run Python code')
      writeOutput('\r\n  cat      - Display file contents')
      writeOutput('\r\n  cd       - Change directory')
    } else if (cmd === 'clear') {
      xtermRef.current?.clear()
      writeOutput('Welcome to AfterIDE Terminal!', 'green')
      writeOutput('\r\nType "help" for available commands.')
    } else if (cmd === 'ls') {
      writeOutput('\r\n[LOCAL FALLBACK] Files in current directory:', 'yellow')
      writeOutput('\r\n  main.py')
      writeOutput('\r\n  requirements.txt')
      writeOutput('\r\n  README.md')
      writeOutput('\r\n  src/', 'blue')
      writeOutput('\r\n[Note: Backend not connected - showing fallback files]', 'yellow')
    } else if (cmd === 'pwd') {
      writeOutput(`\r\nCurrent directory: ${workingDirectoryRef.current}`, 'blue')
    } else {
      writeOutput(`\r\nCommand not found: ${command}`, 'red')
      writeOutput('\r\nType "help" for available commands.')
    }
    
    prompt()
  }, [writeOutput, prompt])

  // Handle command responses from backend
  useEffect(() => {
    const handleCommandResponse = (message: any) => {
      console.log('XTerminal: Received message:', message)
      
      if (message.type === 'command_response') {
        console.log('XTerminal: Processing command response:', message)
        isProcessingRef.current = false
        
        // Update working directory if provided (for cd commands)
        if (message.working_directory) {
          console.log('XTerminal: Updating working directory to:', message.working_directory)
          workingDirectoryRef.current = message.working_directory
        }
        
        // Display stdout
        if (message.stdout) {
          console.log('XTerminal: Displaying stdout:', message.stdout)
          
          // Check for special clear signal
          if (message.stdout === '__CLEAR_TERMINAL__') {
            console.log('XTerminal: Clearing terminal')
            xtermRef.current?.clear()
            writeOutput('Welcome to AfterIDE Terminal!', 'green')
            writeOutput('\r\nType "help" for available commands.')
            prompt()
            return // Don't continue with normal output handling
          } else {
            writeOutput('\r\n' + message.stdout)
          }
        }
        
        // Display stderr
        if (message.stderr) {
          console.log('XTerminal: Displaying stderr:', message.stderr)
          writeOutput('\r\n' + message.stderr, 'red')
        }
        
        // If no output, show a message
        if (!message.stdout && !message.stderr) {
          console.log('XTerminal: No output from command')
          writeOutput('\r\n[Command executed - no output]', 'blue')
        }
        
        prompt()
      } else if (message.type === 'input_request') {
        // Handle input request from backend (e.g., Python input() function)
        console.log('XTerminal: Input request received:', message.prompt)
        waitingForInputRef.current = true
        inputPromptRef.current = message.prompt || ''
        
        // Display the input prompt
        if (message.prompt) {
          writeOutput(message.prompt)
        }
        
        // Don't show the regular prompt - we're waiting for input
        isProcessingRef.current = true
      } else if (message.type === 'input_response') {
        // Handle input response confirmation
        console.log('XTerminal: Input response confirmed')
        waitingForInputRef.current = false
        inputPromptRef.current = ''
        isProcessingRef.current = false
        prompt()
      }
    }

    const handleError = (message: any) => {
      console.log('XTerminal: Received error:', message)
      if (message.type === 'error') {
        isProcessingRef.current = false
        writeOutput(`\r\nError: ${message.message}`, 'red')
        prompt()
      }
    }

    console.log('XTerminal: Setting up message handlers')
    onTerminalMessage('command_response', handleCommandResponse)
    onTerminalMessage('input_request', handleCommandResponse)
    onTerminalMessage('input_response', handleCommandResponse)
    onTerminalMessage('error', handleError)

    return () => {
      console.log('XTerminal: Cleaning up message handlers')
      offTerminalMessage('command_response', handleCommandResponse)
      offTerminalMessage('input_request', handleCommandResponse)
      offTerminalMessage('input_response', handleCommandResponse)
      offTerminalMessage('error', handleError)
    }
  }, [onTerminalMessage, offTerminalMessage, writeOutput, prompt])

  // Initialize terminal only once
  useEffect(() => {
    if (!terminalRef.current || isInitialized) return

    // Ensure the container has dimensions before initializing
    const container = terminalRef.current
    
    const checkDimensions = () => {
      const rect = container.getBoundingClientRect()
      return rect.width > 0 && rect.height > 0
    }
    
    if (!checkDimensions()) {
      // Use ResizeObserver to wait for proper dimensions
      const resizeObserver = new ResizeObserver((entries) => {
        for (const entry of entries) {
          if (entry.contentRect.width > 0 && entry.contentRect.height > 0) {
            resizeObserver.disconnect()
            setTimeout(initializeTerminal, 50) // Small delay to ensure DOM is settled
          }
        }
      })
      resizeObserver.observe(container)
      
      // Fallback timeout in case ResizeObserver doesn't work
      const timeoutId = setTimeout(() => {
        resizeObserver.disconnect()
        if (checkDimensions()) {
          initializeTerminal()
        }
      }, 200)
      
      return () => {
        resizeObserver.disconnect()
        clearTimeout(timeoutId)
      }
    }

    // If dimensions are already available, initialize immediately
    setTimeout(initializeTerminal, 10)

    function initializeTerminal() {
      if (!terminalRef.current || xtermRef.current) return
      
      // Double-check dimensions before proceeding
      const rect = terminalRef.current.getBoundingClientRect()
      if (rect.width === 0 || rect.height === 0) {
        console.warn('Terminal container still has no dimensions, skipping initialization')
        return
      }

      const terminal = new Terminal({
        theme: {
          background: theme === 'dark' ? '#0f1419' : '#ffffff',
          foreground: theme === 'dark' ? '#e6e6e6' : '#1a202c',
          cursor: theme === 'dark' ? '#ffffff' : '#000000',
          cursorAccent: theme === 'dark' ? '#000000' : '#ffffff',
          selectionBackground: theme === 'dark' ? '#264F78' : '#ADD6FF',
        },
        fontFamily: '"Fira Code", "JetBrains Mono", "Monaco", "Menlo", "Ubuntu Mono", monospace',
        fontSize: 14,
        lineHeight: 1.2,
        cursorBlink: true,
        cursorStyle: 'block',
        allowProposedApi: true,
        convertEol: true,
        disableStdin: false,
      })

      const fitAddon = new FitAddon()
      const webLinksAddon = new WebLinksAddon()
      
      try {
        terminal.loadAddon(fitAddon)
        terminal.loadAddon(webLinksAddon)

        // Open terminal in container
        terminal.open(terminalRef.current)
        
        // Store references before fitting
        xtermRef.current = terminal
        fitAddonRef.current = fitAddon
        
        // Wait for terminal to be properly mounted, then fit
        setTimeout(() => {
          try {
            if (xtermRef.current && fitAddonRef.current && terminalRef.current) {
              fitAddonRef.current.fit()
              setIsInitialized(true)
            }
          } catch (e) {
            console.warn('Error fitting terminal:', e)
            setIsInitialized(true) // Still mark as initialized to avoid retries
          }
        }, 100)

      } catch (error) {
        console.warn('Failed to initialize terminal:', error)
        return
      }

      // Welcome message
      setTimeout(() => {
        if (xtermRef.current) {
          writeOutput('Welcome to AfterIDE Terminal!', 'green')
          writeOutput('\r\nType "help" for available commands.')
          prompt()
        }
      }, 100)

      // Handle input
      terminal.onData((data) => {
        // Allow input if we're waiting for user input, even if processing
        if (isProcessingRef.current && !waitingForInputRef.current) return

        const code = data.charCodeAt(0)

        if (code === 13) { // Enter
          const command = currentLineRef.current
          currentLineRef.current = ''
          
          if (waitingForInputRef.current) {
            // We're waiting for input - send it to the backend
            console.log('XTerminal: Sending input to backend:', command)
            sendTerminalMessage({
              type: 'input_response',
              input: command
            })
            terminal.write('\r\n')
            return
          }
          
          // For clear command, clear the current line and don't echo the command back
          if (command.trim().toLowerCase() === 'clear') {
            // Clear the current line by writing backspaces
            terminal.write('\r$ ' + ' '.repeat(command.length) + '\r')
          } else {
            terminal.write('\r\n')
          }
          
          executeCommand(command)
        } else if (code === 127) { // Backspace
          if (currentLineRef.current.length > 0) {
            currentLineRef.current = currentLineRef.current.slice(0, -1)
            terminal.write('\b \b')
          }
        } else if (code === 9) { // Tab key
          // Handle tab completion
          handleTabCompletion()
        } else if (code === 27) { // Escape sequences (arrow keys)
          const seq = data.slice(1)
          if (seq === '[A') { // Arrow Up
            if (historyIndexRef.current > 0 || (historyIndexRef.current === -1 && commandHistoryRef.current.length > 0)) {
              const newIndex = historyIndexRef.current === -1 ? commandHistoryRef.current.length - 1 : historyIndexRef.current - 1
              historyIndexRef.current = newIndex
              const historyCommand = commandHistoryRef.current[newIndex] || ''
              
              // Clear current line
              terminal.write('\r$ ' + ' '.repeat(currentLineRef.current.length) + '\r$ ')
              terminal.write(historyCommand)
              currentLineRef.current = historyCommand
            }
          } else if (seq === '[B') { // Arrow Down
            if (historyIndexRef.current < commandHistoryRef.current.length - 1) {
              const newIndex = historyIndexRef.current + 1
              historyIndexRef.current = newIndex
              const historyCommand = commandHistoryRef.current[newIndex] || ''
              
              // Clear current line
              terminal.write('\r$ ' + ' '.repeat(currentLineRef.current.length) + '\r$ ')
              terminal.write(historyCommand)
              currentLineRef.current = historyCommand
            } else if (historyIndexRef.current === commandHistoryRef.current.length - 1) {
              historyIndexRef.current = commandHistoryRef.current.length
              
              // Clear current line
              terminal.write('\r$ ' + ' '.repeat(currentLineRef.current.length) + '\r$ ')
              currentLineRef.current = ''
            }
          } else {
            // Let xterm handle all other escape sequences (including left/right arrows) naturally
            terminal.write(data)
          }
        } else if (code >= 32) { // Printable characters
          currentLineRef.current = currentLineRef.current + data
          terminal.write(data)
        }
      })

      // Handle paste
      terminal.onSelectionChange(() => {
        const selection = terminal.getSelection()
        if (selection) {
          navigator.clipboard.writeText(selection).catch(() => {
            // Fallback for browsers that don't support clipboard API
          })
        }
      })
    }

    return () => {
      try {
        if (xtermRef.current) {
          xtermRef.current.dispose()
        }
      } catch (e) {
        console.warn('Error disposing terminal:', e)
      } finally {
        xtermRef.current = null
        fitAddonRef.current = null
        setIsInitialized(false)
      }
    }
  }, []) // Only depend on initial mount, not on changing values

  // Handle theme changes separately
  useEffect(() => {
    if (xtermRef.current && isInitialized) {
      xtermRef.current.options.theme = {
        background: theme === 'dark' ? '#0f1419' : '#ffffff',
        foreground: theme === 'dark' ? '#e6e6e6' : '#1a202c',
        cursor: theme === 'dark' ? '#ffffff' : '#000000',
        cursorAccent: theme === 'dark' ? '#000000' : '#ffffff',
        selectionBackground: theme === 'dark' ? '#264F78' : '#ADD6FF',
      }
    }
  }, [theme, isInitialized])

  // Handle resize
  useEffect(() => {
    const handleResize = () => {
      if (fitAddonRef.current && isInitialized) {
        setTimeout(() => {
          fitAddonRef.current?.fit()
        }, 100)
      }
    }

    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [isInitialized])

  return (
    <div 
      className="h-full w-full"
      style={{ 
        border: theme === 'dark' ? '1px solid #1e293b' : '1px solid #e2e8f0',
        borderRadius: '6px',
        overflow: 'hidden',
        minHeight: '200px',
        minWidth: '300px',
        position: 'relative'
      }}
    >
      <div 
        ref={terminalRef} 
        className="h-full w-full" 
        style={{
          minHeight: '200px',
          minWidth: '300px'
        }}
      />
    </div>
  )
}

export default XTerminal 