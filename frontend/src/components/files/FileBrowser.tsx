/**
 * OneDrive file browser component
 */
'use client';

import { useState, useEffect } from 'react';
import { apiClient, FileItem } from '@/lib/api-client';

interface FileBrowserProps {
  connectionId: string;
  onSelectionChange?: (selectedPaths: string[]) => void;
}

export function FileBrowser({ connectionId, onSelectionChange }: FileBrowserProps) {
  const [currentPath, setCurrentPath] = useState('/');
  const [items, setItems] = useState<FileItem[]>([]);
  const [selectedFolders, setSelectedFolders] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadFolder(currentPath);
  }, [currentPath, connectionId]);

  const loadFolder = async (path: string) => {
    try {
      setLoading(true);
      setError(null);

      const response = await apiClient.browseFiles(connectionId, path);
      setItems(response.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load folder');
    } finally {
      setLoading(false);
    }
  };

  const handleFolderClick = (item: FileItem) => {
    if (item.is_folder) {
      setCurrentPath(item.path);
    }
  };

  const handleFolderSelect = (path: string) => {
    const newSelected = new Set(selectedFolders);
    if (newSelected.has(path)) {
      newSelected.delete(path);
    } else {
      newSelected.add(path);
    }
    setSelectedFolders(newSelected);

    if (onSelectionChange) {
      onSelectionChange(Array.from(newSelected));
    }
  };

  const goUp = () => {
    if (currentPath === '/') return;

    const parts = currentPath.split('/').filter((p) => p);
    parts.pop();
    setCurrentPath(parts.length > 0 ? '/' + parts.join('/') : '/');
  };

  if (loading) {
    return (
      <div className="border rounded-lg p-8 text-center">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="border border-red-200 rounded-lg p-4 bg-red-50">
        <p className="text-red-800 text-sm">{error}</p>
        <button
          onClick={() => loadFolder(currentPath)}
          className="mt-2 text-sm text-red-600 hover:text-red-700 underline"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="border rounded-lg overflow-hidden">
      {/* Header */}
      <div className="bg-muted p-4 border-b flex items-center justify-between">
        <div className="flex items-center gap-2">
          {currentPath !== '/' && (
            <button
              onClick={goUp}
              className="text-sm px-3 py-1 rounded hover:bg-background"
            >
              ← Back
            </button>
          )}
          <span className="text-sm font-mono">{currentPath || '/'}</span>
        </div>
        <span className="text-sm text-muted-foreground">
          {selectedFolders.size} folder(s) selected
        </span>
      </div>

      {/* File list */}
      <div className="divide-y max-h-96 overflow-y-auto">
        {items.length === 0 ? (
          <div className="p-8 text-center text-muted-foreground">
            <p>No items in this folder</p>
          </div>
        ) : (
          items.map((item) => (
            <div
              key={item.id}
              className="p-3 hover:bg-muted/50 flex items-center gap-3"
            >
              {item.is_folder && (
                <input
                  type="checkbox"
                  checked={selectedFolders.has(item.path)}
                  onChange={() => handleFolderSelect(item.path)}
                  className="w-4 h-4"
                />
              )}

              <button
                onClick={() => handleFolderClick(item)}
                className="flex-1 text-left flex items-center gap-2"
                disabled={!item.is_folder}
              >
                <span className="text-lg">
                  {item.is_folder ? '📁' : '📄'}
                </span>
                <span className="text-sm">{item.name}</span>
              </button>

              {item.size && (
                <span className="text-xs text-muted-foreground">
                  {formatBytes(item.size)}
                </span>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}
