/**
 * EquityCurve Component
 * 
 * Macro Layer - Equity Curve
 * 
 * 顯示資產淨值曲線圖
 */

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { usePolicyExperimentsHistory } from '../../../hooks/war-room/usePolicy';
import { useWarRoomStore } from '../../../store/warRoomStore';

export function EquityCurve() {
  const { data: experiments, isLoading, isError, error } = usePolicyExperimentsHistory();
  const { selectedRunId } = useWarRoomStore();

  // For now, use placeholder data structure
  // In future, this should come from a dedicated equity curve endpoint
  const equityData = [
    { date: '2024-01-01', equity: 1000000 },
    { date: '2024-02-01', equity: 1020000 },
    { date: '2024-03-01', equity: 1050000 },
    { date: '2024-04-01', equity: 1030000 },
    { date: '2024-05-01', equity: 1070000 },
  ];

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
        <div className="h-64 flex items-center justify-center text-red-500">
          錯誤: {error instanceof Error ? error.message : '未知錯誤'}
        </div>
      </div>
    );
  }

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
        <LineChart data={equityData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis
            dataKey="date"
            stroke="#9ca3af"
            tick={{ fill: '#9ca3af' }}
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
            dot={{ fill: '#3b82f6', r: 4 }}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

