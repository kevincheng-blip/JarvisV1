/**
 * useStrategyPerf Hook
 * 
 * React Query hooks for Strategy Performance Feed API.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";

interface StrategyPerformanceSnapshot {
  snapshot_id: string;
  created_at: string;
  symbol: string;
  limit: number;
  window: number;
  items: Array<{
    strategy_id: string;
    n_points: number;
    avg_return_proxy: number;
    sharpe_proxy: number;
    max_drawdown_proxy: number;
    turnover_proxy: number;
    decay_slope: number;
    grade: "NO_DATA" | "GOOD" | "WATCH" | "BAD";
  }>;
}

/**
 * Fetch latest strategy performance snapshot for a symbol
 */
export function useStrategyPerfLatest(
  symbol: string | null,
  enabled: boolean = true
) {
  return useQuery<StrategyPerformanceSnapshot>({
    queryKey: ["strategyPerfLatest", symbol],
    queryFn: async () => {
      if (!symbol) throw new Error("Symbol is required");
      return await api.getStrategyPerfLatest(symbol);
    },
    enabled: enabled && !!symbol,
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
  });
}

/**
 * Mutation: Recompute strategy performance
 */
export function useRecomputeStrategyPerf() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({
      symbol,
      limit = 60,
      window = 20,
    }: {
      symbol: string;
      limit?: number;
      window?: number;
    }) => {
      return await api.recomputeStrategyPerf(symbol, limit, window);
    },
    onSuccess: (_, { symbol }) => {
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: ["strategyPerfLatest", symbol] });
      queryClient.invalidateQueries({ queryKey: ["sRankV2Recommendation", symbol] });
    },
  });
}

