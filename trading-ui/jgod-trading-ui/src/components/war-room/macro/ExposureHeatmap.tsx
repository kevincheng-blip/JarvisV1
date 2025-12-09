/**
 * ExposureHeatmap Component
 * 
 * Macro Layer - Exposure Heatmap
 * 
 * 顯示市場曝險熱圖
 */

import { useExposureHeatmap } from '../../../hooks/war-room/useRisk';
import { useWarRoomStore } from '../../../store/warRoomStore';

export function ExposureHeatmap() {
  const { data: exposureResponse, isLoading, isError, error } = useExposureHeatmap();
  const { selectedRunId } = useWarRoomStore();

  // Color mapping based on exposure
  const getHeatColor = (exposure: number) => {
    const absExposure = Math.abs(exposure);
    if (absExposure >= 0.1) return 'bg-red-500';
    if (absExposure >= 0.05) return 'bg-orange-500';
    if (absExposure >= 0.02) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  if (isLoading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          市場曝險熱圖
        </h3>
        <div className="grid grid-cols-5 gap-2">
          {Array.from({ length: 20 }).map((_, i) => (
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
          市場曝險熱圖
        </h3>
        <div className="text-red-500 dark:text-red-400">
          錯誤: {error instanceof Error ? error.message : '未知錯誤'}
        </div>
      </div>
    );
  }

  if (!exposureResponse || !exposureResponse.buckets || exposureResponse.buckets.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          市場曝險熱圖
        </h3>
        <div className="text-gray-500 dark:text-gray-400 text-center py-8">
          目前沒有曝險資料
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        市場曝險熱圖
        {selectedRunId && (
          <span className="ml-2 text-sm text-gray-500 dark:text-gray-400">
            ({selectedRunId.substring(0, 8)}...)
          </span>
        )}
      </h3>
      <div className="grid grid-cols-5 gap-2">
        {exposureResponse.buckets.slice(0, 30).map((bucket, idx) => (
          <div
            key={idx}
            className={`${getHeatColor(bucket.exposure)} rounded p-2 text-white text-center cursor-pointer hover:opacity-80 transition-opacity`}
            title={`${bucket.bucket}: ${(bucket.exposure * 100).toFixed(2)}%`}
          >
            <div className="text-xs font-semibold">{bucket.bucket}</div>
            <div className="text-xs">
              {(bucket.exposure * 100).toFixed(1)}%
            </div>
          </div>
        ))}
      </div>
      <div className="mt-4 flex items-center gap-4 text-xs text-gray-600 dark:text-gray-400">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-green-500 rounded"></div>
          <span>&lt; 2%</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-yellow-500 rounded"></div>
          <span>2-5%</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-orange-500 rounded"></div>
          <span>5-10%</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-red-500 rounded"></div>
          <span>&gt; 10%</span>
        </div>
      </div>
    </div>
  );
}

