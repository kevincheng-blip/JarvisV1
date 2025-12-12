/**
 * useDecisionV3 Hook
 * 
 * React Query hooks for Decision V3 API.
 */

import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";

interface DecisionV3Result {
  symbol: string;
  as_of_date: string | null;
  selected_primary_strategy: string | null;
  selected_secondary_strategies: string[];
  weights: Array<{
    strategy_id: string;
    weight: number;
    grade?: string | null;
    metrics?: Record<string, number> | null;
    rationale?: string | null;
  }>;
  risk_plan: {
    position_scale: number;
    risk_state: "RISK_ON" | "RISK_OFF" | "CAUTION";
    reasons: string[];
  };
  confidence: number;
  explain: string;
}

/**
 * Fetch Decision V3 for a symbol
 */
export function useDecisionV3(
  symbol: string | null,
  mode: "signals" | "performance" = "performance",
  limit: number = 60,
  k: number = 5,
  enabled: boolean = true
) {
  return useQuery<DecisionV3Result>({
    queryKey: ["decisionV3", symbol, mode, limit, k],
    queryFn: async () => {
      if (!symbol) throw new Error("Symbol is required");
      return await api.getDecisionV3(symbol, { mode, limit, k });
    },
    enabled: enabled && !!symbol,
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
  });
}

