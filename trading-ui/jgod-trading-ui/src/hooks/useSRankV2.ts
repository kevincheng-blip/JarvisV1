/**
 * useSRankV2 Hook
 * 
 * React Query hooks for S-Rank Engine V2 recommendation API.
 */

import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";

interface SRankV2Recommendation {
  symbol: string;
  start_date: string | null;
  end_date: string | null;
  metrics: {
    n_points: number;
    score_std: number;
    max_abs_delta: number;
    trend_slope: number;
    stability_grade: "NO_DATA" | "STABLE" | "WATCH" | "VOLATILE";
  };
  items: Array<{
    strategy: string;
    weight: number;
    score: number;
  }>;
  weights: Record<string, number>;
  rationale: Record<string, string>;
}

/**
 * Fetch S-Rank V2 recommendation for a symbol
 */
export function useSRankV2Recommendation(
  symbol: string | null,
  limit: number = 60,
  k: number = 5,
  mode: "signals" | "performance" = "performance",
  enabled: boolean = true
) {
  return useQuery<SRankV2Recommendation>({
    queryKey: ["sRankV2Recommendation", symbol, limit, k, mode],
    queryFn: async () => {
      if (!symbol) throw new Error("Symbol is required");
      return await api.getSRankV2Recommendation(symbol, limit, k, mode);
    },
    enabled: enabled && !!symbol,
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
  });
}

