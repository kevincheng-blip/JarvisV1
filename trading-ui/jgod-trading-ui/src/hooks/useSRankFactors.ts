/**
 * useSRankFactors Hook
 * 
 * React Query hooks for S-Rank Factor Engine.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import type { SRankFactor } from "../types/sRank";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * Fetch latest S-Rank factors
 */
export function useSRankLatestFactors(enabled: boolean = true) {
  return useQuery<SRankFactor[]>({
    queryKey: ["sRankLatestFactors"],
    queryFn: async () => {
      const response = await apiClient.get<SRankFactor[]>(
        `/api/v1/s-rank/factors/latest`
      );
      return response.data;
    },
    staleTime: 60000, // 1 minute
    refetchOnWindowFocus: false,
    enabled,
  });
}

/**
 * Fetch historical S-Rank factors for a strategy
 */
export function useSRankStrategyHistory(
  strategyId: string | null,
  startDate: string,
  endDate: string,
  enabled: boolean = true
) {
  return useQuery<SRankFactor[]>({
    queryKey: ["sRankStrategyHistory", strategyId, startDate, endDate],
    queryFn: async () => {
      if (!strategyId) throw new Error("Strategy ID is required");
      const response = await apiClient.get<SRankFactor[]>(
        `/api/v1/s-rank/history/${strategyId}`,
        {
          params: {
            start_date: startDate,
            end_date: endDate,
          },
        }
      );
      return response.data;
    },
    enabled: enabled && !!strategyId,
    staleTime: 300000, // 5 minutes
    refetchOnWindowFocus: false,
  });
}

/**
 * Mutation: Calculate S-Rank factors
 */
export function useCalculateSRank() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (timeHorizonDays: number = 90) => {
      const response = await apiClient.post(`/api/v1/s-rank/calculate`, {
        time_horizon_days: timeHorizonDays,
        force_recalculate: false,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sRankLatestFactors"] });
      queryClient.invalidateQueries({ queryKey: ["sRankStrategyHistory"] });
    },
  });
}

