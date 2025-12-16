/**
 * React Query hook for Intelligence Status
 */

import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";

export function useIntelligenceStatus() {
  return useQuery({
    queryKey: ["intelligence", "status", "latest"],
    queryFn: () => api.getIntelligenceLatest(),
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 60 * 1000, // Refetch every minute
    retry: 1,
  });
}

