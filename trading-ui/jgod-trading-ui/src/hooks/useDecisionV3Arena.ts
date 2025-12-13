/**
 * React Query hooks for Decision V3 Arena API
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";

export function useDecisionV3ArenaLatest(symbol: string | null, enabled: boolean = true) {
  return useQuery({
    queryKey: ["decision-v3-arena", "latest", symbol],
    queryFn: () => api.getDecisionV3ArenaLatest(symbol!),
    enabled: enabled && !!symbol,
    staleTime: 30000, // 30 seconds
  });
}

export function useRecomputeDecisionV3Arena(symbol: string | null) {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (options: { mode?: string; limit?: number; k?: number; window?: number } = {}) => {
      if (!symbol) throw new Error("Symbol is required");
      return api.recomputeDecisionV3Arena(symbol, options);
    },
    onSuccess: () => {
      // Invalidate and refetch arena queries
      queryClient.invalidateQueries({ queryKey: ["decision-v3-arena", "latest", symbol] });
      queryClient.invalidateQueries({ queryKey: ["decision-v3-arena", "list", symbol] });
    },
  });
}

export function useDecisionV3ArenaList(symbol: string | null, n: number = 20, enabled: boolean = true) {
  return useQuery({
    queryKey: ["decision-v3-arena", "list", symbol, n],
    queryFn: () => api.listDecisionV3Arena(symbol!, n),
    enabled: enabled && !!symbol,
    staleTime: 30000, // 30 seconds
  });
}

