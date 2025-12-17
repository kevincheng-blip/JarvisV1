// @ts-nocheck
/**
 * TopPredictionsPanel Component
 * 
 * War Room V2 - Top Predictions Panel
 * 
 * 顯示 Top 5 Long 和 Top 5 Short Predictions (V2)
 */

import { useTopLongPredictions, useTopShortPredictions } from "../../hooks/war-room/usePredictions";
import type { TopLongItem, TopShortItem } from "../../types/warRoom";

interface TopPredictionsPanelProps {
  onPredictionClick?: (symbol: string, item: TopLongItem | TopShortItem) => void;
}

export function TopPredictionsPanel({ onPredictionClick }: TopPredictionsPanelProps) {
  const { 
    data: longPredictions, 
    isLoading: longLoading, 
    isError: longError,
    error: longErrorDetail
  } = useTopLongPredictions({ version: "v2", limit: 5 });
  
  const { 
    data: shortPredictions, 
    isLoading: shortLoading, 
    isError: shortError,
    error: shortErrorDetail
  } = useTopShortPredictions({ version: "v2", limit: 5 });

  const handleClick = (symbol: string, item: TopLongItem | TopShortItem) => {
    if (onPredictionClick) {
      onPredictionClick(symbol, item);
    }
  };

  // Skeleton row
  const SkeletonRow = () => (
    <div className="p-3 border border-gray-200 dark:border-gray-700 rounded animate-pulse">
      <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-24 mb-2" />
      <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-32" />
    </div>
  );

  // Error display
  const ErrorMessage = ({ message }: { message: string }) => (
    <div className="p-4 text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 rounded">
      {message}
    </div>
  );

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Top 5 Predictions (V2)
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Long Predictions */}
        <div>
          <h4 className="text-md font-medium text-green-600 dark:text-green-400 mb-3">
            Top 5 Long
          </h4>
          {longLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <SkeletonRow key={i} />
              ))}
            </div>
          ) : longError ? (
            <ErrorMessage message={`載入失敗: ${longErrorDetail instanceof Error ? longErrorDetail.message : '未知錯誤'}`} />
          ) : !longPredictions || longPredictions.length === 0 ? (
            <div className="text-gray-500 dark:text-gray-400 text-sm py-4">
              暫無資料
            </div>
          ) : (
            <div className="space-y-2">
              {longPredictions.map((item, index) => (
                <div
                  key={item.symbol}
                  className="p-3 border border-gray-200 dark:border-gray-700 rounded cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                  onClick={() => handleClick(item.symbol, item)}
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="font-semibold text-gray-900 dark:text-white">
                        {item.symbol} - {item.name}
                      </div>
                      <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                        Final: <span className="font-medium">{item.final_score.toFixed(2)}</span>
                        {item.raw_score !== undefined && (
                          <span className="ml-2 text-xs">
                            (Raw: {item.raw_score.toFixed(2)})
                          </span>
                        )}
                      </div>
                      {item.doctrine_flags && item.doctrine_flags.length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-1">
                          {item.doctrine_flags.slice(0, 2).map((flag, i) => (
                            <span
                              key={i}
                              className="text-xs px-2 py-0.5 bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200 rounded"
                              title={flag}
                            >
                              ⚠️ {flag}
                            </span>
                          ))}
                          {item.doctrine_flags.length > 2 && (
                            <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300 rounded">
                              +{item.doctrine_flags.length - 2}
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                    <div className="text-lg font-bold text-green-600 dark:text-green-400 ml-2">
                      #{index + 1}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Short Predictions */}
        <div>
          <h4 className="text-md font-medium text-red-600 dark:text-red-400 mb-3">
            Top 5 Short
          </h4>
          {shortLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <SkeletonRow key={i} />
              ))}
            </div>
          ) : shortError ? (
            <ErrorMessage message={`載入失敗: ${shortErrorDetail instanceof Error ? shortErrorDetail.message : '未知錯誤'}`} />
          ) : !shortPredictions || shortPredictions.length === 0 ? (
            <div className="text-gray-500 dark:text-gray-400 text-sm py-4">
              暫無資料
            </div>
          ) : (
            <div className="space-y-2">
              {shortPredictions.map((item, index) => {
                // Handle doctrine_flags which can be string[] or DoctrineFlag[]
                const flags = Array.isArray(item.doctrine_flags) 
                  ? item.doctrine_flags.map(f => typeof f === 'string' ? f : (f as any).type || String(f))
                  : [];
                
                return (
                  <div
                    key={item.symbol}
                    className="p-3 border border-gray-200 dark:border-gray-700 rounded cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                    onClick={() => handleClick(item.symbol, item)}
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="font-semibold text-gray-900 dark:text-white">
                          {item.symbol} - {item.name}
                        </div>
                        <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                          Final: <span className="font-medium">{item.final_score.toFixed(2)}</span>
                          {item.raw_score !== undefined && (
                            <span className="ml-2 text-xs">
                              (Raw: {item.raw_score.toFixed(2)})
                            </span>
                          )}
                        </div>
                        {flags.length > 0 && (
                          <div className="mt-2 flex flex-wrap gap-1">
                            {flags.slice(0, 2).map((flag, i) => (
                              <span
                                key={i}
                                className="text-xs px-2 py-0.5 bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200 rounded"
                                title={String(flag)}
                              >
                                ⚠️ {String(flag)}
                              </span>
                            ))}
                            {flags.length > 2 && (
                              <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300 rounded">
                                +{flags.length - 2}
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                      <div className="text-lg font-bold text-red-600 dark:text-red-400 ml-2">
                        #{index + 1}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
