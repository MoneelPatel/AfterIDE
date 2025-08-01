/**
 * AfterIDE - Enhanced File Tree Component
 * 
 * File tree with drag-and-drop, file operations, and context menus.
 */

import React, { useState, useEffect } from 'react'
import {
  DocumentIcon,
  FolderIcon,
  PlusIcon,
  ChevronRightIcon,
  ChevronDownIcon,
  PencilIcon,
  TrashIcon
} from '@heroicons/react/24/outline'

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

interface FileTreeProps {
  files: FileNode[]
  selectedFileId?: string
  onFileSelect?: (file: FileNode) => void
  onFileCreate?: (type: 'file' | 'folder', parentPath?: string, name?: string) => void
  onFileDelete?: (fileId: string) => void
  onFileRename?: (fileId: string, newName: string) => void
  onFileMove?: (fileId: string, newParentPath: string) => void
  onFolderExpansion?: (folderPath: string) => void
}

// Helper function to get file icon and language based on extension
const getFileInfo = (filename: string) => {
  const ext = filename.split('.').pop()?.toLowerCase() || ''
  
  const fileTypes: { [key: string]: { icon: string, language: string, color: string } } = {
    py: { icon: '🐍', language: 'python', color: 'text-blue-500' },
    js: { icon: '📜', language: 'javascript', color: 'text-yellow-500' },
    ts: { icon: '📘', language: 'typescript', color: 'text-blue-600' },
    jsx: { icon: '⚛️', language: 'javascript', color: 'text-cyan-500' },
    tsx: { icon: '⚛️', language: 'typescript', color: 'text-cyan-600' },
    html: { icon: '🌐', language: 'html', color: 'text-orange-500' },
    css: { icon: '🎨', language: 'css', color: 'text-blue-400' },
    json: { icon: '📋', language: 'json', color: 'text-green-500' },
    md: { icon: '📝', language: 'markdown', color: 'text-gray-600' },
    txt: { icon: '📄', language: 'text', color: 'text-gray-500' },
    sql: { icon: '🗄️', language: 'sql', color: 'text-purple-500' },
    yaml: { icon: '⚙️', language: 'yaml', color: 'text-red-500' },
    yml: { icon: '⚙️', language: 'yaml', color: 'text-red-500' },
    xml: { icon: '📰', language: 'xml', color: 'text-orange-600' },
    java: { icon: '☕', language: 'java', color: 'text-red-600' },
    cpp: { icon: '⚡', language: 'cpp', color: 'text-blue-700' },
    c: { icon: '⚡', language: 'c', color: 'text-blue-800' },
    sh: { icon: '🔧', language: 'shell', color: 'text-green-600' },
    env: { icon: '🔐', language: 'text', color: 'text-yellow-600' },
    docker: { icon: '🐳', language: 'dockerfile', color: 'text-blue-500' },
    dockerfile: { icon: '🐳', language: 'dockerfile', color: 'text-blue-500' },
  }
  
  return fileTypes[ext] || { icon: '📄', language: 'text', color: 'text-gray-500' }
}

const FileTree: React.FC<FileTreeProps> = ({
  files,
  selectedFileId,
  onFileSelect,
  onFileCreate,
  onFileDelete,
  onFileRename,
  onFileMove,
  onFolderExpansion
}) => {
  const [draggedFile, setDraggedFile] = useState<string | null>(null);
  const [dragOverFile, setDragOverFile] = useState<string | null>(null);
  const [contextMenu, setContextMenu] = useState<{
    x: number;
    y: number;
    fileId: string;
  } | null>(null);
  const [renamingFile, setRenamingFile] = useState<string | null>(null);
  const [newFileName, setNewFileName] = useState('');
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set());
  const [showCreateDropdown, setShowCreateDropdown] = useState(false);
  const [creatingFile, setCreatingFile] = useState<{ type: 'file' | 'folder', parentPath?: string } | null>(null);
  const [newFileNameInput, setNewFileNameInput] = useState('');

  useEffect(() => {
    // Preserve existing expanded state when files update
    setExpandedFolders(prevExpanded => {
      const newExpandedFolders = new Set<string>(prevExpanded);
      
      // Add any folders that have isExpanded: true in the new files data
      files.forEach(file => {
        if (file.isExpanded) {
          newExpandedFolders.add(file.id);
        }
      });
      
      // Remove folders that no longer exist in the files array
      const existingFileIds = new Set<string>();
      const collectFileIds = (fileList: FileNode[]) => {
        fileList.forEach(file => {
          existingFileIds.add(file.id);
          if (file.children) {
            collectFileIds(file.children);
          }
        });
      };
      collectFileIds(files);
      
      // Only keep expanded folders that still exist
      const validExpandedFolders = new Set<string>();
      for (const folderId of newExpandedFolders) {
        if (existingFileIds.has(folderId)) {
          validExpandedFolders.add(folderId);
        }
      }
      
      return validExpandedFolders;
    });
  }, [files]);

  const handleFileClick = (file: FileNode) => {
    if (file.type === 'file') {
      if (onFileSelect) onFileSelect(file);
    } else {
      // Toggle folder expansion
      setExpandedFolders(prev => {
        const newSet = new Set(prev);
        if (newSet.has(file.id)) {
          newSet.delete(file.id);
        } else {
          newSet.add(file.id);
        }
        return newSet;
      });
      if (onFolderExpansion) {
        onFolderExpansion(file.path);
      }
    }
  };

  const handleContextMenu = (e: React.MouseEvent, fileId: string) => {
    e.preventDefault();
    setContextMenu({
      x: e.clientX,
      y: e.clientY,
      fileId
    });
  };

  const handleDragStart = (e: React.DragEvent, fileId: string) => {
    setDraggedFile(fileId);
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', fileId);
  };

  const handleDragOver = (e: React.DragEvent, fileId: string) => {
    e.preventDefault();
    if (draggedFile && draggedFile !== fileId) {
      // Only allow dropping onto folders
      const targetFile = findFileById(files, fileId);
      if (targetFile && targetFile.type === 'folder') {
        setDragOverFile(fileId);
      }
    }
  };

  const handleDragLeave = () => {
    setDragOverFile(null);
  };

  const handleDrop = (e: React.DragEvent, targetFileId: string) => {
    e.preventDefault();
    if (draggedFile && draggedFile !== targetFileId && onFileMove) {
      // Find the target file to get its path
      const targetFile = findFileById(files, targetFileId);
      // Only allow dropping onto folders
      if (targetFile && targetFile.type === 'folder') {
        onFileMove(draggedFile, targetFile.path);
      }
    }
    setDraggedFile(null);
    setDragOverFile(null);
  };

  const findFileById = (fileList: FileNode[], fileId: string): FileNode | null => {
    for (const file of fileList) {
      if (file.id === fileId) {
        return file;
      }
      if (file.children) {
        const found = findFileById(file.children, fileId);
        if (found) return found;
      }
    }
    return null;
  };

  const handleCreateNew = (type: 'file' | 'folder') => {
    setCreatingFile({ type, parentPath: undefined });
    setNewFileNameInput(type === 'file' ? 'untitled.txt' : 'new-folder');
    setShowCreateDropdown(false);
    setContextMenu(null);
  };

  const handleCreateFileInFolder = (type: 'file' | 'folder') => {
    if (contextMenu) {
      const parentPath = findFileById(files, contextMenu.fileId)?.path;
      setCreatingFile({ type, parentPath });
      setNewFileNameInput(type === 'file' ? 'untitled.txt' : 'new-folder');
    }
    setContextMenu(null);
  };

  const confirmCreateFile = () => {
    if (creatingFile && newFileNameInput.trim() && onFileCreate) {
      onFileCreate(creatingFile.type, creatingFile.parentPath, newFileNameInput.trim());
    }
    setCreatingFile(null);
    setNewFileNameInput('');
  };

  const cancelCreateFile = () => {
    setCreatingFile(null);
    setNewFileNameInput('');
  };

  const handleDeleteFile = () => {
    if (contextMenu && onFileDelete) {
      onFileDelete(contextMenu.fileId);
    }
    setContextMenu(null);
  };

  const handleRenameFile = () => {
    if (contextMenu) {
      setRenamingFile(contextMenu.fileId);
      const file = findFileById(files, contextMenu.fileId);
      if (file) {
        setNewFileName(file.name);
      }
    }
    setContextMenu(null);
  };

  const handleRenameSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (renamingFile && onFileRename && newFileName.trim()) {
      onFileRename(renamingFile, newFileName.trim());
    }
    setRenamingFile(null);
    setNewFileName('');
  };

  const handleRenameCancel = () => {
    setRenamingFile(null);
    setNewFileName('');
  };

  const renderFileNode = (file: FileNode, depth: number = 0): React.ReactNode => {
    const isSelected = selectedFileId === file.id;
    const isExpanded = expandedFolders.has(file.id);
    const isDraggedOver = dragOverFile === file.id;
    const fileInfo = getFileInfo(file.name);

    return (
      <div key={file.id}>
        <div
          className={`
            flex items-center justify-between group cursor-pointer py-1 px-2 rounded transition-colors
            ${isSelected ? 'bg-blue-100 dark:bg-blue-900/50' : 'hover:bg-gray-100 dark:hover:bg-gray-700'}
            ${isDraggedOver ? 'bg-blue-50 dark:bg-blue-900/25 border border-blue-300 dark:border-blue-600' : ''}
          `}
          style={{ paddingLeft: `${depth * 16 + 8}px` }}
          onClick={() => handleFileClick(file)}
          onContextMenu={(e) => handleContextMenu(e, file.id)}
          draggable
          onDragStart={(e) => handleDragStart(e, file.id)}
          onDragOver={(e) => handleDragOver(e, file.id)}
          onDragLeave={handleDragLeave}
          onDrop={(e) => handleDrop(e, file.id)}
        >
          <div className="flex items-center flex-1 min-w-0">
            {file.type === 'folder' && (
              <div className="mr-1 flex-shrink-0">
                {isExpanded ? (
                  <ChevronDownIcon className="w-3 h-3 text-gray-500" />
                ) : (
                  <ChevronRightIcon className="w-3 h-3 text-gray-500" />
                )}
              </div>
            )}
            
            <div className="mr-2 flex-shrink-0">
              {file.type === 'folder' ? (
                <FolderIcon className="w-4 h-4 text-blue-500" />
              ) : (
                <span className={`text-sm ${fileInfo.color}`}>{fileInfo.icon}</span>
              )}
            </div>
            
            {renamingFile === file.id ? (
              <form onSubmit={handleRenameSubmit} className="flex-1">
                <input
                  type="text"
                  value={newFileName}
                  onChange={(e) => setNewFileName(e.target.value)}
                  onBlur={handleRenameCancel}
                  autoFocus
                  className="w-full px-1 py-0 text-sm bg-white dark:bg-gray-800 border border-blue-500 rounded focus:outline-none"
                />
              </form>
            ) : (
              <span className={`text-sm truncate ${fileInfo.color}`}>
                {file.name}
              </span>
            )}
          </div>

          <button
            onClick={(e) => {
              e.stopPropagation();
              handleContextMenu(e, file.id);
            }}
            className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition-opacity"
          >
            <PencilIcon className="w-3 h-3" />
          </button>
        </div>

        {file.type === 'folder' && isExpanded && file.children && (
          <div>
            {file.children.map(child => renderFileNode(child, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-gray-200 dark:border-gray-700">
        <h3 className="text-sm font-medium text-gray-900 dark:text-white">Files</h3>
        {onFileCreate && (
          <div className="relative">
            <button
              onClick={() => setShowCreateDropdown(!showCreateDropdown)}
              className="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-600 flex items-center"
              title="New file or folder"
            >
              <PlusIcon className="w-4 h-4" />
              <ChevronDownIcon className="w-3 h-3 ml-1" />
            </button>
            
            {/* Dropdown Menu */}
            {showCreateDropdown && (
              <>
                <div
                  className="fixed inset-0 z-40"
                  onClick={() => setShowCreateDropdown(false)}
                />
                <div className="absolute right-0 top-full mt-1 z-50 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md shadow-lg py-1 min-w-[140px]">
                  <button
                    onClick={() => handleCreateNew('file')}
                    className="w-full px-3 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center"
                  >
                    <DocumentIcon className="w-4 h-4 mr-2" />
                    New File
                  </button>
                  <button
                    onClick={() => handleCreateNew('folder')}
                    className="w-full px-3 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center"
                  >
                    <FolderIcon className="w-4 h-4 mr-2" />
                    New Folder
                  </button>
                </div>
              </>
            )}
          </div>
        )}
      </div>

      {/* File Tree */}
      <div className="flex-1 overflow-y-auto p-2">
        {/* Inline File Creation */}
        {creatingFile && (
          <div className="mb-2 p-2 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded">
            <div className="flex items-center mb-2">
              {creatingFile.type === 'folder' ? (
                <FolderIcon className="w-4 h-4 text-blue-500 mr-2" />
              ) : (
                <span className="text-sm mr-2">{getFileInfo(newFileNameInput).icon}</span>
              )}
              <span className="text-xs text-gray-600 dark:text-gray-400">
                Creating new {creatingFile.type}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={newFileNameInput}
                onChange={(e) => setNewFileNameInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    confirmCreateFile();
                  } else if (e.key === 'Escape') {
                    cancelCreateFile();
                  }
                }}
                placeholder={creatingFile.type === 'file' ? 'filename.ext' : 'folder-name'}
                autoFocus
                className="flex-1 px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded focus:outline-none focus:ring-1 focus:ring-blue-500 bg-white dark:bg-gray-700"
              />
              <button
                onClick={confirmCreateFile}
                className="px-2 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
              >
                Create
              </button>
              <button
                onClick={cancelCreateFile}
                className="px-2 py-1 text-xs bg-gray-500 text-white rounded hover:bg-gray-600 transition-colors"
              >
                Cancel
              </button>
            </div>
            {creatingFile.type === 'file' && (
              <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                <div className="flex items-center gap-2">
                  <span>Detected type:</span>
                  <span className={`font-medium ${getFileInfo(newFileNameInput).color}`}>
                    {getFileInfo(newFileNameInput).language}
                  </span>
                  <span className="text-lg">{getFileInfo(newFileNameInput).icon}</span>
                </div>
              </div>
            )}
          </div>
        )}

        {files.length === 0 ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            <DocumentIcon className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No files</p>
          </div>
        ) : (
          <div>
            {files.map(file => renderFileNode(file))}
          </div>
        )}
      </div>

      {/* Context Menu */}
      {contextMenu && (
        <div
          className="fixed z-50 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md shadow-lg py-1"
          style={{
            left: contextMenu.x,
            top: contextMenu.y
          }}
        >
          {onFileCreate && (
            <>
              <button
                onClick={() => handleCreateFileInFolder('file')}
                className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center"
              >
                <DocumentIcon className="w-4 h-4 mr-2" />
                New File
              </button>
              <button
                onClick={() => handleCreateFileInFolder('folder')}
                className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center"
              >
                <FolderIcon className="w-4 h-4 mr-2" />
                New Folder
              </button>
              <hr className="my-1 border-gray-200 dark:border-gray-700" />
            </>
          )}
          
          {onFileRename && (
            <button
              onClick={handleRenameFile}
              className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center"
            >
              <PencilIcon className="w-4 h-4 mr-2" />
              Rename
            </button>
          )}
          
          {onFileDelete && (
            <button
              onClick={handleDeleteFile}
              className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 text-red-600 dark:text-red-400 flex items-center"
            >
              <TrashIcon className="w-4 h-4 mr-2" />
              Delete
            </button>
          )}
        </div>
      )}

      {/* Overlay to close context menu */}
      {contextMenu && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setContextMenu(null)}
        />
      )}
    </div>
  );
};

export default FileTree; 