/**
 * AfterIDE - Current File Context
 * 
 * React context for managing current file information across components.
 */

import React, { createContext, useContext, useState, ReactNode } from 'react';

interface CurrentFile {
  id: string;
  name: string;
  path: string;
}

interface CurrentFileContextType {
  currentFile: CurrentFile | null;
  setCurrentFile: (file: CurrentFile | null) => void;
}

const CurrentFileContext = createContext<CurrentFileContextType | undefined>(undefined);

interface CurrentFileProviderProps {
  children: ReactNode;
}

export const CurrentFileProvider: React.FC<CurrentFileProviderProps> = ({ children }) => {
  const [currentFile, setCurrentFile] = useState<CurrentFile | null>(null);

  return (
    <CurrentFileContext.Provider value={{ currentFile, setCurrentFile }}>
      {children}
    </CurrentFileContext.Provider>
  );
};

export const useCurrentFile = (): CurrentFileContextType => {
  const context = useContext(CurrentFileContext);
  if (context === undefined) {
    throw new Error('useCurrentFile must be used within a CurrentFileProvider');
  }
  return context;
}; 