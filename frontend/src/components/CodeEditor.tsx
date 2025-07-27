import React, { useRef, useEffect } from 'react'
import Editor from '@monaco-editor/react'
import { useTheme } from '../contexts/ThemeContext'

interface CodeEditorProps {
  value: string
  language?: string
  onChange: (value: string) => void
  onSave?: () => void
  readOnly?: boolean
  fileName?: string
}

const CodeEditor: React.FC<CodeEditorProps> = ({
  value,
  language = 'python',
  onChange,
  onSave,
  readOnly = false,
  fileName
}) => {
  const { theme } = useTheme()
  const editorRef = useRef<any>(null)

  const handleEditorDidMount = (editor: any) => {
    editorRef.current = editor
    
    // Add keyboard shortcuts
    editor.addCommand(2048 | 31, () => { // Ctrl/Cmd + S
      if (onSave) {
        onSave()
      }
    })
  }

  const getLanguageFromFileName = (name: string) => {
    const extension = name.split('.').pop()?.toLowerCase()
    switch (extension) {
      case 'py':
        return 'python'
      case 'js':
        return 'javascript'
      case 'ts':
        return 'typescript'
      case 'jsx':
        return 'javascript'
      case 'tsx':
        return 'typescript'
      case 'json':
        return 'json'
      case 'md':
        return 'markdown'
      case 'html':
        return 'html'
      case 'css':
        return 'css'
      default:
        return 'plaintext'
    }
  }

  const editorLanguage = fileName ? getLanguageFromFileName(fileName) : language

  return (
    <div className="h-full w-full">
      <Editor
        height="100%"
        defaultLanguage={editorLanguage}
        language={editorLanguage}
        value={value}
        onChange={(value) => onChange(value || '')}
        onMount={handleEditorDidMount}
        theme={theme === 'dark' ? 'vs-dark' : 'light'}
        options={{
          minimap: { enabled: false },
          fontSize: 14,
          fontFamily: 'JetBrains Mono, Fira Code, Monaco, Consolas, monospace',
          lineNumbers: 'on',
          roundedSelection: false,
          scrollBeyondLastLine: false,
          readOnly: readOnly,
          automaticLayout: true,
          wordWrap: 'on',
          folding: true,
          foldingStrategy: 'indentation',
          showFoldingControls: 'always',
          renderLineHighlight: 'all',
          selectOnLineNumbers: true,
          cursorBlinking: 'smooth',
          cursorSmoothCaretAnimation: 'on',
          smoothScrolling: true,
          tabSize: 2,
          insertSpaces: true,
          detectIndentation: true,
          trimAutoWhitespace: true,
          largeFileOptimizations: true,
          suggest: {
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
          },
        }}
      />
    </div>
  )
}

export default CodeEditor 