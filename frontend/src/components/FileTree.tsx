/**
 * AfterIDE - Enhanced File Tree Component
 * 
 * File tree with drag-and-drop, file operations, and context menus.
 */

import React, { useState, useEffect } from 'react';
import { 
  ChevronRightIcon, 
  ChevronDownIcon, 
  FolderIcon, 
  DocumentIcon,
  PlusIcon,
  EllipsisVerticalIcon
} from '@heroicons/react/24/outline';

interface FileNode {
  id: string;
  name: string;
  type: 'file' | 'folder';
  path: string;
  children?: FileNode[];
  content?: string;
  language?: string;
  isExpanded?: boolean;
}

interface FileTreeProps {
  files: FileNode[];
  selectedFileId?: string;
  onFileSelect: (file: FileNode) => void;
  onFileCreate?: (type: 'file' | 'folder', parentPath?: string) => void;
  onFileDelete?: (fileId: string) => void;
  onFileRename?: (fileId: string, newName: string) => void;
  onFileMove?: (fileId: string, newParentPath: string) => void;
}

const FileTree: React.FC<FileTreeProps> = ({
  files,
  selectedFileId,
  onFileSelect,
  onFileCreate,
  onFileDelete,
  onFileRename,
  onFileMove
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

  useEffect(() => {
    const initialExpandedFolders = new Set<string>();
    files.forEach(file => {
      if (file.isExpanded) {
        initialExpandedFolders.add(file.id);
      }
    });
    setExpandedFolders(initialExpandedFolders);
  }, [files]);

  const handleFileClick = (file: FileNode) => {
    if (file.type === 'file') {
      onFileSelect(file);
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
      setDragOverFile(fileId);
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
      if (targetFile) {
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

  const handleCreateFile = (type: 'file' | 'folder') => {
    if (onFileCreate) {
      const parentPath = contextMenu ? findFileById(files, contextMenu.fileId)?.path : undefined;
      onFileCreate(type, parentPath);
    }
    setContextMenu(null);
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
    if (renamingFile && onFileRename) {
      onFileRename(renamingFile, newFileName);
    }
    setRenamingFile(null);
    setNewFileName('');
  };

  const handleRenameCancel = () => {
    setRenamingFile(null);
    setNewFileName('');
  };

  const getLanguageIcon = (language?: string) => {
    if (!language) return '📄';
    
    switch (language.toLowerCase()) {
      case 'python':
        return '🐍';
      case 'javascript':
        return '📜';
      case 'typescript':
        return '📘';
      case 'html':
        return '🌐';
      case 'css':
        return '🎨';
      case 'json':
        return '📋';
      case 'markdown':
        return '📝';
      default:
        return '📄';
    }
  };

  const renderFileNode = (file: FileNode, depth: number = 0): React.ReactNode => {
    const isSelected = selectedFileId === file.id;
    const isDragged = draggedFile === file.id;
    const isDragOver = dragOverFile === file.id;
    const isRenaming = renamingFile === file.id;
    const isExpanded = expandedFolders.has(file.id);

    return (
      <div key={file.id}>
        <div
          className={`
            flex items-center px-2 py-1 rounded cursor-pointer select-none
            transition-all duration-200 group
            ${isSelected 
              ? 'bg-blue-100 dark:bg-blue-900 text-blue-900 dark:text-blue-100' 
              : 'hover:bg-gray-100 dark:hover:bg-gray-700'
            }
            ${isDragged ? 'opacity-50' : ''}
            ${isDragOver ? 'bg-green-100 dark:bg-green-900' : ''}
          `}
          style={{ paddingLeft: `${depth * 20 + 8}px` }}
          onClick={() => handleFileClick(file)}
          onContextMenu={(e) => handleContextMenu(e, file.id)}
          draggable={true}
          onDragStart={(e) => handleDragStart(e, file.id)}
          onDragOver={(e) => handleDragOver(e, file.id)}
          onDragLeave={handleDragLeave}
          onDrop={(e) => handleDrop(e, file.id)}
        >
          {/* Expand/Collapse Icon for folders */}
          {file.type === 'folder' && (
            <div className="w-4 h-4 mr-1">
              {isExpanded ? (
                <ChevronDownIcon className="w-4 h-4" />
              ) : (
                <ChevronRightIcon className="w-4 h-4" />
              )}
            </div>
          )}

          {/* File/Folder Icon */}
          <div className="w-4 h-4 mr-2">
            {file.type === 'folder' ? (
              <FolderIcon className="w-4 h-4 text-blue-500" />
            ) : (
              <span className="text-sm">{getLanguageIcon(file.language)}</span>
            )}
          </div>

          {/* File Name */}
          {isRenaming ? (
            <form onSubmit={handleRenameSubmit} className="flex-1">
              <input
                type="text"
                value={newFileName}
                onChange={(e) => setNewFileName(e.target.value)}
                onBlur={handleRenameCancel}
                onKeyDown={(e) => {
                  if (e.key === 'Escape') {
                    handleRenameCancel();
                  }
                }}
                className="w-full px-1 py-0.5 text-sm bg-white dark:bg-gray-800 border border-blue-500 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                autoFocus
              />
            </form>
          ) : (
            <span className="flex-1 text-sm truncate">{file.name}</span>
          )}

          {/* Context Menu Button */}
          <button
            onClick={(e) => {
              e.stopPropagation();
              handleContextMenu(e, file.id);
            }}
            className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition-opacity"
          >
            <EllipsisVerticalIcon className="w-3 h-3" />
          </button>
        </div>

        {/* Render children for expanded folders */}
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
          <button
            onClick={() => handleCreateFile('file')}
            className="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-600"
            title="New file"
          >
            <PlusIcon className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* File Tree */}
      <div className="flex-1 overflow-y-auto p-2">
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
                onClick={() => handleCreateFile('file')}
                className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center"
              >
                <PlusIcon className="w-4 h-4 mr-2" />
                New File
              </button>
              <button
                onClick={() => handleCreateFile('folder')}
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
              className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              Rename
            </button>
          )}
          
          {onFileDelete && (
            <button
              onClick={handleDeleteFile}
              className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 text-red-600 dark:text-red-400"
            >
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