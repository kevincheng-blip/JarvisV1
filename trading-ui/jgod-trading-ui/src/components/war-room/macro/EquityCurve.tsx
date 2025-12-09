/**
 * EquityCurve Component
 * 
 * Macro Layer - Equity Curve
 * 
 * 顯示資產淨值曲線圖
 */

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { useEquityCurve } from '../../../hooks/war-room/useEquityCurve';
import { useWarRoomStore } from '../../../store/warRoomStore';

export function EquityCurve() {
  const { data: equityData, isLoading, isError, error } = useEquityCurve();
  const { selectedRunId } = useWarRoomStore();

  if (isLoading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          資產淨值曲線
        </h3>
        <div className="h-64 flex items-center justify-center text-gray-500 dark:text-gray-400">
          載入中...
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          資產淨值曲線
        </h3>
        <div className="h-64 flex items-center justify-center text-red-500 dark:text-red-400">
          無法載入淨值曲線，請稍後重試
        </div>
      </div>
    );
  }

  if (!equityData || equityData.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          資產淨值曲線
        </h3>
        <div className="h-64 flex items-center justify-center text-gray-500 dark:text-gray-400">
          目前沒有淨值資料
        </div>
      </div>
    );
  }

  // Sample data if too many points (as per SPEC 13.2)
  const displayData = equityData.length > 100
    ? equityData.filter((_, idx) => idx % Math.ceil(equityData.length / 100) === 0)
    : equityData;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        資產淨值曲線
        {selectedRunId && (
          <span className="ml-2 text-sm text-gray-500 dark:text-gray-400">
            ({selectedRunId.substring(0, 8)}...)
          </span>
        )}
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={displayData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis
            dataKey="date"
            stroke="#9ca3af"
            tick={{ fill: '#9ca3af' }}
            tickFormatter={(value) => value.split('-').slice(1).join('/')}
          />
          <YAxis
            stroke="#9ca3af"
            tick={{ fill: '#9ca3af' }}
            tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1f2937',
              border: '1px solid #374151',
              borderRadius: '0.5rem',
            }}
            labelStyle={{ color: '#f3f4f6' }}
            formatter={(value: number) => [`$${value.toLocaleString()}`, '淨值']}
          />
          <Line
            type="monotone"
            dataKey="equity"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 6 }}
            name="淨值"
          />
          {displayData.some((d) => d.benchmark_equity !== undefined) && (
            <Line
              type="monotone"
              dataKey="benchmark_equity"
              stroke="#10b981"
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={false}
              name="基準"
            />
          )}
          <Legend />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

