/**
 * PolicyHealthV2 Component
 * 
 * Macro Layer - Policy Health Visualization
 * 
 * 顯示 Sharpe Ratio vs Max Drawdown 雲圖
 * 點擊節點可選擇 selectedRunId
 */

import { useMemo } from "react";
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { usePolicyExperimentsHistory } from '../../../hooks/war-room/usePolicy';
import { useWarRoomStore } from '../../../store/warRoomStore';

export function PolicyHealthV2() {
  const { data: experiments, isLoading, isError, error } = usePolicyExperimentsHistory();
  const { selectedRunId, setSelectedRunId } = useWarRoomStore();

  // Transform data for scatter plot
  const scatterData = useMemo(() => {
    if (!experiments) return [];
    return experiments.map((exp) => ({
      runId: exp.run_id,
      sharpe: exp.sharpe_ratio,
      maxDD: Math.abs(exp.max_drawdown) * 100, // Convert to percentage
      totalReturn: exp.total_return * 100,
      score: exp.score,
      date: exp.start_date,
    }));
  }, [experiments]);

  // Color mapping based on score
  const getColor = (score: number) => {
    if (score >= 0.8) return '#10b981'; // green
    if (score >= 0.6) return '#3b82f6'; // blue
    if (score >= 0.4) return '#f59e0b'; // yellow
    return '#ef4444'; // red
  };

  const handlePointClick = (data: any) => {
    setSelectedRunId(data.runId);
  };

  if (isLoading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Policy Health (Sharpe vs MaxDD)
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
          Policy Health (Sharpe vs MaxDD)
        </h3>
        <div className="h-64 flex items-center justify-center text-red-500">
          錯誤: {error instanceof Error ? error.message : '未知錯誤'}
        </div>
      </div>
    );
  }

  if (!experiments || experiments.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Policy Health (Sharpe vs MaxDD)
        </h3>
        <div className="h-64 flex flex-col items-center justify-center text-gray-500 dark:text-gray-400">
          <div className="text-lg font-semibold mb-2">尚未有任何實驗結果</div>
          <div className="text-sm">請先執行 Policy Loop v2，再回到此畫面</div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        Policy Health (Sharpe vs MaxDD)
      </h3>
      <ResponsiveContainer width="100%" height={400}>
        <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis
            type="number"
            dataKey="sharpe"
            name="Sharpe Ratio"
            label={{ value: 'Sharpe Ratio', position: 'insideBottom', offset: -5 }}
            stroke="#9ca3af"
          />
          <YAxis
            type="number"
            dataKey="maxDD"
            name="Max Drawdown (%)"
            label={{ value: 'Max Drawdown (%)', angle: -90, position: 'insideLeft' }}
            stroke="#9ca3af"
          />
          <Tooltip
            cursor={{ strokeDasharray: '3 3' }}
            content={({ active, payload }) => {
              if (active && payload && payload[0]) {
                const data = payload[0].payload;
                return (
                  <div className="bg-gray-900 text-white p-3 rounded-lg shadow-lg">
                    <p className="font-semibold">Run ID: {data.runId.substring(0, 8)}...</p>
                    <p>Sharpe: {data.sharpe.toFixed(4)}</p>
                    <p>MaxDD: {data.maxDD.toFixed(2)}%</p>
                    <p>Return: {data.totalReturn.toFixed(2)}%</p>
                    <p>Score: {data.score.toFixed(4)}</p>
                  </div>
                );
              }
              return null;
            }}
          />
          <Scatter
            name="Experiments"
            data={scatterData}
            fill="#8884d8"
            onClick={handlePointClick}
          >
            {scatterData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={selectedRunId === entry.runId ? '#fbbf24' : getColor(entry.score)}
                stroke={selectedRunId === entry.runId ? '#f59e0b' : undefined}
                strokeWidth={selectedRunId === entry.runId ? 3 : 1}
              />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>
      {selectedRunId && (
        <div className="mt-4 text-sm text-gray-600 dark:text-gray-400">
          已選擇: {selectedRunId.substring(0, 8)}...
        </div>
      )}
    </div>
  );
}

