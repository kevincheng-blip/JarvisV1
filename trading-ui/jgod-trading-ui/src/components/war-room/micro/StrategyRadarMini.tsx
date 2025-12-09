/**
 * StrategyRadarMini Component
 * 
 * Mini Radar Chart showing strategy votes distribution
 * 
 * 策略雷達圖：顯示單一股票的各策略投票分佈
 */

import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from "recharts";

export interface StrategyRadarMiniProps {
  strategyVotes: Record<string, -1 | 0 | 1>;
}

export function StrategyRadarMini({ strategyVotes }: StrategyRadarMiniProps) {
  // Convert strategy votes to radar chart data
  // Map: -1 → 0 (strong bearish), 0 → 0.5 (neutral), 1 → 1.0 (strong bullish)
  const radarData = Object.entries(strategyVotes)
    .sort(([a], [b]) => {
      // Sort by strategy ID (S1, S2, ...)
      const aNum = parseInt(a.replace("S", ""));
      const bNum = parseInt(b.replace("S", ""));
      return aNum - bNum;
    })
    .map(([strategyId, vote]) => {
      let value: number;
      if (vote === 1) {
        value = 1.0; // Strong bullish
      } else if (vote === -1) {
        value = 0.0; // Strong bearish
      } else {
        value = 0.5; // Neutral
      }

      return {
        strategy: strategyId,
        value,
        vote, // Keep original vote for reference
      };
    });

  if (radarData.length === 0) {
    return (
      <div className="text-center text-gray-500 dark:text-gray-400 text-sm py-4">
        無策略投票資料
      </div>
    );
  }

  return (
    <div>
      <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
        策略投票分佈
      </h4>
      <ResponsiveContainer width="100%" height={250}>
        <RadarChart data={radarData}>
          <PolarGrid stroke="#e5e7eb" />
          <PolarAngleAxis
            dataKey="strategy"
            tick={{ fontSize: 10, fill: "#6b7280" }}
          />
          <PolarRadiusAxis
            angle={90}
            domain={[0, 1]}
            tick={{ fontSize: 8, fill: "#9ca3af" }}
            tickCount={3}
          />
          <Radar
            name="Strategy Vote"
            dataKey="value"
            stroke="#3b82f6"
            fill="#3b82f6"
            fillOpacity={0.3}
            strokeWidth={2}
          />
        </RadarChart>
      </ResponsiveContainer>
      
      {/* Vote Summary */}
      <div className="flex justify-center gap-4 mt-2 text-xs text-gray-600 dark:text-gray-400">
        <div>
          看多: {Object.values(strategyVotes).filter((v) => v === 1).length}
        </div>
        <div>
          看空: {Object.values(strategyVotes).filter((v) => v === -1).length}
        </div>
        <div>
          中性: {Object.values(strategyVotes).filter((v) => v === 0).length}
        </div>
      </div>
    </div>
  );
}

