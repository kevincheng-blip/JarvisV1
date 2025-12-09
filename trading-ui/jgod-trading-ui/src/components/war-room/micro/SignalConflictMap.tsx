/**
 * SignalConflictMap Component
 * 
 * Micro Layer - Signal Conflict Map
 * 
 * 顯示策略共識地圖：散點圖展示每檔股票的 Consensus vs Conflict 分數
 */

import { useSignalConflicts } from "../../../hooks/useSignalConflicts";
import { useWarRoomStore } from "../../../store/warRoomStore";
import { StrategyRadarMini } from "./StrategyRadarMini";
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  Cell,
} from "recharts";
import type { SignalConflictItem } from "../../../types/signalConflict";

interface ScatterDataPoint {
  x: number;  // conflict_score
  y: number;  // consensus_score
  symbol: string;
  name: string;
  majority_vote: 1 | -1 | 0;
  final_score?: number | null;
  raw_score?: number | null;
  strategy_votes: Record<string, -1 | 0 | 1>;
}

export function SignalConflictMap() {
  const { selectedSymbol, setSelectedSymbol, dateRange } = useWarRoomStore();
  const { data: conflicts, isLoading, isError, error, refetch } = useSignalConflicts(
    dateRange.end,
    100,
    "all"
  );

  // Loading state
  if (isLoading) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          策略共識地圖 (Signal Conflict Map)
        </h3>
        <div className="text-gray-500 dark:text-gray-400 text-center py-8 text-sm">
          載入策略共識資料中…
        </div>
      </div>
    );
  }

  // Error state
  if (isError) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          策略共識地圖 (Signal Conflict Map)
        </h3>
        <div className="text-red-500 dark:text-red-400 text-center py-8">
          <div className="mb-4">無法取得策略共識資料</div>
          <div className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            {error instanceof Error ? error.message : "未知錯誤"}
          </div>
          <button
            onClick={() => refetch()}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm"
          >
            重試
          </button>
        </div>
      </div>
    );
  }

  // Empty state
  if (!conflicts || conflicts.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          策略共識地圖 (Signal Conflict Map)
        </h3>
        <div className="text-gray-500 dark:text-gray-400 text-center py-8 text-sm">
          目前尚無可用的策略共識資料，請先執行 Prediction + Decision Pipeline。
        </div>
      </div>
    );
  }

  // Prepare scatter chart data
  const scatterData: ScatterDataPoint[] = conflicts.map((item) => ({
    x: item.conflict_score,
    y: item.consensus_score,
    symbol: item.symbol,
    name: item.name,
    majority_vote: item.majority_vote,
    final_score: item.final_score,
    raw_score: item.raw_score,
    strategy_votes: item.strategy_votes,
  }));

  // Get selected conflict item
  const selectedConflict = conflicts.find((c) => c.symbol === selectedSymbol);

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload || !payload[0]) return null;

    const data = payload[0].payload as ScatterDataPoint;
    const longCount = Object.values(data.strategy_votes).filter((v) => v === 1).length;
    const shortCount = Object.values(data.strategy_votes).filter((v) => v === -1).length;
    const neutralCount = Object.values(data.strategy_votes).filter((v) => v === 0).length;

    return (
      <div className="bg-gray-900 text-white p-3 rounded-lg shadow-lg text-xs">
        <div className="font-semibold mb-2">{data.symbol} - {data.name}</div>
        <div className="space-y-1">
          <div>Consensus: {data.y.toFixed(1)}</div>
          <div>Conflict: {data.x.toFixed(1)}</div>
          <div>
            Majority:{" "}
            {data.majority_vote === 1
              ? "Long"
              : data.majority_vote === -1
              ? "Short"
              : "Neutral"}
          </div>
          {data.final_score !== null && data.final_score !== undefined && (
            <div>Final Score: {data.final_score.toFixed(2)}</div>
          )}
          <div className="mt-2 pt-2 border-t border-gray-700">
            {longCount} 多 {shortCount} 空 {neutralCount} 中性
          </div>
        </div>
      </div>
    );
  };

  // Get color based on majority vote
  const getPointColor = (majority_vote: 1 | -1 | 0) => {
    if (majority_vote === 1) return "#10b981"; // green
    if (majority_vote === -1) return "#ef4444"; // red
    return "#6b7280"; // gray
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        策略共識地圖 (Signal Conflict Map)
      </h3>

      {/* Scatter Chart */}
      <div className="mb-4">
        <ResponsiveContainer width="100%" height={400}>
          <ScatterChart
            margin={{ top: 20, right: 20, bottom: 60, left: 60 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              type="number"
              dataKey="x"
              name="Conflict Score"
              label={{ value: "Conflict Score", position: "insideBottom", offset: -5 }}
              domain={[0, 100]}
              stroke="#6b7280"
              fontSize={12}
            />
            <YAxis
              type="number"
              dataKey="y"
              name="Consensus Score"
              label={{ value: "Consensus Score", angle: -90, position: "insideLeft" }}
              domain={[0, 100]}
              stroke="#6b7280"
              fontSize={12}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            {/* Reference lines for quadrants */}
            <ReferenceLine
              x={50}
              stroke="#9ca3af"
              strokeDasharray="3 3"
              strokeWidth={1}
            />
            <ReferenceLine
              y={50}
              stroke="#9ca3af"
              strokeDasharray="3 3"
              strokeWidth={1}
            />
            <Scatter
              name="Stocks"
              data={scatterData}
              onClick={(data: any) => {
                if (data && data.payload) {
                  setSelectedSymbol(data.payload.symbol);
                }
              }}
              cursor="pointer"
            >
              {scatterData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={getPointColor(entry.majority_vote)}
                  opacity={entry.symbol === selectedSymbol ? 1.0 : 0.6}
                  stroke={entry.symbol === selectedSymbol ? "#3b82f6" : "none"}
                  strokeWidth={entry.symbol === selectedSymbol ? 3 : 0}
                />
              ))}
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>

        {/* Quadrant Labels */}
        <div className="grid grid-cols-2 gap-2 mt-2 text-xs text-gray-600 dark:text-gray-400">
          <div className="text-left">
            <div className="font-semibold">左上：行動區</div>
            <div className="text-xs">高共識 / 低衝突</div>
          </div>
          <div className="text-right">
            <div className="font-semibold">右上：異常區</div>
            <div className="text-xs">高共識 / 高衝突（罕見）</div>
          </div>
          <div className="text-left">
            <div className="font-semibold">左下：觀望區</div>
            <div className="text-xs">低共識 / 低衝突</div>
          </div>
          <div className="text-right">
            <div className="font-semibold">右下：危險區</div>
            <div className="text-xs">低共識 / 高衝突</div>
          </div>
        </div>

        {/* Legend */}
        <div className="flex justify-center gap-4 mt-2 text-xs">
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-full bg-green-500" />
            <span>多頭 (Long)</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-full bg-red-500" />
            <span>空頭 (Short)</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-full bg-gray-500" />
            <span>中性 (Neutral)</span>
          </div>
        </div>
      </div>

      {/* Strategy Radar Mini for selected symbol */}
      <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
        {selectedConflict ? (
          <>
            {selectedConflict.conflict_score >= 70 && (
              <div className="mb-2">
                <span className="px-2 py-1 bg-red-500 text-white text-xs rounded font-semibold">
                  策略分歧嚴重
                </span>
              </div>
            )}
            <StrategyRadarMini strategyVotes={selectedConflict.strategy_votes} />
          </>
        ) : (
          <div className="text-center text-gray-500 dark:text-gray-400 text-sm py-4">
            點擊上方散點圖中的股票以查看策略分佈。
          </div>
        )}
      </div>
    </div>
  );
}
