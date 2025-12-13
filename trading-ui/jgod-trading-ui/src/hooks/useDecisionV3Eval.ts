/**
 * React Query hooks for Decision V3 Evaluation
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";

export function useDecisionV3EvalLatest(symbol: string) {
  return useQuery({
    queryKey: ["decisionV3Eval", "latest", symbol],
    queryFn: () => api.getDecisionV3EvalLatest(symbol),
    enabled: !!symbol,
    staleTime: 30 * 1000, // 30 seconds
  });
}

export function useRecomputeDecisionV3Eval(symbol: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (options?: {
      mode?: string;
      limit?: number;
      k?: number;
      window?: number;
    }) => api.recomputeDecisionV3Eval(symbol, options || {}),
    onSuccess: () => {
      // Invalidate and refetch
      queryClient.invalidateQueries({ queryKey: ["decisionV3Eval", "latest", symbol] });
      queryClient.invalidateQueries({ queryKey: ["decisionV3Eval", "list", symbol] });
    },
  });
}

export function useDecisionV3EvalList(symbol: string, n: number = 20) {
  return useQuery({
    queryKey: ["decisionV3Eval", "list", symbol, n],
    queryFn: () => api.listDecisionV3Evals(symbol, n),
    enabled: !!symbol,
    staleTime: 60 * 1000, // 1 minute
  });
}

