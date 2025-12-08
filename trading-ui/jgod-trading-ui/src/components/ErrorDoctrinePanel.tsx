/**
 * ErrorDoctrinePanel Component
 * 
 * 顯示錯誤回放與 Doctrine 聖經建議的工具型 Widget
 * 
 * 功能：
 * - 快速瀏覽最近的錯誤事件
 * - 在表格中看到每一筆錯誤對應的 DoctrineHit（聖經段落）
 * - 點選錯誤顯示詳細內容 + Doctrine 建議列表
 */

import { useState, useMemo } from 'react';
import { useErrorReview } from '../hooks/useErrorReview';
import type { ErrorReviewItem } from '../types/errorReview';

export function ErrorDoctrinePanel() {
  const [selectedErrorId, setSelectedErrorId] = useState<string | null>(null);
  const [dateRange, setDateRange] = useState<'7' | '30' | '90' | 'all'>('30');
  const [symbolFilter, setSymbolFilter] = useState<string>('');

  // Calculate date range
  const { startDate, endDate } = useMemo(() => {
    if (dateRange === 'all') {
      return { startDate: undefined, endDate: undefined };
    }
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - parseInt(dateRange));
    return {
      startDate: start.toISOString().split('T')[0],
      endDate: end.toISOString().split('T')[0],
    };
  }, [dateRange]);

  // Fetch error reviews
  const { data: errorReviews, isLoading, isError, error, refetch } = useErrorReview({
    startDate,
    endDate,
    symbol: symbolFilter || undefined,
    limit: 100,
  });

  // Filter by symbol if needed
  const filteredReviews = useMemo(() => {
    if (!errorReviews) return [];
    if (!symbolFilter) return errorReviews;
    return errorReviews.filter((r) => 
      r.symbol.toLowerCase().includes(symbolFilter.toLowerCase())
    );
  }, [errorReviews, symbolFilter]);

  // Get selected error details
  const selectedError = useMemo(() => {
    if (!selectedErrorId || !errorReviews) return null;
    return errorReviews.find((r) => r.id === selectedErrorId) || null;
  }, [selectedErrorId, errorReviews]);

  // Format timestamp
  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleString('zh-TW', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return timestamp;
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
          錯誤回放 & Doctrine 建議
        </h2>
        <button
          onClick={() => refetch()}
          disabled={isLoading}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
        >
          {isLoading ? '載入中...' : '重新載入'}
        </button>
      </div>

      {/* Filters */}
      <div className="mb-4 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            時間範圍
          </label>
          <select
            value={dateRange}
            onChange={(e) => setDateRange(e.target.value as '7' | '30' | '90' | 'all')}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
          >
            <option value="7">最近 7 天</option>
            <option value="30">最近 30 天</option>
            <option value="90">最近 90 天</option>
            <option value="all">全部</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            股票代號
          </label>
          <input
            type="text"
            value={symbolFilter}
            onChange={(e) => setSymbolFilter(e.target.value)}
            placeholder="例如: 2330"
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
          />
        </div>
        <div className="flex items-end">
          <div className="text-sm text-gray-600 dark:text-gray-400">
            共 {filteredReviews?.length || 0} 筆錯誤
          </div>
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="text-center py-8 text-gray-500 dark:text-gray-400">
          載入錯誤回放中...
        </div>
      )}

      {/* Error State */}
      {isError && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md p-4 text-red-700 dark:text-red-400">
          <p>無法載入錯誤資料：{error instanceof Error ? error.message : '未知錯誤'}</p>
          <button
            onClick={() => refetch()}
            className="mt-2 px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
          >
            重試
          </button>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !isError && (!filteredReviews || filteredReviews.length === 0) && (
        <div className="text-center py-8 text-gray-500 dark:text-gray-400">
          目前沒有任何錯誤分析紀錄
        </div>
      )}

      {/* Main Content */}
      {!isLoading && !isError && filteredReviews && filteredReviews.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-[40%_60%] gap-6">
          {/* Left: Error List Table */}
          <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
            <div className="bg-gray-50 dark:bg-gray-900 px-4 py-2 border-b border-gray-200 dark:border-gray-700">
              <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
                錯誤列表
              </h3>
            </div>
            <div className="overflow-x-auto max-h-[600px] overflow-y-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 dark:bg-gray-900 sticky top-0">
                  <tr>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                      時間
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                      代號
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                      錯誤類型
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                      PnL
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                      Doctrine
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                  {filteredReviews.map((review) => (
                    <tr
                      key={review.id}
                      onClick={() => setSelectedErrorId(review.id === selectedErrorId ? null : review.id)}
                      className={`cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 ${
                        selectedErrorId === review.id
                          ? 'bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-500'
                          : ''
                      }`}
                    >
                      <td className="px-3 py-2 text-gray-900 dark:text-white text-xs">
                        {formatTimestamp(review.timestamp)}
                      </td>
                      <td className="px-3 py-2 text-gray-900 dark:text-white font-mono">
                        {review.symbol}
                      </td>
                      <td className="px-3 py-2 text-gray-900 dark:text-white">
                        {review.error_type || '-'}
                      </td>
                      <td className={`px-3 py-2 font-semibold ${
                        review.pnl_impact !== null && review.pnl_impact < 0
                          ? 'text-red-600 dark:text-red-400'
                          : review.pnl_impact !== null && review.pnl_impact > 0
                          ? 'text-green-600 dark:text-green-400'
                          : 'text-gray-600 dark:text-gray-400'
                      }`}>
                        {review.pnl_impact !== null
                          ? `${review.pnl_impact >= 0 ? '+' : ''}${review.pnl_impact.toFixed(2)}`
                          : '-'}
                      </td>
                      <td className="px-3 py-2">
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200">
                          {review.doctrine_hits.length} hits
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Right: Error Details + Doctrine Suggestions */}
          <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
            <div className="bg-gray-50 dark:bg-gray-900 px-4 py-2 border-b border-gray-200 dark:border-gray-700">
              <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
                錯誤詳情 & Doctrine 建議
              </h3>
            </div>
            <div className="p-4 max-h-[600px] overflow-y-auto">
              {!selectedError ? (
                <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                  請先選擇一筆錯誤
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Error Summary */}
                  <div>
                    <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">
                      錯誤摘要
                    </h4>
                    <div className="bg-gray-50 dark:bg-gray-900 rounded-md p-3 space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600 dark:text-gray-400">股票代號:</span>
                        <span className="font-mono text-gray-900 dark:text-white">{selectedError.symbol}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600 dark:text-gray-400">錯誤類型:</span>
                        <span className="text-gray-900 dark:text-white">{selectedError.error_type || '未知'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600 dark:text-gray-400">時間:</span>
                        <span className="text-gray-900 dark:text-white">{formatTimestamp(selectedError.timestamp)}</span>
                      </div>
                      {selectedError.pnl_impact !== null && (
                        <div className="flex justify-between">
                          <span className="text-gray-600 dark:text-gray-400">損益影響:</span>
                          <span className={`font-semibold ${
                            selectedError.pnl_impact < 0
                              ? 'text-red-600 dark:text-red-400'
                              : 'text-green-600 dark:text-green-400'
                          }`}>
                            {selectedError.pnl_impact >= 0 ? '+' : ''}{selectedError.pnl_impact.toFixed(2)}
                          </span>
                        </div>
                      )}
                      <div className="flex justify-between">
                        <span className="text-gray-600 dark:text-gray-400">分類:</span>
                        <span className="text-gray-900 dark:text-white">{selectedError.classification}</span>
                      </div>
                      {selectedError.human_summary && (
                        <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-700">
                          <p className="text-gray-900 dark:text-white">{selectedError.human_summary}</p>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Doctrine Suggestions */}
                  {selectedError.doctrine_hits.length > 0 ? (
                    <div>
                      <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">
                        Doctrine 聖經建議 ({selectedError.doctrine_hits.length} 筆)
                      </h4>
                      <div className="space-y-4">
                        {selectedError.doctrine_hits.map((hit, idx) => (
                          <div
                            key={`${hit.book_id}-${hit.section_id}-${idx}`}
                            className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-md p-4"
                          >
                            <div className="mb-2">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="text-xs font-mono text-blue-800 dark:text-blue-200">
                                  {hit.book_id}
                                </span>
                                <span className="text-xs text-gray-500 dark:text-gray-400">/</span>
                                <span className="text-xs font-mono text-blue-800 dark:text-blue-200">
                                  {hit.section_id}
                                </span>
                              </div>
                              {hit.summary && (
                                <p className="text-sm text-gray-900 dark:text-white mt-2">
                                  {hit.summary}
                                </p>
                              )}
                            </div>

                            {hit.core_principles && hit.core_principles.length > 0 && (
                              <div className="mt-3">
                                <h5 className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                                  核心原則:
                                </h5>
                                <ul className="list-disc list-inside space-y-1 text-xs text-gray-700 dark:text-gray-300">
                                  {hit.core_principles.slice(0, 3).map((principle, pIdx) => (
                                    <li key={pIdx}>{principle}</li>
                                  ))}
                                </ul>
                              </div>
                            )}

                            {hit.risk_rules && hit.risk_rules.length > 0 && (
                              <div className="mt-3">
                                <h5 className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                                  風控規則:
                                </h5>
                                <ul className="list-disc list-inside space-y-1 text-xs text-gray-700 dark:text-gray-300">
                                  {hit.risk_rules.slice(0, 3).map((rule, rIdx) => (
                                    <li key={rIdx}>{rule}</li>
                                  ))}
                                </ul>
                              </div>
                            )}

                            {hit.tags && hit.tags.length > 0 && (
                              <div className="mt-3 flex flex-wrap gap-1">
                                {hit.tags.slice(0, 5).map((tag, tIdx) => (
                                  <span
                                    key={tIdx}
                                    className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300"
                                  >
                                    {tag}
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-4 text-gray-500 dark:text-gray-400 text-sm">
                      此錯誤沒有對應的 Doctrine 建議
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

