/**
 * useObserver Hook
 * 
 * React Query hooks for Knowledge Brain Observer API.
 */

import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import type {
  KnowledgeGovernanceSummary,
  StabilityAlert,
  SRankDistributionHistory,
} from "../types/observer";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * Fetch knowledge governance summary
 */
export function useGovernanceSummary(enabled: boolean = true) {
  return useQuery<KnowledgeGovernanceSummary>({
    queryKey: ["governanceSummary"],
    queryFn: async () => {
      const response = await apiClient.get<KnowledgeGovernanceSummary>(
        `/api/v1/observer/governance-summary`
      );
      return response.data;
    },
    staleTime: 60000, // 1 minute
    refetchInterval: 60000, // Auto-refetch every 60 seconds
    refetchOnWindowFocus: false,
    enabled,
  });
}

/**
 * Fetch stability alerts
 */
export function useStabilityAlerts(enabled: boolean = true) {
  return useQuery<StabilityAlert[]>({
    queryKey: ["stabilityAlerts"],
    queryFn: async () => {
      const response = await apiClient.get<StabilityAlert[]>(
        `/api/v1/observer/stability-alerts`
      );
      return response.data;
    },
    staleTime: 30000, // 30 seconds
    refetchInterval: 30000,
    refetchOnWindowFocus: true,
    enabled,
  });
}

/**
 * Fetch S-Rank distribution history
 */
export function useSRankDistributionHistory(
  days: number = 30,
  enabled: boolean = true
) {
  return useQuery<SRankDistributionHistory[]>({
    queryKey: ["sRankDistributionHistory", days],
    queryFn: async () => {
      const response = await apiClient.get<SRankDistributionHistory[]>(
        `/api/v1/observer/s-rank-history/distribution`,
        {
          params: { days },
        }
      );
      return response.data;
    },
    staleTime: 300000, // 5 minutes
    refetchInterval: 180000, // Auto-refetch every 3 minutes (S-Rank data changes less frequently)
    refetchOnWindowFocus: false,
    enabled,
  });
}

