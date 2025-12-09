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

  // Convert sentiment score (-1 to 1) to percentage (0 to 100)
  const sentimentPercent = ((sentiment.sentiment_score + 1) / 2) * 100;
  const sentimentAngle = (sentimentPercent / 100) * 180 - 90; // -90 to 90 degrees

  const getSentimentColor = () => {
    if (sentiment.sentiment_score >= 0.5) return 'text-green-600 dark:text-green-400';
    if (sentiment.sentiment_score >= 0) return 'text-yellow-600 dark:text-yellow-400';
    if (sentiment.sentiment_score >= -0.5) return 'text-orange-600 dark:text-orange-400';
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

        {/* Sentiment Score */}
        <div className={`text-3xl font-bold mb-2 ${getSentimentColor()}`}>
          {sentiment.sentiment_score >= 0 ? '+' : ''}
          {sentiment.sentiment_score.toFixed(2)}
        </div>

        {/* Trend Direction */}
        <div className="text-sm text-gray-600 dark:text-gray-400 mb-4">
          {sentiment.trend_direction === 'bullish' && '📈 看漲'}
          {sentiment.trend_direction === 'bearish' && '📉 看跌'}
          {sentiment.trend_direction === 'neutral' && '➡️ 中性'}
        </div>

        {/* Breakdown */}
        <div className="grid grid-cols-3 gap-4 text-center text-xs">
          <div>
            <div className="text-green-600 dark:text-green-400 font-semibold">
              {sentiment.bullish_count}
            </div>
            <div className="text-gray-500 dark:text-gray-500">看漲</div>
          </div>
          <div>
            <div className="text-gray-600 dark:text-gray-400 font-semibold">
              {sentiment.neutral_count}
            </div>
            <div className="text-gray-500 dark:text-gray-500">中性</div>
          </div>
          <div>
            <div className="text-red-600 dark:text-red-400 font-semibold">
              {sentiment.bearish_count}
            </div>
            <div className="text-gray-500 dark:text-gray-500">看跌</div>
          </div>
        </div>
      </div>
    </div>
  );
}

