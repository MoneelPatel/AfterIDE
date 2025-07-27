import React, { useState, useEffect, useRef, useCallback } from 'react'
import { useTheme } from '../contexts/ThemeContext'
import { useWebSocket } from '../contexts/WebSocketContext'
import FileTree from '../components/FileTree'
import MonacoEditor from '../components/MonacoEditor'
import FileTabs from '../components/FileTabs'
import EditorToolbar from '../components/EditorToolbar'
import EditorSettings from '../components/EditorSettings'
import Terminal from '../components/Terminal'

interface Session {
  id: string
  name: string
  description: string
  status: string
  expires_at: string
}

interface FileNode {
  id: string
  name: string
  type: 'file' | 'folder'
  path: string
  children?: FileNode[]
  content?: string
  language?: string
  isExpanded?: boolean
}

interface FileTab {
  id: string
  name: string
  path: string
  language: string
  isDirty: boolean
  isActive: boolean
}

interface EditorSettingsConfig {
  fontSize: number;
  fontFamily: string;
  tabSize: number;
  insertSpaces: boolean;
  wordWrap: 'on' | 'off' | 'wordWrapColumn' | 'bounded';
  minimap: boolean;
  lineNumbers: 'on' | 'off' | 'relative';
  renderWhitespace: 'none' | 'boundary' | 'selection' | 'trailing' | 'all';
  cursorBlinking: 'blink' | 'smooth' | 'phase' | 'expand' | 'solid';
  cursorSmoothCaretAnimation: 'on' | 'off';
  autoSave: boolean;
  autoSaveDelay: number;
  theme: 'light' | 'dark' | 'afteride-light' | 'afteride-dark';
}

const EditorPage: React.FC = () => {
  const [sessions, setSessions] = useState<Session[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [editorHeight, setEditorHeight] = useState(70)
  const [isDragging, setIsDragging] = useState(false)
  const [showSessions, setShowSessions] = useState(false)
  const [showFileTree, setShowFileTree] = useState(true)
  const [files, setFiles] = useState<FileNode[]>([])
  const [selectedFile, setSelectedFile] = useState<FileNode | null>(null)
  const [fileContent, setFileContent] = useState('')
  const [terminalOutput, setTerminalOutput] = useState('')
  const containerRef = useRef<HTMLDivElement>(null)
  const { theme } = useTheme()
  const { 
    connectTerminal, 
    connectFiles, 
    sendTerminalMessage, 
    sendFilesMessage, 
    onFilesMessage, 
    offFilesMessage, 
    terminalConnected,
    onTerminalMessage,
    offTerminalMessage
  } = useWebSocket()

  // File tabs state
  const [openTabs, setOpenTabs] = useState<FileTab[]>([])
  const [activeTabId, setActiveTabId] = useState<string>('')

  // Editor state
  const [isDirty, setIsDirty] = useState(false)
  const [showMinimap, setShowMinimap] = useState(true)
  const [wordWrap, setWordWrap] = useState(true)
  const [findQuery, setFindQuery] = useState('')
  const [replaceQuery, setReplaceQuery] = useState('')

  // Settings state
  const [showSettings, setShowSettings] = useState(false)
  const [editorSettings, setEditorSettings] = useState<EditorSettingsConfig>({
    fontSize: 14,
    fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
    tabSize: 4,
    insertSpaces: true,
    wordWrap: 'on',
    minimap: true,
    lineNumbers: 'on',
    renderWhitespace: 'selection',
    cursorBlinking: 'blink',
    cursorSmoothCaretAnimation: 'on',
    autoSave: true,
    autoSaveDelay: 2000,
    theme: 'afteride-dark'
  })

  // Initialize default files
  useEffect(() => {
    const defaultFiles: FileNode[] = [
      {
        id: '1',
        name: 'main.py',
        type: 'file',
        path: '/main.py',
        content: `# Welcome to AfterIDE!
# This is your main Python file.

def hello_world():
    print("Hello, AfterIDE!")
    print("You can run this code in the terminal below.")

if __name__ == "__main__":
    hello_world()
`,
        language: 'python'
      },
      {
        id: '2',
        name: 'requirements.txt',
        type: 'file',
        path: '/requirements.txt',
        content: `# Python dependencies
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
structlog==23.2.0
`,
        language: 'text'
      },
      {
        id: '3',
        name: 'README.md',
        type: 'file',
        path: '/README.md',
        content: `# AfterIDE Project

Welcome to your AfterIDE workspace!

## Getting Started

1. Open the terminal below
2. Run \`python main.py\` to execute your code
3. Use \`ls\` to list files
4. Use \`cat filename\` to view file contents

## Features

- Real-time terminal with command execution
- File system integration
- Python script execution
- WebSocket-based communication

Happy coding!
`,
        language: 'markdown'
      },
      {
        id: '4',
        name: 'src',
        type: 'folder',
        path: '/src',
        children: [],
        isExpanded: false
      }
    ]

    setFiles(defaultFiles)
    setSelectedFile(defaultFiles[0])
    setFileContent(defaultFiles[0].content || '')

    // Open first file in tabs
    setOpenTabs([{
      id: defaultFiles[0].id,
      name: defaultFiles[0].name,
      path: defaultFiles[0].path,
      language: defaultFiles[0].language || 'text',
      isDirty: false,
      isActive: true
    }])
    setActiveTabId(defaultFiles[0].id)

    setIsLoading(false)
  }, [])

  // Connect to WebSocket on component mount
  useEffect(() => {
    const connectWebSockets = async () => {
      try {
        await connectTerminal('default-session')
        await connectFiles('default-session')
      } catch (error) {
        console.error('Failed to connect to WebSocket:', error)
      }
    }

    connectWebSockets()
  }, [connectTerminal, connectFiles])

  // Handle file synchronization messages
  useEffect(() => {
    const handleFilesMessage = (message: any) => {
      if (message.type === 'file_updated') {
        // Update file content when it's modified by another client
        const updatedFile = files.find(f => f.name === message.filename)
        if (updatedFile) {
          setFiles(prevFiles => 
            prevFiles.map(f => 
              f.name === message.filename 
                ? { ...f, content: message.content }
                : f
            )
          )
          
          // Update current file content if it's the selected file
          if (selectedFile?.name === message.filename) {
            setFileContent(message.content)
            setIsDirty(false)
          }
        }
      }
    }

    onFilesMessage('file_updated', handleFilesMessage)

    return () => {
      offFilesMessage('file_updated', handleFilesMessage)
    }
  }, [files, selectedFile, onFilesMessage, offFilesMessage])

  // Handle terminal messages for file operations
  useEffect(() => {
    const handleTerminalMessage = (message: any) => {
      if (message.type === 'command_response') {
        // Handle file operations from terminal
        if (message.command.startsWith('cat ')) {
          // File content was displayed in terminal
          console.log('File content displayed in terminal:', message.stdout)
        } else if (message.command.startsWith('ls')) {
          // Directory listing was shown
          console.log('Directory listing shown in terminal')
        }
      }
    }

    onTerminalMessage('command_response', handleTerminalMessage)

    return () => {
      offTerminalMessage('command_response', handleTerminalMessage)
    }
  }, [onTerminalMessage, offTerminalMessage])

  // Handle resize functionality
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isDragging) {
        setIsDragging(false)
      }
    }

    const handleMouseMove = (e: MouseEvent) => {
      if (isDragging && containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect()
        const newHeight = ((e.clientY - rect.top) / rect.height) * 100
        setEditorHeight(Math.max(20, Math.min(80, newHeight)))
      }
    }

    const handleMouseUp = () => {
      setIsDragging(false)
    }

    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
      document.addEventListener('keydown', handleKeyDown)
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [isDragging])

  const fetchSessions = async () => {
    try {
      // TODO: Implement actual session fetching
      const mockSessions: Session[] = [
        {
          id: 'default-session',
          name: 'Default Session',
          description: 'Your default development session',
          status: 'active',
          expires_at: '2024-12-31T23:59:59Z'
        }
      ]
      setSessions(mockSessions)
    } catch (error) {
      console.error('Failed to fetch sessions:', error)
      setError('Failed to load sessions')
    }
  }

  const createSession = async () => {
    try {
      // TODO: Implement session creation
      console.log('Creating new session...')
    } catch (error) {
      console.error('Failed to create session:', error)
      setError('Failed to create session')
    }
  }

  const handleFileSelect = (file: FileNode) => {
    setSelectedFile(file)
    setFileContent(file.content || '')
    setIsDirty(false)

    // Add to tabs if not already open
    const existingTab = openTabs.find(tab => tab.id === file.id)
    if (!existingTab) {
      const newTab: FileTab = {
        id: file.id,
        name: file.name,
        path: file.path,
        language: file.language || 'text',
        isDirty: false,
        isActive: true
      }
      setOpenTabs(prev => [...prev, newTab])
    }

    // Set as active tab
    setActiveTabId(file.id)
    setOpenTabs(prev => prev.map(tab => ({
      ...tab,
      isActive: tab.id === file.id
    })))
  }

  const handleFileCreate = (type: 'file' | 'folder', parentPath?: string) => {
    const newId = Date.now().toString()
    const newName = type === 'file' ? 'new_file.txt' : 'new_folder'
    const newPath = parentPath ? `${parentPath}/${newName}` : `/${newName}`

    const updateFiles = (files: FileNode[]): FileNode[] => {
      return files.map(file => {
        if (file.path === parentPath || (!parentPath && file.path === '/')) {
          return {
            ...file,
            children: [...(file.children || []), {
              id: newId,
              name: newName,
              type,
              path: newPath,
              children: type === 'folder' ? [] : undefined,
              content: type === 'file' ? '' : undefined,
              language: type === 'file' ? 'text' : undefined
            }]
          }
        }
        return file
      })
    }

    setFiles(updateFiles)
  }

  const handleFileDelete = (fileId: string) => {
    const removeFile = (files: FileNode[]): FileNode[] => {
      return files.filter(file => {
        if (file.id === fileId) {
          return false
        }
        if (file.children) {
          file.children = removeFile(file.children)
        }
        return true
      })
    }

    setFiles(removeFile)

    // Close tab if file is deleted
    const deletedFile = files.find(f => f.id === fileId)
    if (deletedFile) {
      setOpenTabs(prev => prev.filter(tab => tab.id !== fileId))
      
      // Select another file if the deleted one was selected
      if (selectedFile?.id === fileId) {
        const remainingFiles = removeFile([...files])
        if (remainingFiles.length > 0) {
          handleFileSelect(remainingFiles[0])
        } else {
          setSelectedFile(null)
          setFileContent('')
        }
      }
    }
  }

  const handleFileRename = (fileId: string, newName: string) => {
    const renameFile = (files: FileNode[]): FileNode[] => {
      return files.map(file => {
        if (file.id === fileId) {
          return { ...file, name: newName }
        }
        if (file.children) {
          file.children = renameFile(file.children)
        }
        return file
      })
    }

    setFiles(renameFile)

    // Update tab name
    setOpenTabs(prev => prev.map(tab => 
      tab.id === fileId ? { ...tab, name: newName } : tab
    ))

    // Update selected file
    if (selectedFile?.id === fileId) {
      setSelectedFile(prev => prev ? { ...prev, name: newName } : null)
    }
  }

  const handleFileMove = (fileId: string, newParentPath: string) => {
    // TODO: Implement file move functionality
    console.log('Moving file', fileId, 'to', newParentPath)
  }

  const handleFileSave = () => {
    if (!selectedFile) return

    const updateFileContent = (files: FileNode[]): FileNode[] => {
      return files.map(file => {
        if (file.id === selectedFile.id) {
          return { ...file, content: fileContent }
        }
        if (file.children) {
          file.children = updateFileContent(file.children)
        }
        return file
      })
    }

    setFiles(updateFileContent)
    setSelectedFile(prev => prev ? { ...prev, content: fileContent } : null)
    setIsDirty(false)

    // Update tab dirty state
    setOpenTabs(prev => prev.map(tab => 
      tab.id === selectedFile.id ? { ...tab, isDirty: false } : tab
    ))

    // Send file update to backend
    if (selectedFile) {
      sendFilesMessage({
        type: 'file_update',
        filename: selectedFile.name,
        content: fileContent,
        language: selectedFile.language
      })
    }
  }

  const handleTabSelect = (tabId: string) => {
    const tab = openTabs.find(t => t.id === tabId)
    if (!tab) return

    const file = files.find(f => f.id === tabId)
    if (file) {
      setSelectedFile(file)
      setFileContent(file.content || '')
      setIsDirty(false)
    }

    setActiveTabId(tabId)
    setOpenTabs(prev => prev.map(t => ({
      ...t,
      isActive: t.id === tabId
    })))
  }

  const handleTabClose = (tabId: string) => {
    const tabIndex = openTabs.findIndex(tab => tab.id === tabId)
    if (tabIndex === -1) return

    setOpenTabs(prev => prev.filter(tab => tab.id !== tabId))

    // Select another tab if the closed one was active
    if (activeTabId === tabId) {
      const remainingTabs = openTabs.filter(tab => tab.id !== tabId)
      if (remainingTabs.length > 0) {
        const nextTab = remainingTabs[Math.min(tabIndex, remainingTabs.length - 1)]
        handleTabSelect(nextTab.id)
      } else {
        setSelectedFile(null)
        setFileContent('')
        setActiveTabId('')
      }
    }
  }

  const handleTabReorder = (fromIndex: number, toIndex: number) => {
    setOpenTabs(prev => {
      const newTabs = [...prev]
      const [movedTab] = newTabs.splice(fromIndex, 1)
      newTabs.splice(toIndex, 0, movedTab)
      return newTabs
    })
  }

  const handleEditorChange = (value: string) => {
    setFileContent(value)
    setIsDirty(true)

    // Update tab dirty state
    if (selectedFile) {
      setOpenTabs(prev => prev.map(tab => 
        tab.id === selectedFile.id ? { ...tab, isDirty: true } : tab
      ))
    }
  }

  const handleTerminalCommand = useCallback((command: string) => {
    // Send command to backend via WebSocket
    sendTerminalMessage({
      type: 'command',
      command: command
    })
  }, [sendTerminalMessage])

  const handleFind = (query: string) => {
    setFindQuery(query)
    // Monaco Editor will handle the find operation
  }

  const handleReplace = (query: string, replace: string) => {
    setFindQuery(query)
    setReplaceQuery(replace)
    // Monaco Editor will handle the replace operation
  }

  const handleToggleMinimap = () => {
    setShowMinimap(!showMinimap)
  }

  const handleToggleWordWrap = () => {
    setWordWrap(!wordWrap)
  }

  const handleRefresh = () => {
    if (selectedFile) {
      setFileContent(selectedFile.content || '')
      setIsDirty(false)
    }
  }

  const handleOpenSettings = () => {
    setShowSettings(true)
  }

  const handleSettingsChange = (newSettings: EditorSettingsConfig) => {
    setEditorSettings(newSettings)
    // Update local settings based on editor settings
    setShowMinimap(newSettings.minimap)
    setWordWrap(newSettings.wordWrap === 'on')
  }

  return (
    <div ref={containerRef} className="h-full flex flex-col">
      {/* File Tabs */}
      <FileTabs
        tabs={openTabs}
        activeTabId={activeTabId}
        onTabSelect={handleTabSelect}
        onTabClose={handleTabClose}
        onTabReorder={handleTabReorder}
      />

      {/* Editor Toolbar */}
      <EditorToolbar
        onSave={handleFileSave}
        onFind={handleFind}
        onReplace={handleReplace}
        onRefresh={handleRefresh}
        onToggleMinimap={handleToggleMinimap}
        onToggleWordWrap={handleToggleWordWrap}
        onOpenSettings={handleOpenSettings}
        isDirty={isDirty}
        showMinimap={showMinimap}
        wordWrap={wordWrap}
        findQuery={findQuery}
        replaceQuery={replaceQuery}
        onFindQueryChange={setFindQuery}
        onReplaceQueryChange={setReplaceQuery}
      />

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* File Tree */}
        {showFileTree && (
          <div className="w-64 bg-gray-50 dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700">
            <FileTree
              files={files}
              selectedFileId={selectedFile?.id}
              onFileSelect={handleFileSelect}
              onFileCreate={handleFileCreate}
              onFileDelete={handleFileDelete}
              onFileRename={handleFileRename}
              onFileMove={handleFileMove}
            />
          </div>
        )}

        {/* Editor and Terminal */}
        <div className="flex-1 flex flex-col min-h-0">
          {/* Editor */}
          <div style={{ height: `${editorHeight}%` }} className="relative flex-shrink-0">
            {selectedFile ? (
              <MonacoEditor
                value={fileContent}
                onChange={handleEditorChange}
                language={selectedFile.language || 'python'}
                filename={selectedFile.name}
                onSave={handleFileSave}
                autoSave={editorSettings.autoSave}
                autoSaveDelay={editorSettings.autoSaveDelay}
              />
            ) : (
              <div className="h-full flex items-center justify-center bg-gray-50 dark:bg-gray-900">
                <div className="text-center">
                  <div className="text-6xl mb-4">📝</div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                    Welcome to AfterIDE
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400">
                    Select a file from the explorer to start coding
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Resize Handle */}
          <div
            className="h-2 bg-gray-200 dark:bg-gray-700 cursor-ns-resize hover:bg-blue-500 hover:h-3 transition-all duration-200 flex items-center justify-center group"
            onMouseDown={() => setIsDragging(true)}
          >
            <div className="w-8 h-1 bg-gray-400 dark:bg-gray-500 group-hover:bg-blue-300 rounded-full transition-colors"></div>
          </div>

          {/* Terminal */}
          <div style={{ height: `${100 - editorHeight}%` }} className="flex-1 min-h-0 flex flex-col terminal-container">
            <Terminal 
              onCommand={handleTerminalCommand} 
              isConnected={terminalConnected} 
            />
          </div>
        </div>
      </div>

      {/* Editor Settings Modal */}
      <EditorSettings
        settings={editorSettings}
        onSettingsChange={handleSettingsChange}
        isOpen={showSettings}
        onClose={() => setShowSettings(false)}
      />
    </div>
  )
}

export default EditorPage 