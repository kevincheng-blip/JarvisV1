/**
 * ErrorReplayPanel Component
 * 
 * Anomaly Layer - Error Replay Panel
 * 
 * 錯誤回放面板（預留 SPEC）
 * 左側：錯誤清單（已完成）
 * 右側：Replay Viewer（目前先做 Placeholder）
 * 
 * 準備接：
 * - K 線
 * - 因子走勢
 * - Raw Score / Strategy Score / Final Score
 * - 買賣行為還原
 */

import { useErrorReview } from '../../../hooks/useErrorReview';
import { useWarRoomStore } from '../../../store/warRoomStore';

export function ErrorReplayPanel() {
  const { dateRange, selectedErrorId, setSelectedErrorId } = useWarRoomStore();
  const { data: errorReviews, isLoading, isError, error } = useErrorReview({
    startDate: dateRange.start,
    endDate: dateRange.end,
    limit: 50,
  });

  const selectedError = errorReviews?.find((e) => e.id === selectedErrorId);

  if (isLoading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          錯誤回放
        </h3>
        <div className="text-gray-500 dark:text-gray-400 text-center py-8">
          載入中...
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          錯誤回放
        </h3>
        <div className="text-red-500">
          錯誤: {error instanceof Error ? error.message : '未知錯誤'}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        錯誤回放
      </h3>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Left: Error List */}
        <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
          <div className="bg-gray-50 dark:bg-gray-900 px-4 py-2 border-b border-gray-200 dark:border-gray-700">
            <h4 className="text-sm font-semibold text-gray-900 dark:text-white">
              錯誤列表
            </h4>
          </div>
          <div className="max-h-64 overflow-y-auto">
            {!errorReviews || errorReviews.length === 0 ? (
              <div className="p-4 text-center text-gray-500 dark:text-gray-400 text-sm">
                目前沒有錯誤記錄
              </div>
            ) : (
              <div className="divide-y divide-gray-200 dark:divide-gray-700">
                {errorReviews.map((err) => (
                  <div
                    key={err.id}
                    onClick={() => setSelectedErrorId(err.id)}
                    className={`p-3 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors ${
                      selectedErrorId === err.id
                        ? 'bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-500'
                        : ''
                    }`}
                  >
                    <div className="text-sm font-mono text-gray-900 dark:text-white">
                      {err.symbol}
                    </div>
                    <div className="text-xs text-gray-600 dark:text-gray-400">
                      {err.error_type || '未知錯誤'}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-500">
                      {new Date(err.timestamp).toLocaleDateString('zh-TW')}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right: Replay Viewer (Placeholder) */}
        <div className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
          <div className="bg-gray-50 dark:bg-gray-900 px-4 py-2 border-b border-gray-200 dark:border-gray-700">
            <h4 className="text-sm font-semibold text-gray-900 dark:text-white">
              Replay Viewer
            </h4>
          </div>
          <div className="p-4 h-64 flex items-center justify-center">
            {!selectedError ? (
              <div className="text-gray-500 dark:text-gray-400 text-sm text-center">
                請先在錯誤列表中選擇一筆錯誤，才能啟動回放。
              </div>
            ) : (
              <div className="text-gray-500 dark:text-gray-400 text-sm text-center">
                <div className="mb-2">準備顯示：</div>
                <ul className="text-left text-xs space-y-1">
                  <li>• K 線圖</li>
                  <li>• 因子走勢</li>
                  <li>• Raw/Strategy/Final Score</li>
                  <li>• 買賣行為還原</li>
                </ul>
                <div className="mt-4 text-xs italic">
                  (Replay Engine v1 規格待撰寫)
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

