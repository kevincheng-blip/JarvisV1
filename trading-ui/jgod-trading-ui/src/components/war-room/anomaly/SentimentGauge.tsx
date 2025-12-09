/**
 * SentimentGauge Component
 * 
 * Anomaly Layer - Sentiment Gauge
 * 
 * 顯示市場情緒指標
 */

import { useMarketSentiment } from '../../../hooks/war-room/useSentiment';

export function SentimentGauge() {
  const { data: sentiment, isLoading, isError, error } = useMarketSentiment();

  if (isLoading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          市場情緒
        </h3>
        <div className="flex items-center justify-center h-32">
          <div className="text-gray-500 dark:text-gray-400">載入中...</div>
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          市場情緒
        </h3>
        <div className="text-red-500 text-sm">
          錯誤: {error instanceof Error ? error.message : '未知錯誤'}
        </div>
      </div>
    );
  }

  if (!sentiment) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          市場情緒
        </h3>
        <div className="text-gray-500 dark:text-gray-400 text-center py-8 text-sm">
          目前沒有情緒資料
        </div>
      </div>
    );
  }

  // Convert index_value (0~100) to angle (-90 to 90 degrees)
  const sentimentAngle = (sentiment.index_value / 100) * 180 - 90;

  const getSentimentColor = () => {
    if (sentiment.index_value >= 70) return 'text-green-600 dark:text-green-400';
    if (sentiment.index_value >= 40) return 'text-yellow-600 dark:text-yellow-400';
    if (sentiment.index_value >= 20) return 'text-orange-600 dark:text-orange-400';
    return 'text-red-600 dark:text-red-400';
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        市場情緒
      </h3>
      <div className="flex flex-col items-center">
        {/* Gauge Visualization (Simplified) */}
        <div className="relative w-48 h-24 mb-4">
          {/* Gauge Background */}
          <svg viewBox="0 0 200 100" className="w-full h-full">
            {/* Gauge Arc */}
            <path
              d="M 20 80 A 80 80 0 0 1 180 80"
              stroke="#374151"
              strokeWidth="12"
              fill="none"
              strokeLinecap="round"
            />
            {/* Sentiment Indicator */}
            <path
              d="M 20 80 A 80 80 0 0 1 180 80"
              stroke={
                sentiment.sentiment_score >= 0.5
                  ? '#10b981'
                  : sentiment.sentiment_score >= 0
                  ? '#f59e0b'
                  : '#ef4444'
              }
              strokeWidth="12"
              fill="none"
              strokeLinecap="round"
              strokeDasharray={`${(sentimentPercent / 100) * 502.4} 502.4`}
              transform="rotate(180 100 80)"
            />
          </svg>
          {/* Needle */}
          <div
            className="absolute bottom-0 left-1/2 transform -translate-x-1/2 origin-bottom"
            style={{
              transform: `translateX(-50%) rotate(${sentimentAngle}deg)`,
              transformOrigin: 'bottom center',
            }}
          >
            <div className="w-1 h-16 bg-gray-900 dark:bg-white rounded-full"></div>
          </div>
        </div>

          {/* Sentiment Index */}
          <div className={`text-3xl font-bold mb-2 ${getSentimentColor()}`}>
            {sentiment.index_value}
          </div>

          {/* Label */}
          <div className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            {sentiment.label}
          </div>

          {/* Sources */}
          {sentiment.sources && sentiment.sources.length > 0 && (
            <div className="text-xs text-gray-500 dark:text-gray-500">
              來源: {sentiment.sources.join(', ')}
            </div>
          )}
      </div>
    </div>
  );
}

