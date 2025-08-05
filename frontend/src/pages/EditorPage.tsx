import React, { useState, useEffect, useRef, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import CodeMirrorEditor from '../components/CodeMirrorEditor'
import { Play, Settings, Save, FileText, Folder, FolderOpen, Plus, Search, Terminal as TerminalIcon, X, Menu, Sun, Moon, Code, GitBranch } from 'lucide-react'
import toast from 'react-hot-toast'
import { useTheme } from '../contexts/ThemeContext'
import FileTree from '../components/FileTree'
import FileTabs from '../components/FileTabs'
import EditorToolbar from '../components/EditorToolbar'
import XTerminal from '../components/XTerminal'
import SubmissionForm from '../components/SubmissionForm'
import { useWebSocket } from '../contexts/WebSocketContext'
import { useAuthStore } from '../store/authStore'
import { useCurrentFile } from '../contexts/CurrentFileContext'
import { getUserSessionId, getUserSessionIdSync, getAuthToken } from '../services/websocket';

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
  const [loadedDirectories, setLoadedDirectories] = useState<Set<string>>(new Set(['/']))
  const containerRef = useRef<HTMLDivElement>(null)
  const { theme } = useTheme()
  const { isAuthenticated, user } = useAuthStore()
  const { setCurrentFile } = useCurrentFile()
  
  // Clear files when user changes (security fix)
  useEffect(() => {
    console.log('🔍 User changed, clearing files for security:', user?.username)
    setFiles([])
    setSelectedFile(null)
    setOpenTabs([])
    setActiveTabId('')
    setLoadedDirectories(new Set(['/']))
    setCurrentFile(null) // Clear current file when user changes
  }, [user?.id, setCurrentFile]) // Clear when user ID changes

  // Update current file in context when selectedFile changes
  useEffect(() => {
    if (selectedFile) {
      setCurrentFile({
        id: selectedFile.id,
        name: selectedFile.name || '',
        path: selectedFile.path
      })
    } else {
      setCurrentFile(null)
    }
  }, [selectedFile, setCurrentFile])
  const { 
    connectTerminal, 
    connectFiles, 
    sendTerminalMessage, 
    sendFilesMessage, 
    onFilesMessage, 
    offFilesMessage, 
    terminalConnected,
    onTerminalMessage,
    offTerminalMessage,
    filesConnected
  } = useWebSocket()

  // File tabs state
  const [openTabs, setOpenTabs] = useState<FileTab[]>([])
  const [activeTabId, setActiveTabId] = useState<string>('')

  // Editor state
  const [isDirty, setIsDirty] = useState(false)
  const [originalFileContent, setOriginalFileContent] = useState('')
  const [isLoadingFileContent, setIsLoadingFileContent] = useState(false)
  const [allowDirtyStateChanges, setAllowDirtyStateChanges] = useState(true)
  const [isInitialLoad, setIsInitialLoad] = useState(false)

  // Use refs to track loading state more reliably
  const isLoadingRef = useRef(false)
  const isInitialLoadRef = useRef(false)
  const allowDirtyChangesRef = useRef(true)
  const originalFileContentRef = useRef('')


  // Submission state
  const [showSubmissionForm, setShowSubmissionForm] = useState(false)

  // Initialize default files
  useEffect(() => {
    // Load files from backend when files WebSocket connects
    if (filesConnected) {
      sendFilesMessage({
        type: 'file_list',
        directory: '/'
      })
    }
  }, [filesConnected, sendFilesMessage])

  // Flatten hierarchical file tree to flat list
  const flattenFileTree = (files: FileNode[]): FileNode[] => {
    const flattened: FileNode[] = []
    
    const flatten = (nodes: FileNode[]) => {
      nodes.forEach(node => {
        // Add the node itself (without children to avoid circular references)
        flattened.push({
          ...node,
          children: undefined
        })
        
        // Recursively flatten children
        if (node.children && node.children.length > 0) {
          flatten(node.children)
        }
      })
    }
    
    flatten(files)
    return flattened
  }

  // Build hierarchical tree structure from flat file list
  const buildHierarchicalTree = (flatFiles: FileNode[]): FileNode[] => {
    const fileMap = new Map<string, FileNode>()
    const rootFiles: FileNode[] = []
    
    // First pass: create all nodes and put them in the map
    flatFiles.forEach(file => {
      const nodeWithChildren = {
        ...file,
        children: file.type === 'folder' ? [] : undefined
      }
      fileMap.set(file.path, nodeWithChildren)
    })
    
    // Second pass: build parent-child relationships
    flatFiles.forEach(file => {
      const pathParts = file.path.split('/').filter(part => part !== '')
      
      if (pathParts.length === 1) {
        // Root level file/folder
        const node = fileMap.get(file.path)
        if (node) {
          rootFiles.push(node)
        }
      } else {
        // Nested file/folder - find parent and add to its children
        const parentPath = '/' + pathParts.slice(0, -1).join('/')
        const parentNode = fileMap.get(parentPath)
        const currentNode = fileMap.get(file.path)
        
        if (parentNode && currentNode && parentNode.children) {
          parentNode.children.push(currentNode)
        }
      }
    })
    
    // Sort each level: folders first, then files, alphabetically
    const sortNodes = (nodes: FileNode[]): FileNode[] => {
      nodes.sort((a, b) => {
        if (a.type !== b.type) {
          return a.type === 'folder' ? -1 : 1
        }
        return a.name.localeCompare(b.name)
      })
      
      // Recursively sort children
      nodes.forEach(node => {
        if (node.children) {
          node.children = sortNodes(node.children)
        }
      })
      
      return nodes
    }
    
    return sortNodes(rootFiles)
  }

  // Handle folder expansion - load files from subdirectory if not already loaded
  const handleFolderExpansion = (folderPath: string) => {
    if (!loadedDirectories.has(folderPath)) {
      sendFilesMessage({
        type: 'file_list',
        directory: folderPath
      })
      setLoadedDirectories(prev => new Set([...prev, folderPath]))
    }
  }

  // Initialize WebSocket connections
  useEffect(() => {
    const connectWebSockets = async () => {
      try {
        // Get the current session ID and token from the WebSocket service
        const sessionId = await getUserSessionId();
        const token = getAuthToken();
        
        console.log('EditorPage: Connecting WebSockets with session:', sessionId, 'authenticated:', isAuthenticated);
        
        // Only connect if we have a valid token
        if (!token) {
          console.log('EditorPage: Not connecting WebSockets - no token');
          return;
        }
        
        // If we got the default session ID but have a token, use the fallback session ID
        let finalSessionId = sessionId;
        if (sessionId === 'default-session' && token) {
          console.log('EditorPage: Backend not available, using fallback session ID');
          finalSessionId = getUserSessionIdSync();
        }
        
        // Only connect if not already connected
        if (!terminalConnected) {
          await connectTerminal(finalSessionId, token);
        }
        if (!filesConnected) {
          await connectFiles(finalSessionId, token);
        }
      } catch (error) {
        console.error('Failed to connect to WebSocket:', error)
      }
    }

    // Only connect if user is authenticated and not already connected
    if (isAuthenticated && (!terminalConnected || !filesConnected)) {
      connectWebSockets()
    }
  }, [connectTerminal, connectFiles, isAuthenticated, terminalConnected, filesConnected])

  // Handle file synchronization messages
  useEffect(() => {
    const handleFilesMessage = (message: any) => {
      if (message.type === 'file_list_response') {
        console.log('🔍 File list response received:', message)
        
        // Convert backend file format to frontend FileNode format
        const backendFiles = message.files || []
        const convertedFiles: FileNode[] = backendFiles.map((file: any, index: number) => ({
          id: `file_${file.path}`,
          name: file.name,
          type: file.type === 'directory' ? 'folder' : 'file',
          path: file.path,
          content: '',
          language: file.language || (file.name.endsWith('.py') ? 'python' : file.name.endsWith('.md') ? 'markdown' : 'text'),
          size: file.size,
          modified: file.modified,
          children: file.type === 'directory' ? [] : undefined
        }))
        
        console.log('🔍 Converted files:', convertedFiles)
        
        // SECURITY FIX: Replace files instead of merging to prevent cross-user file leakage
        // Only merge files if we're loading a subdirectory, not the root
        const requestedDirectory = message.directory || '/'
        
        if (requestedDirectory === '/') {
          // Root directory request - replace all files
          console.log('🔍 Replacing all files (root directory)')
          setFiles(buildHierarchicalTree(convertedFiles))
        } else {
          // Subdirectory request - merge carefully 
          setFiles(prevFiles => {
            const fileMap = new Map<string, FileNode>()
            
            // Flatten existing hierarchical structure to get all files at all levels
            const existingFlatFiles = flattenFileTree(prevFiles)
            
            // Only keep existing files that are NOT direct children of the directory being updated
            // but keep the directory itself and files in other directories
            existingFlatFiles.forEach(file => {
              const normalizedRequestedDir = requestedDirectory.endsWith('/') ? requestedDirectory : requestedDirectory + '/'
              const normalizedFilePath = file.path.endsWith('/') ? file.path : file.path + '/'
              
              // Keep the file if:
              // 1. It's not in the requested directory at all, OR
              // 2. It's the requested directory itself, OR  
              // 3. It's in a subdirectory of the requested directory (deeper nesting)
              const isInRequestedDir = file.path.startsWith(normalizedRequestedDir) && file.path !== requestedDirectory
              const isDirectChild = isInRequestedDir && !file.path.substring(normalizedRequestedDir.length).includes('/')
              
              if (!isDirectChild || file.path === requestedDirectory) {
                fileMap.set(file.path, file)
              }
            })
            
            // Add new files from the requested directory
            convertedFiles.forEach(file => fileMap.set(file.path, file))
            
            const allFlatFiles = Array.from(fileMap.values())
            console.log('🔍 Final merged files:', allFlatFiles)
            
            // Build hierarchical tree structure
            return buildHierarchicalTree(allFlatFiles)
          })
        }
        
        setIsLoading(false)
        
        // If no file is selected but we have files, select the first file (not folder)
        if (!selectedFile) {
          const firstFile = convertedFiles.find(file => file.type === 'file')
          if (firstFile) {
            handleFileSelect(firstFile)
          }
        }
      } else if (message.type === 'file_content') {
        // Set states directly without setTimeout for better timing
        const content = message.content || '';
        console.log('🔧 File content received:', { 
          filename: message.filename, 
          contentLength: content.length,
          wasLoading: isLoadingFileContent,
          selectedFile: selectedFile?.path,
          isInitialLoad: isInitialLoad
        });
        
        // Set states directly without setTimeout for better timing
        setFileContent(content)
        setOriginalFileContent(content) // Set original content - THIS IS THE IMPORTANT BASELINE
        setIsLoadingFileContent(false) // Content loading complete
        setAllowDirtyStateChanges(true) // Re-enable dirty state changes now that content is loaded
        setIsInitialLoad(false) // Clear initial load flag now that content is loaded
        
        // Update refs for immediate access
        isLoadingRef.current = false
        isInitialLoadRef.current = false
        allowDirtyChangesRef.current = true
        originalFileContentRef.current = content // Set ref for immediate access
        
        console.log('🔧 BASELINE SET - originalFileContent now:', content.length, 'chars for:', message.filename);
        console.log('🔧 State flags cleared - isLoadingFileContent: false, allowDirtyStateChanges: true, isInitialLoad: false');
        console.log('🔧 Refs updated - isLoadingRef: false, isInitialLoadRef: false, allowDirtyChangesRef: true, originalFileContentRef:', content.length);
        
        // Add a small delay to ensure state updates are processed
        setTimeout(() => {
          console.log('🔧 State update delay completed - flags should now be properly set');
        }, 10);
      } else if (message.type === 'file_updated') {
        console.log('🔧 File update message received:', message.filename, message.language, 'content length:', message.content?.length)
        
        // Update file content when it's modified by another client
        const updatedFile = files.find(f => f.path === message.filename)
        if (updatedFile) {
          // File exists - update its content
          setFiles(prevFiles => 
            prevFiles.map(f => 
              f.path === message.filename 
                ? { ...f, content: message.content }
                : f
            )
          )
          
          // Update current file content if it's the selected file
          if (selectedFile?.path === message.filename) {
            setFileContent(message.content)
            setOriginalFileContent(message.content) // Set original content
            setIsDirty(false)
            setIsLoadingFileContent(false) // Content loading complete
            
            // Update tab dirty state
            setOpenTabs(prev => prev.map(tab => 
              tab.path === message.filename 
                ? { ...tab, isDirty: false }
                : tab
            ))
          }
        } else {
          // File doesn't exist - this is a new file, add it to the file tree
          const fileName = message.filename.split('/').pop() || 'unknown'
          const newFile: FileNode = {
            id: `file_${message.filename}`,
            name: fileName,
            type: 'file',
            path: message.filename,
            content: message.content,
            language: message.language || 'text'
          }
          
          // Add the new file to the file tree
          setFiles(prevFiles => {
            const fileMap = new Map<string, FileNode>()
            
            // Flatten existing hierarchical structure to get all files at all levels
            const existingFlatFiles = flattenFileTree(prevFiles)
            
            // Add existing files to map
            existingFlatFiles.forEach(file => fileMap.set(file.path, file))
            
            // Add the new file
            fileMap.set(newFile.path, newFile)
            
            const allFlatFiles = Array.from(fileMap.values())
            
            // Build hierarchical tree structure
            return buildHierarchicalTree(allFlatFiles)
          })
          
          console.log('🔧 Added new file to file tree:', newFile.name, newFile.path)
        }
      } else if (message.type === 'file_deleted') {
        // Handle file deletion broadcast
        const deletedFilePath = message.filename
        
        setFiles(prevFiles => {
          // Flatten existing tree to get all files
          const flatFiles = flattenFileTree(prevFiles)
          
          // Remove the deleted file
          const remainingFiles = flatFiles.filter(file => file.path !== deletedFilePath)
          
          // Rebuild hierarchical tree
          return buildHierarchicalTree(remainingFiles)
        })
        
        // Close tab and clear selection if deleted file was selected
        if (selectedFile?.path === deletedFilePath) {
          setSelectedFile(null)
          setFileContent('')
          setActiveTabId('')
        }
        
        // Remove tab if file was open
        setOpenTabs(prev => prev.filter(tab => tab.path !== deletedFilePath))
      } else if (message.type === 'folder_created') {
        // Handle folder creation broadcast - refresh file list
        sendFilesMessage({
          type: 'file_list',
          directory: '/'
        })
      } else if (message.type === 'file_renamed') {
        // Handle file rename/move broadcast
        const oldPath = message.old_filename
        const newPath = message.new_filename
        
        setFiles(prevFiles => {
          // Flatten existing tree to get all files
          const flatFiles = flattenFileTree(prevFiles)
          
          // Update the renamed/moved file's path
          const updatedFiles = flatFiles.map(file => 
            file.path === oldPath 
              ? { ...file, path: newPath, name: newPath.split('/').pop() || file.name }
              : file
          )
          
          // Rebuild hierarchical tree
          return buildHierarchicalTree(updatedFiles)
        })
        
        // Update selected file if it was the renamed/moved file
        if (selectedFile?.path === oldPath) {
          setSelectedFile(prev => prev ? {
            ...prev,
            path: newPath,
            name: newPath.split('/').pop() || prev.name
          } : null)
        }
        
        // Update open tabs
        setOpenTabs(prev => prev.map(tab => 
          tab.path === oldPath 
            ? { ...tab, path: newPath, name: newPath.split('/').pop() || tab.name }
            : tab
        ))
      }
    }

    onFilesMessage('file_list_response', handleFilesMessage)
    onFilesMessage('file_updated', handleFilesMessage)
    onFilesMessage('file_content', handleFilesMessage) // Added this line
    onFilesMessage('file_deleted', handleFilesMessage) // Added this line
    onFilesMessage('folder_created', handleFilesMessage) // Added this line
    onFilesMessage('file_renamed', handleFilesMessage) // Added this line

    return () => {
      offFilesMessage('file_list_response', handleFilesMessage)
      offFilesMessage('file_updated', handleFilesMessage)
      offFilesMessage('file_content', handleFilesMessage) // Added this line
      offFilesMessage('file_deleted', handleFilesMessage) // Added this line
      offFilesMessage('folder_created', handleFilesMessage) // Added this line
      offFilesMessage('file_renamed', handleFilesMessage) // Added this line
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
        } else if (message.command.startsWith('cd ') && message.working_directory) {
          // Directory changed - update file tree to show new directory contents
          console.log('Directory changed via cd command, updating file tree for:', message.working_directory)
          sendFilesMessage({
            type: 'file_list',
            directory: message.working_directory
          })
        }
      }
    }

    onTerminalMessage('command_response', handleTerminalMessage)

    return () => {
      offTerminalMessage('command_response', handleTerminalMessage)
    }
  }, [onTerminalMessage, offTerminalMessage, sendFilesMessage])

  // Handle resize functionality
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isDragging) {
        setIsDragging(false)
      }
      
      // Prevent default browser Cmd+S and handle file saving
      if ((e.metaKey || e.ctrlKey) && e.key === 's') {
        e.preventDefault()
        // The save will be handled by Monaco Editor's keyboard shortcut
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

    document.addEventListener('keydown', handleKeyDown)
    
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
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
    console.log('🔍 handleFileSelect called with:', file.path, file.name)
    setSelectedFile(file)
    setIsDirty(false)
    // DON'T set originalFileContent here - wait for backend response
    setOriginalFileContent('') // Clear it so dirty state doesn't trigger until we have real content
    setIsLoadingFileContent(true) // Start loading content
    setAllowDirtyStateChanges(false) // Temporarily disable dirty state changes
    setIsInitialLoad(true) // Mark as initial load to prevent first change event from setting dirty state
    
    // Update refs for immediate access
    isLoadingRef.current = true
    isInitialLoadRef.current = true
    allowDirtyChangesRef.current = false
    originalFileContentRef.current = '' // Clear original content ref
    
    console.log('🔧 Set isLoadingFileContent to true for:', file.path);

    // Load file content from backend if it's a file
    if (file.type === 'file') {
      sendFilesMessage({
        type: 'file_request',
        filename: file.path
      })
      
      // Re-enable dirty state changes after a longer delay as fallback
      setTimeout(() => {
        setAllowDirtyStateChanges(true)
        setIsLoadingFileContent(false)
        setIsInitialLoad(false) // Clear initial load flag
        allowDirtyChangesRef.current = true
        isLoadingRef.current = false
        isInitialLoadRef.current = false
        console.log('🔧 Re-enabled dirty state changes after timeout (fallback)')
      }, 2000) // Increased timeout to give more time for content to load
    } else {
      setFileContent('')
      setIsLoadingFileContent(false) // Not loading for folders
      setAllowDirtyStateChanges(true) // Re-enable for folders immediately
      setIsInitialLoad(false) // Clear initial load flag for folders
      allowDirtyChangesRef.current = true
      isLoadingRef.current = false
      isInitialLoadRef.current = false
      console.log('🔧 Set isLoadingFileContent to false for folder:', file.path);
    }

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

  const handleFileCreate = (type: 'file' | 'folder', parentPath?: string, name?: string) => {
    if (!name) {
      console.error('File/folder name is required');
      return;
    }
    
    const basePath = parentPath || '/'
    const newPath = basePath === '/' ? `/${name}` : `${basePath}/${name}`
    
    if (type === 'file') {
      // Get file extension for language detection
      const extension = name.split('.').pop() || 'txt'
      const languageMap: { [key: string]: string } = {
        py: 'python',
        js: 'javascript', 
        ts: 'typescript',
        jsx: 'javascript',
        tsx: 'typescript',
        html: 'html',
        css: 'css',
        json: 'json',
        md: 'markdown',
        txt: 'text',
        sql: 'sql',
        csv: 'csv',
        yaml: 'yaml',
        yml: 'yaml'
      }
      const language = languageMap[extension] || 'text'
      
      // Send file creation message via WebSocket
      sendFilesMessage({
        type: 'file_update',
        filename: newPath,
        content: '',
        language: language
      })
      
      // Refresh file list to show the new file
      sendFilesMessage({
        type: 'file_list',
        directory: '/'
      })
    } else {
      // Handle folder creation
      sendFilesMessage({
        type: 'folder_create',
        foldername: name,
        parent_path: basePath
      })
      
      // Refresh file list to show the new folder
      sendFilesMessage({
        type: 'file_list',
        directory: '/'
      })
    }
  }

  const handleFileDelete = (fileId: string) => {
    // Find the file to get its path
    const findFileById = (files: FileNode[], id: string): FileNode | null => {
      for (const file of files) {
        if (file.id === id) return file
        if (file.children) {
          const found = findFileById(file.children, id)
          if (found) return found
        }
      }
      return null
    }

    const fileToDelete = findFileById(files, fileId)
    if (fileToDelete) {
      // Send delete request to backend
      sendFilesMessage({
        type: 'file_delete',
        filename: fileToDelete.path
      })
      
      // Note: UI updates (tab closure, selection clearing, file tree updates) 
      // are now handled by the file_deleted broadcast message
    }
  }

  const handleFileRename = (fileId: string, newName: string) => {
    // Find the file to get its current path
    const findFileById = (files: FileNode[], id: string): FileNode | null => {
      for (const file of files) {
        if (file.id === id) return file
        if (file.children) {
          const found = findFileById(file.children, id)
          if (found) return found
        }
      }
      return null
    }

    const fileToRename = findFileById(files, fileId)
    if (fileToRename) {
      // Create new path with the new name
      const pathParts = fileToRename.path.split('/')
      pathParts[pathParts.length - 1] = newName
      const newPath = pathParts.join('/')

      // Send rename request to backend
      sendFilesMessage({
        type: 'file_rename',
        old_filename: fileToRename.path,
        new_filename: newPath
      })
      
      // Refresh file list to show updated state
      sendFilesMessage({
        type: 'file_list',
        directory: '/'
      })

      // Update tab name
      setOpenTabs(prev => prev.map(tab => 
        tab.id === fileId ? { ...tab, name: newName } : tab
      ))

      // Update selected file
      if (selectedFile?.id === fileId) {
        setSelectedFile(prev => prev ? { ...prev, name: newName } : null)
      }
    }
  }

  const handleFileMove = (fileId: string, newParentPath: string) => {
    // Find the source file to get its current path and name
    const findFileById = (files: FileNode[], id: string): FileNode | null => {
      for (const file of files) {
        if (file.id === id) return file
        if (file.children) {
          const found = findFileById(file.children, id)
          if (found) return found
        }
      }
      return null
    }

    const sourceFile = findFileById(files, fileId)
    if (!sourceFile) {
      console.error('Source file not found for move operation')
      return
    }

    // Don't allow moving a folder into itself
    if (sourceFile.type === 'folder' && newParentPath.startsWith(sourceFile.path)) {
      console.error('Cannot move a folder into itself or its subdirectory')
      return
    }

    // Create the new file path
    const fileName = sourceFile.name
    const newFilePath = newParentPath === '/' ? `/${fileName}` : `${newParentPath}/${fileName}`
    
    // Don't move if it's already in the same location
    if (sourceFile.path === newFilePath) {
      return
    }

    console.log(`Moving file from ${sourceFile.path} to ${newFilePath}`)

    // Send rename request to backend (rename can be used for moving)
    sendFilesMessage({
      type: 'file_rename',
      old_filename: sourceFile.path,
      new_filename: newFilePath
    })
  }

  const handleFileSave = (editorContent?: string) => {
    console.log('🔧 handleFileSave called with editorContent:', editorContent);
    console.log('🔧 Current isDirty state:', isDirty);
    
    if (!selectedFile) return

    // Handle case where editorContent might be an event object (from button click)
    let contentToSave: string;
    if (typeof editorContent === 'string') {
      contentToSave = editorContent;
    } else {
      // If editorContent is not a string (e.g., event object), use current fileContent
      contentToSave = fileContent;
      console.log('🔧 Using current fileContent instead of editorContent parameter');
    }

    const updateFileContent = (files: FileNode[]): FileNode[] => {
      return files.map(file => {
        if (file.id === selectedFile.id) {
          return { ...file, content: contentToSave }
        }
        if (file.children) {
          file.children = updateFileContent(file.children)
        }
        return file
      })
    }

    setFiles(updateFileContent)
    setSelectedFile(prev => prev ? { ...prev, content: contentToSave } : null)
    setIsDirty(false)

    // Update the fileContent state to match what was saved
    if (typeof editorContent === 'string') {
      setFileContent(editorContent);
    }
    
    // Update original content to the saved content
    setOriginalFileContent(contentToSave);
    originalFileContentRef.current = contentToSave; // Update ref as well

    // Update tab dirty state
    setOpenTabs(prev => prev.map(tab => 
      tab.id === selectedFile.id ? { ...tab, isDirty: false } : tab
    ))

    // Send file update to backend via WebSocket
    if (filesConnected && selectedFile.path) {
      const message = {
        type: 'file_update',
        filename: selectedFile.path,
        content: contentToSave,
        language: getLanguageFromFileName(selectedFile.name || '')
      };
      console.log('🔧 Sending file update message:', message);
      sendFilesMessage(message);
    } else {
      console.error('🔧 Files WebSocket not connected or no file path!');
    }
  }

  const handleTabSelect = (tabId: string) => {
    const tab = openTabs.find(t => t.id === tabId)
    if (!tab) return

    const file = files.find(f => f.id === tabId)
    if (file) {
      setSelectedFile(file)
      setIsDirty(false)
      // DON'T set originalFileContent here - wait for backend response
      setOriginalFileContent('') // Clear it so dirty state doesn't trigger until we have real content
      setIsLoadingFileContent(true) // Start loading content
      setAllowDirtyStateChanges(false) // Temporarily disable dirty state changes
      setIsInitialLoad(true) // Mark as initial load to prevent first change event from setting dirty state
      
      // Update refs for immediate access
      isLoadingRef.current = true
      isInitialLoadRef.current = true
      allowDirtyChangesRef.current = false
      originalFileContentRef.current = '' // Clear original content ref
      
      // Always request fresh content from backend instead of using cached content
      if (file.type === 'file') {
        sendFilesMessage({
          type: 'file_request',
          filename: file.path
        })
        
        // Re-enable dirty state changes after a longer delay as fallback
        setTimeout(() => {
          setAllowDirtyStateChanges(true)
          setIsLoadingFileContent(false)
          setIsInitialLoad(false) // Clear initial load flag
          allowDirtyChangesRef.current = true
          isLoadingRef.current = false
          isInitialLoadRef.current = false
          console.log('🔧 Re-enabled dirty state changes after timeout (tab select fallback)')
        }, 2000) // Increased timeout to match handleFileSelect
      } else {
        setFileContent('')
        setIsLoadingFileContent(false) // Not loading for folders
        setAllowDirtyStateChanges(true) // Re-enable for folders immediately
        setIsInitialLoad(false) // Clear initial load flag for folders
        allowDirtyChangesRef.current = true
        isLoadingRef.current = false
        isInitialLoadRef.current = false
      }
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

  const handleEditorChange = (value: string | undefined) => {
    if (value === undefined) return; // Handle case where value is undefined (e.g., initial load)
    
    console.log('🔧 handleEditorChange v4 SIMPLE:', { 
      originalFileContent: originalFileContent.length, 
      originalFileContentRef: originalFileContentRef.current.length,
      newValue: value.length,
      selectedFile: selectedFile?.path,
      areEqual: value === originalFileContent,
      areEqualRef: value === originalFileContentRef.current,
      allowDirtyStateChanges,
      isLoadingFileContent,
      isInitialLoad,
      // Add ref values for debugging
      isLoadingRef: isLoadingRef.current,
      isInitialLoadRef: isInitialLoadRef.current,
      allowDirtyChangesRef: allowDirtyChangesRef.current
    });
    
    setFileContent(value)
    
    // Use refs for more reliable state checking
    if (isInitialLoadRef.current || !allowDirtyChangesRef.current || isLoadingRef.current) {
      console.log('🔧 Skipping dirty state change - using refs for reliable state checking');
      console.log('🔧 Debug refs:', { 
        isInitialLoadRef: isInitialLoadRef.current, 
        allowDirtyChangesRef: allowDirtyChangesRef.current, 
        isLoadingRef: isLoadingRef.current 
      });
      return;
    }
    
    // Use ref for original content to avoid async state issues
    const originalContent = originalFileContentRef.current;
    
    // Simple approach: only set dirty if content differs AND original content exists
    if (originalContent && value !== originalContent) {
      console.log('🔧 Setting dirty state TRUE - content differs (using ref)');
      console.log('🔧 Original content length (ref):', originalContent.length, 'New content length:', value.length);
      setIsDirty(true)
      
      // Update tab dirty state
      if (selectedFile) {
        setOpenTabs(prev => prev.map(tab => 
          tab.id === selectedFile.id ? { ...tab, isDirty: true } : tab
        ))
      }
    } else if (originalContent && value === originalContent) {
      console.log('🔧 Setting dirty state FALSE - content matches original (using ref)');
      setIsDirty(false)
      
      // Update tab dirty state
      if (selectedFile) {
        setOpenTabs(prev => prev.map(tab => 
          tab.id === selectedFile.id ? { ...tab, isDirty: false } : tab
        ))
      }
    } else {
      console.log('🔧 No dirty state change - no original content yet (using ref)');
      console.log('🔧 Original content exists (ref):', !!originalContent, 'Length (ref):', originalContent.length);
    }
  }

  const handleTerminalCommand = useCallback((command: string) => {
    // Send command to backend via WebSocket
    sendTerminalMessage({
      type: 'command',
      command: command
    })
  }, [sendTerminalMessage])

  // Submission handlers
  const handleSubmitForReview = () => {
    if (selectedFile) {
      setShowSubmissionForm(true)
    } else {
      toast.error('Please select a file to submit for review')
    }
  }

  const handleSubmissionSuccess = () => {
    setShowSubmissionForm(false)
    toast.success('Code submitted for review successfully!')
  }

  const handleSubmissionCancel = () => {
    setShowSubmissionForm(false)
  }

  const getLanguageFromFileName = (fileName: string) => {
    const extension = fileName.split('.').pop() || 'txt'
    const languageMap: { [key: string]: string } = {
      py: 'python',
      js: 'javascript', 
      ts: 'typescript',
      jsx: 'javascript',
      tsx: 'typescript',
      html: 'html',
      css: 'css',
      json: 'json',
      md: 'markdown',
      txt: 'text',
      sql: 'sql',
      csv: 'csv',
      yaml: 'yaml',
      yml: 'yaml'
    }
    return languageMap[extension] || 'text'
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
        onSubmitForReview={handleSubmitForReview}
        isDirty={isDirty}
        canSubmit={!!selectedFile}
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
              onFolderExpansion={handleFolderExpansion}
            />
          </div>
        )}

        {/* Editor and Terminal */}
        <div className="flex-1 flex flex-col min-h-0">
          {/* Editor */}
          <div style={{ height: `${editorHeight}%` }} className="relative flex-shrink-0">
            {selectedFile ? (
              <CodeMirrorEditor
                key={selectedFile.path}
                value={fileContent}
                onChange={handleEditorChange}
                language={getLanguageFromFileName(selectedFile.name || '')}
                filename={selectedFile.path}
                height="100%"
                theme={theme}
                onSave={handleFileSave}
                autoSave={false}
                autoSaveDelay={2000}
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
            <XTerminal 
              onCommand={handleTerminalCommand} 
              isConnected={terminalConnected} 
            />
          </div>
        </div>
      </div>


      {/* Submission Form Modal */}
      {showSubmissionForm && selectedFile && (
        <SubmissionForm
          filePath={selectedFile.path}
          fileName={selectedFile.name || ''}
          onSuccess={handleSubmissionSuccess}
          onCancel={handleSubmissionCancel}
        />
      )}
    </div>
  )
}

export default EditorPage 