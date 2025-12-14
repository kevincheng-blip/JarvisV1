/**
 * React Query hooks for Execution API
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";

/**
 * Hook to fetch latest execution ledger for a symbol
 */
export function useLedgerLatest(symbol: string | null) {
  return useQuery({
    queryKey: ["execution", "ledger", "latest", symbol],
    queryFn: () => api.getExecutionLedgerLatest(symbol!),
    enabled: !!symbol,
    staleTime: 30000, // 30 seconds
  });
}

/**
 * Hook to recompute (reset) execution ledger
 */
export function useRecomputeLedger() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ symbol, initialCash }: { symbol: string; initialCash?: number }) =>
      api.recomputeExecutionLedger(symbol, initialCash),
    onSuccess: (data, variables) => {
      // Invalidate ledger queries for this symbol
      queryClient.invalidateQueries({ queryKey: ["execution", "ledger", "latest", variables.symbol] });
      queryClient.invalidateQueries({ queryKey: ["execution", "order", "simulate", variables.symbol] });
    },
  });
}

/**
 * Hook to simulate order from latest Decision V3
 */
export function useSimulateOrder(
  symbol: string | null,
  params: {
    mode?: "signals" | "performance";
    limit?: number;
    k?: number;
  } = {}
) {
  return useQuery({
    queryKey: ["execution", "order", "simulate", symbol, params],
    queryFn: () => api.simulateExecutionOrder(symbol!, params),
    enabled: !!symbol,
    staleTime: 10000, // 10 seconds
  });
}

