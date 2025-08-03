/**
 * AfterIDE - Monaco Editor Component
 * 
 * Professional-grade code editor with Python language support and advanced features.
 */

import React, { useRef, useEffect, useState, useCallback } from 'react';
import { useTheme } from '../contexts/ThemeContext';
import { useWebSocket } from '../contexts/WebSocketContext';
import Editor, { OnMount, OnChange, BeforeMount } from '@monaco-editor/react';
import * as monaco from 'monaco-editor';

interface MonacoEditorProps {
  value: string;
  onChange: (value: string) => void;
  language?: string;
  filename?: string;
  readOnly?: boolean;
  height?: string;
  onSave?: () => void;
  autoSave?: boolean;
  autoSaveDelay?: number;
  showMinimap?: boolean;
}

interface EditorState {
  isDirty: boolean;
  lastSaved: string;
  autoSaveTimer: NodeJS.Timeout | null;
}

const MonacoEditor: React.FC<MonacoEditorProps> = ({
  value,
  onChange,
  language = 'python',
  filename,
  readOnly = false,
  height = '100%',
  onSave,
  autoSave = true,
  autoSaveDelay = 2000,
  showMinimap = true
}) => {
  const { theme } = useTheme();
  const { sendFilesMessage, filesConnected } = useWebSocket();
  const editorRef = useRef<monaco.editor.IStandaloneCodeEditor | null>(null);
  const monacoRef = useRef<typeof monaco | null>(null);
  const [editorState, setEditorState] = useState<EditorState>({
    isDirty: false,
    lastSaved: value,
    autoSaveTimer: null
  });

  // Initialize editor when value or container changes
  // Configure Monaco Editor before mount
  const handleBeforeMount: BeforeMount = (monaco) => {
    monacoRef.current = monaco;
    
    // Configure Python language features
    monaco.languages.register({ id: 'python' });
    
    // Python syntax highlighting
    monaco.languages.setMonarchTokensProvider('python', {
      defaultToken: '',
      tokenPostfix: '.python',

      keywords: [
        'and', 'as', 'assert', 'break', 'class', 'continue', 'def',
        'del', 'elif', 'else', 'except', 'exec', 'finally', 'for',
        'from', 'global', 'if', 'import', 'in', 'is', 'lambda', 'None',
        'not', 'or', 'pass', 'print', 'raise', 'return', 'try',
        'while', 'yield', 'del', 'except', 'exec', 'finally',
        'from', 'global', 'import', 'lambda', 'pass', 'print',
        'raise', 'return', 'try', 'with', 'yield', 'async', 'await'
      ],

      brackets: [
        { open: '{', close: '}', token: 'delimiter.curly' },
        { open: '[', close: ']', token: 'delimiter.square' },
        { open: '(', close: ')', token: 'delimiter.parenthesis' }
      ],

      operators: [
        '=', '>', '<', '!', '~', '?', ':', '==', '<=', '>=', '!=',
        '<>', '&&', '||', '++', '--', '+', '-', '*', '/', '&',
        '|', '^', '%', '<<', '>>', '>>>', '+=', '-=', '*=', '/=',
        '&=', '|=', '^=', '%=', '<<=', '>>=', '>>>='
      ],

      symbols: /[=><!~?:&|+\-*\/\^%]+/,
      escapes: /\\(?:[abfnrtv\\"']|x[0-9A-Fa-f]{1,4}|u[0-9A-Fa-f]{4}|U[0-9A-Fa-f]{8})/,

      tokenizer: {
        root: [
          [/[a-zA-Z_]\w*/, {
            cases: {
              '@keywords': 'keyword',
              '@default': 'identifier'
            }
          }],
          { include: '@whitespace' },
          { include: '@numbers' },
          [/[{}()\[\]]/, '@brackets'],
          [/@symbols/, {
            cases: {
              '@operators': 'operator',
              '@default': ''
            }
          }],
          [/'/, 'string', '@string_single'],
          [/"/, 'string', '@string_double'],
          [/#.*$/, 'comment']
        ],

        whitespace: [
          [/\s+/, 'white']
        ],

        numbers: [
          [/\d*\.\d+([eE][\-+]?\d+)?/, 'number.float'],
          [/0[xX][0-9a-fA-F]+/, 'number.hex'],
          [/\d+/, 'number']
        ],

        string_single: [
          [/[^\\']+/, 'string'],
          [/@escapes/, 'string.escape'],
          [/\\./, 'string.escape.invalid'],
          [/'/, 'string', '@pop']
        ],

        string_double: [
          [/[^\\"]+/, 'string'],
          [/@escapes/, 'string.escape'],
          [/\\./, 'string.escape.invalid'],
          [/"/, 'string', '@pop']
        ]
      }
    });

    // Python code completion
    monaco.languages.registerCompletionItemProvider('python', {
      provideCompletionItems: (model, position) => {
        const word = model.getWordUntilPosition(position);
        const range = {
          startLineNumber: position.lineNumber,
          endLineNumber: position.lineNumber,
          startColumn: word.startColumn,
          endColumn: word.endColumn
        };

        const suggestions = [
          {
            label: 'print',
            kind: monaco.languages.CompletionItemKind.Function,
            insertText: 'print(${1:value})',
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            documentation: 'Print a value to the console',
            range: range
          },
          {
            label: 'def',
            kind: monaco.languages.CompletionItemKind.Snippet,
            insertText: [
              'def ${1:function_name}(${2:parameters}):',
              '\t${3:pass}'
            ].join('\n'),
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            documentation: 'Define a function',
            range: range
          },
          {
            label: 'class',
            kind: monaco.languages.CompletionItemKind.Snippet,
            insertText: [
              'class ${1:ClassName}:',
              '\tdef __init__(self):',
              '\t\t${2:pass}'
            ].join('\n'),
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            documentation: 'Define a class',
            range: range
          },
          {
            label: 'if',
            kind: monaco.languages.CompletionItemKind.Snippet,
            insertText: [
              'if ${1:condition}:',
              '\t${2:pass}'
            ].join('\n'),
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            documentation: 'If statement',
            range: range
          },
          {
            label: 'for',
            kind: monaco.languages.CompletionItemKind.Snippet,
            insertText: [
              'for ${1:item} in ${2:iterable}:',
              '\t${3:pass}'
            ].join('\n'),
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            documentation: 'For loop',
            range: range
          },
          {
            label: 'while',
            kind: monaco.languages.CompletionItemKind.Snippet,
            insertText: [
              'while ${1:condition}:',
              '\t${2:pass}'
            ].join('\n'),
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            documentation: 'While loop',
            range: range
          },
          {
            label: 'try',
            kind: monaco.languages.CompletionItemKind.Snippet,
            insertText: [
              'try:',
              '\t${1:pass}',
              'except ${2:Exception} as ${3:e}:',
              '\t${4:pass}'
            ].join('\n'),
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            documentation: 'Try-except block',
            range: range
          },
          {
            label: 'import',
            kind: monaco.languages.CompletionItemKind.Snippet,
            insertText: 'import ${1:module}',
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            documentation: 'Import a module',
            range: range
          },
          {
            label: 'from',
            kind: monaco.languages.CompletionItemKind.Snippet,
            insertText: 'from ${1:module} import ${2:name}',
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            documentation: 'Import from module',
            range: range
          }
        ];

        return { suggestions };
      }
    });

    // Configure editor options
    monaco.editor.defineTheme('afteride-dark', {
      base: 'vs-dark',
      inherit: true,
      rules: [
        { token: 'keyword', foreground: '569cd6' },
        { token: 'string', foreground: 'ce9178' },
        { token: 'number', foreground: 'b5cea8' },
        { token: 'comment', foreground: '6a9955' },
        { token: 'operator', foreground: 'd4d4d4' }
      ],
      colors: {
        'editor.background': '#1e1e1e',
        'editor.foreground': '#d4d4d4',
        'editor.lineHighlightBackground': '#2a2d2e',
        'editor.lineHighlightBorder': '#007acc',
        'editor.selectionBackground': '#264f78',
        'editor.inactiveSelectionBackground': '#3a3d41',
        'editorCursor.foreground': '#d4d4d4'
      }
    });

    monaco.editor.defineTheme('afteride-light', {
      base: 'vs',
      inherit: true,
      rules: [
        { token: 'keyword', foreground: '0000ff' },
        { token: 'string', foreground: 'a31515' },
        { token: 'number', foreground: '098658' },
        { token: 'comment', foreground: '008000' },
        { token: 'operator', foreground: '000000' }
      ],
      colors: {
        'editor.background': '#ffffff',
        'editor.foreground': '#000000',
        'editor.lineHighlightBackground': '#f7f7f7',
        'editor.lineHighlightBorder': '#007acc',
        'editor.selectionBackground': '#add6ff',
        'editor.inactiveSelectionBackground': '#e5ebf1',
        'editorCursor.foreground': '#000000'
      }
    });
  };

  // Handle editor mount
  const handleEditorDidMount: OnMount = (editor, monaco) => {
    editorRef.current = editor;
    
    // Set up keyboard shortcuts
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => {
      handleSave();
    });

    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyF, () => {
      editor.getAction('actions.find')?.run();
    });

    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyMod.Shift | monaco.KeyCode.KeyF, () => {
      editor.getAction('editor.action.startFindReplaceAction')?.run();
    });

    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyD, () => {
      editor.getAction('editor.action.selectHighlights')?.run();
    });

    // Set up auto-save
    if (autoSave) {
      editor.onDidChangeModelContent(() => {
        setEditorState(prev => ({
          ...prev,
          isDirty: true
        }));
        
        // Clear existing timer
        if (editorState.autoSaveTimer) {
          clearTimeout(editorState.autoSaveTimer);
        }
        
        // Set new timer
        const timer = setTimeout(() => {
          handleAutoSave();
        }, autoSaveDelay);
        
        setEditorState(prev => ({
          ...prev,
          autoSaveTimer: timer
        }));
      });
    }

    // Set up error markers
    setupErrorDetection(editor);
  };

  // Handle editor changes
  const handleEditorChange: OnChange = (value) => {
    if (value !== undefined) {
      onChange(value);
    }
  };

  // Set up error detection
  const setupErrorDetection = (editor: monaco.editor.IStandaloneCodeEditor) => {
    // Simple Python syntax error detection
    const validatePython = (code: string) => {
      const errors: monaco.editor.IMarkerData[] = [];
      
      const lines = code.split('\n');
      lines.forEach((line, index) => {
        const lineNumber = index + 1;
        
        // Check for unmatched parentheses
        const openParens = (line.match(/\(/g) || []).length;
        const closeParens = (line.match(/\)/g) || []).length;
        const openBrackets = (line.match(/\[/g) || []).length;
        const closeBrackets = (line.match(/\]/g) || []).length;
        const openBraces = (line.match(/\{/g) || []).length;
        const closeBraces = (line.match(/\}/g) || []).length;
        
        if (openParens !== closeParens) {
          errors.push({
            message: 'Unmatched parentheses',
            severity: monaco.MarkerSeverity.Error,
            startLineNumber: lineNumber,
            startColumn: 1,
            endLineNumber: lineNumber,
            endColumn: line.length + 1
          });
        }
        
        if (openBrackets !== closeBrackets) {
          errors.push({
            message: 'Unmatched brackets',
            severity: monaco.MarkerSeverity.Error,
            startLineNumber: lineNumber,
            startColumn: 1,
            endLineNumber: lineNumber,
            endColumn: line.length + 1
          });
        }
        
        if (openBraces !== closeBraces) {
          errors.push({
            message: 'Unmatched braces',
            severity: monaco.MarkerSeverity.Error,
            startLineNumber: lineNumber,
            startColumn: 1,
            endLineNumber: lineNumber,
            endColumn: line.length + 1
          });
        }
        
        // Check for indentation issues
        if (line.trim() && !line.startsWith(' ') && !line.startsWith('\t')) {
          const prevLine = lines[index - 1];
          if (prevLine && prevLine.trim().endsWith(':')) {
            // Previous line ends with colon, this line should be indented
            if (!line.startsWith(' ') && !line.startsWith('\t')) {
              errors.push({
                message: 'Expected indentation after colon',
                severity: monaco.MarkerSeverity.Warning,
                startLineNumber: lineNumber,
                startColumn: 1,
                endLineNumber: lineNumber,
                endColumn: line.length + 1
              });
            }
          }
        }
      });
      
      return errors;
    };

    // Update markers when content changes
    const updateMarkers = () => {
      const model = editor.getModel();
      if (model) {
        const errors = validatePython(model.getValue());
        monaco.editor.setModelMarkers(model, 'python', errors);
      }
    };

    editor.onDidChangeModelContent(updateMarkers);
    updateMarkers(); // Initial validation
  };

  // Handle save
  const handleSave = useCallback(() => {
    console.log('🔧 handleSave called', { filename, filesConnected, language });
    
    if (editorRef.current && filename) {
      const content = editorRef.current.getValue();
      console.log('🔧 Editor content length:', content.length);
      
      // Send file update via WebSocket
      if (filesConnected) {
        const message = {
          type: 'file_update',
          filename: filename,
          content: content,
          language: language
        };
        console.log('🔧 Sending file update message:', message);
        sendFilesMessage(message);
      } else {
        console.error('🔧 Files WebSocket not connected!');
      }
      
      // Call onSave callback
      if (onSave) {
        onSave();
      }
      
      setEditorState(prev => ({
        ...prev,
        isDirty: false,
        lastSaved: content
      }));
      
      console.log('🔧 Save completed');
    } else {
      console.error('🔧 Cannot save: editor not ready or no filename', { 
        hasEditor: !!editorRef.current, 
        filename 
      });
    }
  }, [filename, filesConnected, sendFilesMessage, onSave, language]);

  // Handle auto-save
  const handleAutoSave = useCallback(() => {
    console.log('🔧 handleAutoSave called', { autoSave, filename, filesConnected });
    
    if (autoSave && editorRef.current && filename) {
      const content = editorRef.current.getValue();
      
      // Only auto-save if content has changed
      if (content !== editorState.lastSaved) {
        console.log('🔧 Auto-saving file, content changed');
        
        if (filesConnected) {
          const message = {
            type: 'file_update',
            filename: filename,
            content: content,
            language: language
          };
          console.log('🔧 Sending auto-save message:', message);
          sendFilesMessage(message);
        } else {
          console.error('🔧 Files WebSocket not connected for auto-save!');
        }
        
        setEditorState(prev => ({
          ...prev,
          isDirty: false,
          lastSaved: content
        }));
        
        console.log('🔧 Auto-save completed');
      } else {
        console.log('🔧 Auto-save skipped - content unchanged');
      }
    } else {
      console.log('🔧 Auto-save conditions not met', { 
        autoSave, 
        hasEditor: !!editorRef.current, 
        filename,
        filesConnected 
      });
    }
  }, [autoSave, filename, filesConnected, sendFilesMessage, language, editorState.lastSaved]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (editorState.autoSaveTimer) {
        clearTimeout(editorState.autoSaveTimer);
      }
    };
  }, [editorState.autoSaveTimer]);

  // Update editor value when prop changes
  useEffect(() => {
    if (editorRef.current && value !== editorRef.current.getValue()) {
      editorRef.current.setValue(value);
      setEditorState(prev => ({
        ...prev,
        lastSaved: value,
        isDirty: false
      }));
    }
  }, [value]);

  // Update minimap setting when prop changes
  useEffect(() => {
    if (editorRef.current) {
      editorRef.current.updateOptions({
        minimap: { enabled: showMinimap }
      });
    }
  }, [showMinimap]);

  return (
    <div className="monaco-editor-container h-full w-full">
      <Editor
        height="100%"
        language={language}
        value={value}
        onChange={handleEditorChange}
        onMount={handleEditorDidMount}
        beforeMount={handleBeforeMount}
        theme={theme === 'dark' ? 'afteride-dark' : 'afteride-light'}
        options={{
          readOnly: readOnly,
          minimap: { enabled: showMinimap },
          scrollBeyondLastLine: false,
          fontSize: 14,
          fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
          lineNumbers: 'on',
          lineNumbersMinChars: 3,
          lineDecorationsWidth: 10,
          glyphMargin: false,
          folding: false,
          showFoldingControls: 'never',
          wordWrap: 'on',
          automaticLayout: true,
          suggestOnTriggerCharacters: true,
          quickSuggestions: true,
          parameterHints: {
            enabled: true
          },
          hover: {
            enabled: true
          },
          contextmenu: true,
          mouseWheelZoom: true,
          smoothScrolling: true,
          cursorBlinking: 'blink',
          cursorSmoothCaretAnimation: 'on',
          renderWhitespace: 'selection',
          renderControlCharacters: false,
          renderLineHighlight: 'line',
          selectOnLineNumbers: true,
          useTabStops: false,
          tabSize: 4,
          insertSpaces: true,
          detectIndentation: true,
          trimAutoWhitespace: true,
          largeFileOptimizations: true,
          wordBasedSuggestions: true,
          scrollbar: {
            vertical: 'visible',
            horizontal: 'visible',
            verticalScrollbarSize: 14,
            horizontalScrollbarSize: 14
          },
          suggest: {
            insertMode: 'replace',
            showKeywords: true,
            showSnippets: true,
            showClasses: true,
            showFunctions: true,
            showVariables: true,
            showModules: true,
            showProperties: true,
            showEvents: true,
            showOperators: true,
            showUnits: true,
            showValues: true,
            showConstants: true,
            showEnums: true,
            showEnumMembers: true,
            showColors: true,
            showFiles: true,
            showReferences: true,
            showFolders: true,
            showTypeParameters: true,
            showWords: true,
            snippetsPreventQuickSuggestions: false,
            localityBonus: false,
            shareSuggestSelections: false,
            showIcons: true
          }
        }}
      />
    </div>
  );
};

export default MonacoEditor; 