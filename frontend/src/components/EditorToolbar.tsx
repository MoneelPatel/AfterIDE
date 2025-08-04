/**
 * AfterIDE - Editor Toolbar Component
 * 
 * Toolbar with save and submit controls.
 */

import React from 'react';
import {
  DocumentArrowDownIcon,
  PaperAirplaneIcon
} from '@heroicons/react/24/outline';

interface EditorToolbarProps {
  onSave: (content?: string) => void;
  onSubmitForReview?: () => void;
  isDirty: boolean;
  canSubmit?: boolean;
}

const EditorToolbar: React.FC<EditorToolbarProps> = ({
  onSave,
  onSubmitForReview,
  isDirty,
  canSubmit = false
}) => {
  return (
    <div className="flex items-center justify-between px-4 py-2 bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
      {/* Left side - File operations */}
      <div className="flex items-center space-x-2">
        <button
          onClick={() => onSave()}
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

      {/* Right side - Empty for now */}
      <div className="flex items-center space-x-2">
      </div>
    </div>
  );
};

export default EditorToolbar; 