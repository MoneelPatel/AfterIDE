/**
 * CodeMirror Editor Component
 * 
 * Modern code editor with syntax highlighting and guaranteed text selection
 */

import React, { useEffect, useRef } from 'react';
import { EditorView, basicSetup } from 'codemirror';
import { EditorState } from '@codemirror/state';
import { python } from '@codemirror/lang-python';
import { oneDark } from '@codemirror/theme-one-dark';
import { keymap } from '@codemirror/view';

interface CodeMirrorEditorProps {
  value: string;
  onChange: (value: string) => void;
  language?: string;
  filename?: string;
  readOnly?: boolean;
  height?: string;
  theme?: string;
  onSave?: (content?: string) => void;
  autoSave?: boolean;
  autoSaveDelay?: number;
}

const CodeMirrorEditor: React.FC<CodeMirrorEditorProps> = ({
  value,
  onChange,
  language = 'python',
  filename,
  readOnly = false,
  height = '100%',
  theme = 'light',
  onSave,
  autoSave = true,
  autoSaveDelay = 2000
}) => {
  const editorRef = useRef<HTMLDivElement>(null);
  const viewRef = useRef<EditorView | null>(null);
  const autoSaveTimerRef = useRef<NodeJS.Timeout | null>(null);
  const lastSavedRef = useRef<string>(value);

  useEffect(() => {
    if (!editorRef.current) return;

    // Create editor extensions
    const extensions = [
      basicSetup,
      python(), // Always use Python for now
      EditorView.updateListener.of((update) => {
        if (update.docChanged) {
          const newValue = update.state.doc.toString();
          onChange(newValue);
          
          // Auto-save functionality
          if (autoSave && onSave) {
            // Clear existing timer
            if (autoSaveTimerRef.current) {
              clearTimeout(autoSaveTimerRef.current);
            }
            
            // Set new timer
            autoSaveTimerRef.current = setTimeout(() => {
              if (newValue !== lastSavedRef.current) {
                onSave(newValue);
                lastSavedRef.current = newValue;
              }
            }, autoSaveDelay);
          }
        }
      }),
      // Add save keyboard shortcut
      keymap.of([
        {
          key: 'Ctrl-s',
          mac: 'Cmd-s',
          run: (view) => {
            if (onSave) {
              // Get current content directly from the editor
              const currentContent = view.state.doc.toString();
              onSave(currentContent);
            }
            return true;
          }
        }
      ]),
      EditorView.theme({
        '&': {
          height: '100%',
          fontSize: '14px',
          fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace'
        },
        '.cm-content': {
          padding: '10px',
          minHeight: '100%'
        },
        '.cm-focused': {
          outline: 'none'
        },
        '.cm-editor': {
          height: '100%'
        },
        '.cm-scroller': {
          height: '100%'
        },
        // Force text selection styling
        '.cm-content ::selection': {
          backgroundColor: '#0078d4 !important',
          color: '#ffffff !important'
        },
        '.cm-content ::-moz-selection': {
          backgroundColor: '#0078d4 !important',
          color: '#ffffff !important'
        }
      }),
      EditorState.readOnly.of(readOnly)
    ];

    // Add dark theme if needed
    if (theme === 'dark' || theme === 'vs-dark') {
      extensions.push(oneDark);
    }

    // Create initial state
    const state = EditorState.create({
      doc: value,
      extensions
    });

    // Create editor view
    const view = new EditorView({
      state,
      parent: editorRef.current
    });

    viewRef.current = view;

    // Cleanup function
    return () => {
      view.destroy();
      viewRef.current = null;
      // Clear auto-save timer
      if (autoSaveTimerRef.current) {
        clearTimeout(autoSaveTimerRef.current);
        autoSaveTimerRef.current = null;
      }
    };
  }, [theme, readOnly]); // Only recreate on theme/readOnly change

  // Update content when value prop changes
  useEffect(() => {
    if (viewRef.current && value !== viewRef.current.state.doc.toString()) {
      const transaction = viewRef.current.state.update({
        changes: {
          from: 0,
          to: viewRef.current.state.doc.length,
          insert: value
        }
      });
      viewRef.current.dispatch(transaction);
    }
  }, [value]);

  return (
    <div className="codemirror-editor-container h-full w-full">
      <div 
        ref={editorRef} 
        className="h-full w-full border border-gray-300 dark:border-gray-600 rounded"
        style={{ height: height }}
      />
      <style dangerouslySetInnerHTML={{
        __html: `
          .codemirror-editor-container .cm-content ::selection {
            background: #0078d4 !important;
            color: #ffffff !important;
          }
          
          .codemirror-editor-container .cm-content ::-moz-selection {
            background: #0078d4 !important;
            color: #ffffff !important;
          }
          
          .codemirror-editor-container .cm-line ::selection {
            background: #0078d4 !important;
            color: #ffffff !important;
          }
          
          .codemirror-editor-container .cm-line ::-moz-selection {
            background: #0078d4 !important;
            color: #ffffff !important;
          }
        `
      }} />
    </div>
  );
};

export default CodeMirrorEditor;