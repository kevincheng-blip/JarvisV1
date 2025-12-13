/**
 * React Query hooks for Decision V3 Compare
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";

export function useDecisionV3CompareLatest(symbol: string) {
  return useQuery({
    queryKey: ["decisionV3Compare", "latest", symbol],
    queryFn: () => api.getDecisionV3CompareLatest(symbol),
    enabled: !!symbol,
    staleTime: 30 * 1000, // 30 seconds
  });
}

export function useRecomputeDecisionV3Compare(symbol: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (options?: {
      mode?: string;
      limit?: number;
      k?: number;
      window?: number;
    }) => api.recomputeDecisionV3Compare(symbol, options || {}),
    onSuccess: () => {
      // Invalidate and refetch
      queryClient.invalidateQueries({ queryKey: ["decisionV3Compare", "latest", symbol] });
      queryClient.invalidateQueries({ queryKey: ["decisionV3Compare", "list", symbol] });
    },
  });
}

export function useDecisionV3CompareList(symbol: string, n: number = 20) {
  return useQuery({
    queryKey: ["decisionV3Compare", "list", symbol, n],
    queryFn: () => api.listDecisionV3Compares(symbol, n),
    enabled: !!symbol,
    staleTime: 60 * 1000, // 1 minute
  });
}

