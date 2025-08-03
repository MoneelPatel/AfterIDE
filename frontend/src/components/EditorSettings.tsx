/**
 * AfterIDE - Editor Settings Component
 * 
 * Editor preferences and settings panel.
 */

import React, { useState } from 'react';
import { XMarkIcon, Cog6ToothIcon } from '@heroicons/react/24/outline';

interface EditorSettings {
  fontSize: number;
  fontFamily: string;
  tabSize: number;
  insertSpaces: boolean;
  minimap: boolean;
  lineNumbers: 'on' | 'off' | 'relative';
  renderWhitespace: 'none' | 'boundary' | 'selection' | 'trailing' | 'all';
  cursorBlinking: 'blink' | 'smooth' | 'phase' | 'expand' | 'solid';
  cursorSmoothCaretAnimation: 'on' | 'off';
  autoSave: boolean;
  autoSaveDelay: number;
  theme: 'light' | 'dark' | 'afteride-light' | 'afteride-dark';
}

interface EditorSettingsProps {
  settings: EditorSettings;
  onSettingsChange: (settings: EditorSettings) => void;
  isOpen: boolean;
  onClose: () => void;
}

const EditorSettings: React.FC<EditorSettingsProps> = ({
  settings,
  onSettingsChange,
  isOpen,
  onClose
}) => {
  const [localSettings, setLocalSettings] = useState<EditorSettings>(settings);

  const handleSettingChange = (key: keyof EditorSettings, value: any) => {
    const newSettings = { ...localSettings, [key]: value };
    setLocalSettings(newSettings);
    onSettingsChange(newSettings);
  };

  const handleSave = () => {
    onSettingsChange(localSettings);
    onClose();
  };

  const handleCancel = () => {
    setLocalSettings(settings);
    onClose();
  };

  const handleReset = () => {
    const defaultSettings: EditorSettings = {
      fontSize: 14,
      fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
      tabSize: 4,
      insertSpaces: true,
      minimap: true,
      lineNumbers: 'on',
      renderWhitespace: 'selection',
      cursorBlinking: 'blink',
      cursorSmoothCaretAnimation: 'on',
      autoSave: true,
      autoSaveDelay: 2000,
      theme: 'afteride-dark'
    };
    setLocalSettings(defaultSettings);
    onSettingsChange(defaultSettings);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-3">
            <Cog6ToothIcon className="w-6 h-6 text-gray-600 dark:text-gray-400" />
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Editor Settings
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
          <div className="space-y-6">
            {/* Appearance */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                Appearance
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Font Size
                  </label>
                  <input
                    type="range"
                    min="10"
                    max="24"
                    value={localSettings.fontSize}
                    onChange={(e) => handleSettingChange('fontSize', parseInt(e.target.value))}
                    className="w-full"
                  />
                  <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                    {localSettings.fontSize}px
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Font Family
                  </label>
                  <select
                    value={localSettings.fontFamily}
                    onChange={(e) => handleSettingChange('fontFamily', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="Monaco, Menlo, 'Ubuntu Mono', monospace">Monaco</option>
                    <option value="'Fira Code', monospace">Fira Code</option>
                    <option value="'JetBrains Mono', monospace">JetBrains Mono</option>
                    <option value="'Source Code Pro', monospace">Source Code Pro</option>
                    <option value="'Consolas', monospace">Consolas</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Theme
                  </label>
                  <select
                    value={localSettings.theme}
                    onChange={(e) => handleSettingChange('theme', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="afteride-dark">AfterIDE Dark</option>
                    <option value="afteride-light">AfterIDE Light</option>
                    <option value="dark">VS Code Dark</option>
                    <option value="light">VS Code Light</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Line Numbers
                  </label>
                  <select
                    value={localSettings.lineNumbers}
                    onChange={(e) => handleSettingChange('lineNumbers', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="on">On</option>
                    <option value="off">Off</option>
                    <option value="relative">Relative</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Editor Behavior */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                Editor Behavior
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Tab Size
                  </label>
                  <input
                    type="range"
                    min="2"
                    max="8"
                    value={localSettings.tabSize}
                    onChange={(e) => handleSettingChange('tabSize', parseInt(e.target.value))}
                    className="w-full"
                  />
                  <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                    {localSettings.tabSize} spaces
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Cursor Blinking
                  </label>
                  <select
                    value={localSettings.cursorBlinking}
                    onChange={(e) => handleSettingChange('cursorBlinking', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="blink">Blink</option>
                    <option value="smooth">Smooth</option>
                    <option value="phase">Phase</option>
                    <option value="expand">Expand</option>
                    <option value="solid">Solid</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Render Whitespace
                  </label>
                  <select
                    value={localSettings.renderWhitespace}
                    onChange={(e) => handleSettingChange('renderWhitespace', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="none">None</option>
                    <option value="boundary">Boundary</option>
                    <option value="selection">Selection</option>
                    <option value="trailing">Trailing</option>
                    <option value="all">All</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Features */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                Features
              </h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      Show Minimap
                    </label>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      Display a minimap on the right side of the editor
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={localSettings.minimap}
                    onChange={(e) => handleSettingChange('minimap', e.target.checked)}
                    className="rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500"
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      Insert Spaces
                    </label>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      Use spaces instead of tabs for indentation
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={localSettings.insertSpaces}
                    onChange={(e) => handleSettingChange('insertSpaces', e.target.checked)}
                    className="rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500"
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      Smooth Caret Animation
                    </label>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      Enable smooth cursor movement animation
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={localSettings.cursorSmoothCaretAnimation === 'on'}
                    onChange={(e) => handleSettingChange('cursorSmoothCaretAnimation', e.target.checked ? 'on' : 'off')}
                    className="rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500"
                  />
                </div>
              </div>
            </div>

            {/* Auto Save */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                Auto Save
              </h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      Enable Auto Save
                    </label>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      Automatically save files after changes
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={localSettings.autoSave}
                    onChange={(e) => handleSettingChange('autoSave', e.target.checked)}
                    className="rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500"
                  />
                </div>

                {localSettings.autoSave && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Auto Save Delay (ms)
                    </label>
                    <input
                      type="range"
                      min="500"
                      max="10000"
                      step="500"
                      value={localSettings.autoSaveDelay}
                      onChange={(e) => handleSettingChange('autoSaveDelay', parseInt(e.target.value))}
                      className="w-full"
                    />
                    <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                      {localSettings.autoSaveDelay}ms
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={handleReset}
            className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors"
          >
            Reset to Defaults
          </button>
          <div className="flex items-center space-x-3">
            <button
              onClick={handleCancel}
              className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              className="px-4 py-2 text-sm font-medium bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              Save Settings
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EditorSettings; 