/**
 * SystemLogStream Component
 * 
 * Anomaly Layer - System Log Stream
 * 
 * 顯示系統日誌串流
 */

import { useState, useEffect } from 'react';

interface LogEntry {
  id: string;
  timestamp: string;
  level: 'INFO' | 'WARN' | 'ERROR' | 'DEBUG';
  message: string;
  module?: string;
}

export function SystemLogStream() {
  const [logs, setLogs] = useState<LogEntry[]>([]);

  // Placeholder: In future, this should connect to WebSocket or polling API
  useEffect(() => {
    // Simulate log entries
    const simulatedLogs: LogEntry[] = [
      {
        id: '1',
        timestamp: new Date().toISOString(),
        level: 'INFO',
        message: 'Policy Loop v2 執行完成',
        module: 'Policy',
      },
      {
        id: '2',
        timestamp: new Date().toISOString(),
        level: 'WARN',
        message: 'Signal conflict detected: 2330',
        module: 'Strategy',
      },
      {
        id: '3',
        timestamp: new Date().toISOString(),
        level: 'INFO',
        message: 'Backtest experiment logged',
        module: 'PathA',
      },
    ];
    setLogs(simulatedLogs);
  }, []);

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'ERROR':
        return 'text-red-600 dark:text-red-400';
      case 'WARN':
        return 'text-yellow-600 dark:text-yellow-400';
      case 'INFO':
        return 'text-blue-600 dark:text-blue-400';
      case 'DEBUG':
        return 'text-gray-600 dark:text-gray-400';
      default:
        return 'text-gray-600 dark:text-gray-400';
    }
  };

  const getLevelBg = (level: string) => {
    switch (level) {
      case 'ERROR':
        return 'bg-red-50 dark:bg-red-900/20';
      case 'WARN':
        return 'bg-yellow-50 dark:bg-yellow-900/20';
      case 'INFO':
        return 'bg-blue-50 dark:bg-blue-900/20';
      case 'DEBUG':
        return 'bg-gray-50 dark:bg-gray-900/20';
      default:
        return 'bg-gray-50 dark:bg-gray-900/20';
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        系統日誌串流
      </h3>
      <div className="max-h-64 overflow-y-auto space-y-2">
        {logs.length === 0 ? (
          <div className="text-gray-500 dark:text-gray-400 text-center py-8 text-sm">
            目前沒有系統日誌
          </div>
        ) : (
          logs.map((log) => (
            <div
              key={log.id}
              className={`p-2 rounded text-xs ${getLevelBg(log.level)}`}
            >
              <div className="flex items-center gap-2 mb-1">
                <span className={`font-semibold ${getLevelColor(log.level)}`}>
                  [{log.level}]
                </span>
                <span className="text-gray-500 dark:text-gray-500">
                  {new Date(log.timestamp).toLocaleTimeString('zh-TW')}
                </span>
                {log.module && (
                  <span className="text-gray-600 dark:text-gray-400 font-mono">
                    {log.module}
                  </span>
                )}
              </div>
              <div className="text-gray-900 dark:text-white">{log.message}</div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

