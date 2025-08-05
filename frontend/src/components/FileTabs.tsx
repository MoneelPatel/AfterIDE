/**
 * AfterIDE - File Tabs Component
 * 
 * File tab management system with drag-and-drop support.
 */

import React, { useState } from 'react';
import { XMarkIcon, DocumentIcon } from '@heroicons/react/24/outline';

interface FileTab {
  id: string;
  name: string;
  path: string;
  language: string;
  isDirty: boolean;
  isActive: boolean;
}

interface FileTabsProps {
  tabs: FileTab[];
  activeTabId: string;
  onTabSelect: (tabId: string) => void;
  onTabClose: (tabId: string) => void;
  onTabReorder?: (fromIndex: number, toIndex: number) => void;
}

const FileTabs: React.FC<FileTabsProps> = ({
  tabs,
  activeTabId,
  onTabSelect,
  onTabClose,
  onTabReorder
}) => {
  const [draggedTab, setDraggedTab] = useState<string | null>(null);
  const [dragOverTab, setDragOverTab] = useState<string | null>(null);

  const handleTabClick = (tabId: string) => {
    onTabSelect(tabId);
  };

  const handleTabClose = (e: React.MouseEvent, tabId: string) => {
    e.stopPropagation();
    onTabClose(tabId);
  };

  const handleDragStart = (e: React.DragEvent, tabId: string) => {
    setDraggedTab(tabId);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e: React.DragEvent, tabId: string) => {
    e.preventDefault();
    if (draggedTab && draggedTab !== tabId) {
      setDragOverTab(tabId);
    }
  };

  const handleDragLeave = () => {
    setDragOverTab(null);
  };

  const handleDrop = (e: React.DragEvent, targetTabId: string) => {
    e.preventDefault();
    if (draggedTab && draggedTab !== targetTabId && onTabReorder) {
      const fromIndex = tabs.findIndex(tab => tab.id === draggedTab);
      const toIndex = tabs.findIndex(tab => tab.id === targetTabId);
      onTabReorder(fromIndex, toIndex);
    }
    setDraggedTab(null);
    setDragOverTab(null);
  };

  const getLanguageIcon = (language: string) => {
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
      case 'csv':
        return '📊';
      default:
        return '📄';
    }
  };

  const getLanguageColor = (language: string) => {
    switch (language.toLowerCase()) {
      case 'python':
        return 'border-blue-500';
      case 'javascript':
        return 'border-yellow-500';
      case 'typescript':
        return 'border-blue-600';
      case 'html':
        return 'border-orange-500';
      case 'css':
        return 'border-purple-500';
      case 'json':
        return 'border-green-500';
      case 'markdown':
        return 'border-gray-500';
      case 'csv':
        return 'border-green-600';
      default:
        return 'border-gray-400';
    }
  };

  if (tabs.length === 0) {
    return (
      <div className="flex items-center justify-center h-12 bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <p className="text-gray-500 dark:text-gray-400 text-sm">
          No files open
        </p>
      </div>
    );
  }

  return (
    <div className="flex items-center bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 overflow-x-auto">
      {tabs.map((tab, index) => (
        <div
          key={tab.id}
          draggable={onTabReorder !== undefined}
          onDragStart={(e) => handleDragStart(e, tab.id)}
          onDragOver={(e) => handleDragOver(e, tab.id)}
          onDragLeave={handleDragLeave}
          onDrop={(e) => handleDrop(e, tab.id)}
          className={`
            flex items-center min-w-0 max-w-xs px-4 py-2 border-r border-gray-200 dark:border-gray-700 cursor-pointer
            transition-all duration-200 group
            ${tab.isActive 
              ? 'bg-white dark:bg-gray-900 border-b-2 border-blue-500' 
              : 'bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600'
            }
            ${dragOverTab === tab.id ? 'border-l-2 border-blue-500' : ''}
            ${draggedTab === tab.id ? 'opacity-50' : ''}
          `}
          onClick={() => handleTabClick(tab.id)}
        >
          {/* Language Icon */}
          <span className="mr-2 text-sm" title={tab.language}>
            {getLanguageIcon(tab.language)}
          </span>

          {/* Tab Name */}
          <span 
            className={`
              truncate text-sm font-medium
              ${tab.isActive 
                ? 'text-gray-900 dark:text-white' 
                : 'text-gray-600 dark:text-gray-300'
              }
            `}
            title={tab.path}
          >
            {tab.name}
          </span>

          {/* Dirty Indicator */}
          {tab.isDirty && (
            <div className="ml-2 w-2 h-2 bg-orange-500 rounded-full" title="Unsaved changes" />
          )}

          {/* Close Button */}
          <button
            onClick={(e) => handleTabClose(e, tab.id)}
            className={`
              ml-2 p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-600
              transition-colors duration-200 opacity-0 group-hover:opacity-100
              ${tab.isActive ? 'opacity-100' : ''}
            `}
            title="Close tab"
          >
            <XMarkIcon className="w-3 h-3 text-gray-500 dark:text-gray-400" />
          </button>
        </div>
      ))}
    </div>
  );
};

export default FileTabs; 