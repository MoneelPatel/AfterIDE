/**
 * Fallback Editor - Simple textarea-based editor to test text selection
 */

import React from 'react';

interface FallbackEditorProps {
  value: string;
  onChange: (value: string) => void;
  language?: string;
  filename?: string;
  readOnly?: boolean;
  height?: string;
}

const FallbackEditor: React.FC<FallbackEditorProps> = ({
  value,
  onChange,
  language = 'python',
  filename,
  readOnly = false,
  height = '100%'
}) => {
  return (
    <div className="fallback-editor-container h-full w-full">
      <div className="mb-2 text-sm text-gray-600 dark:text-gray-300">
        Fallback Editor: {filename} ({language})
      </div>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        readOnly={readOnly}
        className="w-full h-full p-4 font-mono text-sm border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
        style={{ 
          height: height === '100%' ? 'calc(100% - 2rem)' : height,
          fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
          fontSize: '14px',
          lineHeight: '1.5',
          tabSize: 4
        }}
        spellCheck={false}
        wrap="off"
      />
      <style dangerouslySetInnerHTML={{
        __html: `
          .fallback-editor-container textarea::selection {
            background: #0078d4 !important;
            color: #ffffff !important;
          }
          
          .fallback-editor-container textarea::-moz-selection {
            background: #0078d4 !important;
            color: #ffffff !important;
          }
        `
      }} />
    </div>
  );
};

export default FallbackEditor;