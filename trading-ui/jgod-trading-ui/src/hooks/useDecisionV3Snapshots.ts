/**
 * useDecisionV3Snapshots Hook
 * 
 * React Query hooks for Decision V3 snapshot API.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";

interface DecisionV3Snapshot {
  snapshot_id: string;
  created_at: string;
  symbol: string;
  mode: string;
  limit: number;
  k: number;
  result: {
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
  };
}

interface DecisionV3SnapshotList {
  symbol: string;
  items: Array<{
    snapshot_id: string;
    created_at: string;
    symbol: string;
    mode: string;
    primary_strategy: string | null;
    confidence: number;
    risk_state: string;
  }>;
  total: number;
}

/**
 * Fetch latest Decision V3 snapshot for a symbol
 */
export function useDecisionV3Latest(
  symbol: string | null,
  enabled: boolean = true
) {
  return useQuery<DecisionV3Snapshot>({
    queryKey: ["decisionV3Latest", symbol],
    queryFn: async () => {
      if (!symbol) throw new Error("Symbol is required");
      return await api.getDecisionV3Latest(symbol);
    },
    enabled: enabled && !!symbol,
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
  });
}

/**
 * Mutation: Recompute Decision V3
 */
export function useRecomputeDecisionV3() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({
      symbol,
      mode = "performance",
      limit = 60,
      k = 5,
    }: {
      symbol: string;
      mode?: "signals" | "performance";
      limit?: number;
      k?: number;
    }) => {
      return await api.recomputeDecisionV3(symbol, { mode, limit, k });
    },
    onSuccess: (_, { symbol }) => {
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: ["decisionV3Latest", symbol] });
      queryClient.invalidateQueries({ queryKey: ["decisionV3SnapshotList", symbol] });
      queryClient.invalidateQueries({ queryKey: ["decisionV3", symbol] });
    },
  });
}

/**
 * Fetch Decision V3 snapshot list for a symbol
 */
export function useDecisionV3SnapshotList(
  symbol: string | null,
  n: number = 20,
  enabled: boolean = true
) {
  return useQuery<DecisionV3SnapshotList>({
    queryKey: ["decisionV3SnapshotList", symbol, n],
    queryFn: async () => {
      if (!symbol) throw new Error("Symbol is required");
      return await api.listDecisionV3Snapshots(symbol, n);
    },
    enabled: enabled && !!symbol,
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: false,
  });
}

