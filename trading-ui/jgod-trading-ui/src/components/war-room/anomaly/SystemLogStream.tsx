/**
 * SystemLogStream Component
 * 
 * Anomaly Layer - System Log Stream
 * 
 * 顯示系統日誌串流
 */

import { useSystemLogs } from '../../../hooks/war-room/useSystemLogs';
import type { SystemLog } from '../../../types/warRoom';

export function SystemLogStream() {
  const { data: logs, isLoading, isError, error } = useSystemLogs();

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'error':
        return 'text-red-600 dark:text-red-400';
      case 'warning':
        return 'text-yellow-600 dark:text-yellow-400';
      case 'info':
        return 'text-blue-600 dark:text-blue-400';
      default:
        return 'text-gray-600 dark:text-gray-400';
    }
  };

  const getLevelBg = (level: string) => {
    switch (level) {
      case 'error':
        return 'bg-red-50 dark:bg-red-900/20';
      case 'warning':
        return 'bg-yellow-50 dark:bg-yellow-900/20';
      case 'info':
        return 'bg-blue-50 dark:bg-blue-900/20';
      default:
        return 'bg-gray-50 dark:bg-gray-900/20';
    }
  };

  if (isLoading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          系統日誌串流
        </h3>
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-12 bg-gray-200 dark:bg-gray-700 animate-pulse rounded" />
          ))}
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          系統日誌串流
        </h3>
        <div className="text-red-500 dark:text-red-400 text-sm">
          錯誤: {error instanceof Error ? error.message : '未知錯誤'}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        系統日誌串流
      </h3>
      <div className="max-h-64 overflow-y-auto space-y-2">
        {!logs || logs.length === 0 ? (
          <div className="text-gray-500 dark:text-gray-400 text-center py-8 text-sm">
            尚未收到任何系統事件。
          </div>
        ) : (
          logs.map((log) => (
            <div
              key={log.id}
              className={`p-2 rounded text-xs ${getLevelBg(log.level)}`}
            >
              <div className="flex items-center gap-2 mb-1">
                <span className={`font-semibold ${getLevelColor(log.level)}`}>
                  [{log.level.toUpperCase()}]
                </span>
                <span className="text-gray-500 dark:text-gray-500">
                  {new Date(log.created_at).toLocaleTimeString('zh-TW')}
                </span>
                <span className="text-gray-600 dark:text-gray-400 font-mono">
                  {log.source}
                </span>
              </div>
              <div className="text-gray-900 dark:text-white">{log.message}</div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

