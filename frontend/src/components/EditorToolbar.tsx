/**
 * AfterIDE - Editor Toolbar Component
 * 
 * Toolbar with find/replace, save, and other editor controls.
 */

import React, { useState } from 'react';
import {
  MagnifyingGlassIcon,
  ArrowPathIcon,
  DocumentArrowDownIcon,
  Cog6ToothIcon,
  EyeIcon,
  EyeSlashIcon,
  PaperAirplaneIcon
} from '@heroicons/react/24/outline';

interface EditorToolbarProps {
  onSave: () => void;
  onFind: (query: string, replace?: string) => void;
  onReplace: (query: string, replace: string) => void;
  onRefresh: () => void;
  onToggleMinimap: () => void;
  onToggleWordWrap: () => void;
  onOpenSettings: () => void;
  onSubmitForReview?: () => void;
  isDirty: boolean;
  showMinimap: boolean;
  wordWrap: boolean;
  findQuery: string;
  replaceQuery: string;
  onFindQueryChange: (query: string) => void;
  onReplaceQueryChange: (query: string) => void;
  canSubmit?: boolean;
}

const EditorToolbar: React.FC<EditorToolbarProps> = ({
  onSave,
  onFind,
  onReplace,
  onRefresh,
  onToggleMinimap,
  onToggleWordWrap,
  onOpenSettings,
  onSubmitForReview,
  isDirty,
  showMinimap,
  wordWrap,
  findQuery,
  replaceQuery,
  onFindQueryChange,
  onReplaceQueryChange,
  canSubmit = false
}) => {
  const [showFindReplace, setShowFindReplace] = useState(false);
  const [findOptions, setFindOptions] = useState({
    caseSensitive: false,
    wholeWord: false,
    regex: false
  });

  const handleFind = () => {
    if (findQuery.trim()) {
      onFind(findQuery);
    }
  };

  const handleReplace = () => {
    if (findQuery.trim() && replaceQuery.trim()) {
      onReplace(findQuery, replaceQuery);
    }
  };

  const handleReplaceAll = () => {
    if (findQuery.trim() && replaceQuery.trim()) {
      // This would typically be handled by the editor
      onReplace(findQuery, replaceQuery);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      if (e.shiftKey) {
        handleReplace();
      } else {
        handleFind();
      }
    } else if (e.key === 'Escape') {
      setShowFindReplace(false);
    }
  };

  return (
    <div className="flex items-center justify-between px-4 py-2 bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
      {/* Left side - File operations */}
      <div className="flex items-center space-x-2">
        <button
          onClick={onSave}
          disabled={!isDirty}
          className={`
            flex items-center px-3 py-1.5 rounded-md text-sm font-medium transition-colors
            ${isDirty 
              ? 'bg-blue-600 text-white hover:bg-blue-700' 
              : 'bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400 cursor-not-allowed'
            }
          `}
          title="Save file (Ctrl+S)"
        >
          <DocumentArrowDownIcon className="w-4 h-4 mr-1" />
          Save
        </button>

        <button
          onClick={onRefresh}
          className="flex items-center px-3 py-1.5 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
          title="Refresh file"
        >
          <ArrowPathIcon className="w-4 h-4 mr-1" />
          Refresh
        </button>

        {canSubmit && onSubmitForReview && (
          <button
            onClick={onSubmitForReview}
            className="flex items-center px-3 py-1.5 rounded-md text-sm font-medium bg-green-600 text-white hover:bg-green-700 transition-colors"
            title="Submit for review"
          >
            <PaperAirplaneIcon className="w-4 h-4 mr-1" />
            Submit for Review
          </button>
        )}
      </div>

      {/* Center - Find/Replace */}
      <div className="flex items-center space-x-2">
        <button
          onClick={() => setShowFindReplace(!showFindReplace)}
          className="flex items-center px-3 py-1.5 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
          title="Find/Replace (Ctrl+F)"
        >
          <MagnifyingGlassIcon className="w-4 h-4 mr-1" />
          Find
        </button>

        {showFindReplace && (
          <div className="flex items-center space-x-2 bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-md p-2 shadow-lg">
            {/* Find input */}
            <div className="flex items-center space-x-1">
              <input
                type="text"
                value={findQuery}
                onChange={(e) => onFindQueryChange(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Find..."
                className="px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
                autoFocus
              />
              <button
                onClick={handleFind}
                className="px-2 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
              >
                Find
              </button>
            </div>

            {/* Replace input */}
            <div className="flex items-center space-x-1">
              <input
                type="text"
                value={replaceQuery}
                onChange={(e) => onReplaceQueryChange(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Replace..."
                className="px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
              <button
                onClick={handleReplace}
                className="px-2 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
              >
                Replace
              </button>
              <button
                onClick={handleReplaceAll}
                className="px-2 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
              >
                All
              </button>
            </div>

            {/* Find options */}
            <div className="flex items-center space-x-2 text-xs">
              <label className="flex items-center space-x-1">
                <input
                  type="checkbox"
                  checked={findOptions.caseSensitive}
                  onChange={(e) => setFindOptions(prev => ({ ...prev, caseSensitive: e.target.checked }))}
                  className="rounded"
                />
                <span className="text-gray-600 dark:text-gray-400">Aa</span>
              </label>
              <label className="flex items-center space-x-1">
                <input
                  type="checkbox"
                  checked={findOptions.wholeWord}
                  onChange={(e) => setFindOptions(prev => ({ ...prev, wholeWord: e.target.checked }))}
                  className="rounded"
                />
                <span className="text-gray-600 dark:text-gray-400">Word</span>
              </label>
              <label className="flex items-center space-x-1">
                <input
                  type="checkbox"
                  checked={findOptions.regex}
                  onChange={(e) => setFindOptions(prev => ({ ...prev, regex: e.target.checked }))}
                  className="rounded"
                />
                <span className="text-gray-600 dark:text-gray-400">.*</span>
              </label>
            </div>
          </div>
        )}
      </div>

      {/* Right side - Editor options */}
      <div className="flex items-center space-x-2">
        <button
          onClick={onToggleMinimap}
          className={`
            flex items-center px-3 py-1.5 rounded-md text-sm font-medium transition-colors
            ${showMinimap 
              ? 'bg-blue-600 text-white hover:bg-blue-700' 
              : 'text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
            }
          `}
          title="Toggle minimap"
        >
          {showMinimap ? (
            <EyeIcon className="w-4 h-4 mr-1" />
          ) : (
            <EyeSlashIcon className="w-4 h-4 mr-1" />
          )}
          Minimap
        </button>

        <button
          onClick={onToggleWordWrap}
          className={`
            flex items-center px-3 py-1.5 rounded-md text-sm font-medium transition-colors
            ${wordWrap 
              ? 'bg-blue-600 text-white hover:bg-blue-700' 
              : 'text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
            }
          `}
          title="Toggle word wrap"
        >
          <Cog6ToothIcon className="w-4 h-4 mr-1" />
          Wrap
        </button>

        <button
          onClick={onOpenSettings}
          className="flex items-center px-3 py-1.5 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
          title="Editor settings"
        >
          <Cog6ToothIcon className="w-4 h-4 mr-1" />
          Settings
        </button>
      </div>
    </div>
  );
};

export default EditorToolbar; 