/**
 * usePolicy Hook
 * 
 * React Query hook for fetching Policy-related data
 */

import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import { useWarRoomStore } from "../../store/warRoomStore";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

export interface PolicyExperimentSummary {
  run_id: string;
  timestamp: string;
  start_date: string;
  end_date: string;
  score: number;
  sharpe_ratio: number;
  max_drawdown: number;
  total_return: number;
  win_rate: number;
  num_days: number;
  num_trades: number;
  long_budget: number;
  short_budget: number;
  max_weight_per_symbol: number;
  min_score: number;
  allow_short: boolean;
}

export interface PolicyActiveConfig {
  file_path: string;
  exists: boolean;
  risk_version?: number;
  run_id?: string;
  start_date?: string;
  end_date?: string;
  long_budget?: number;
  short_budget?: number;
  max_weight_per_symbol?: number;
  min_score?: number;
  allow_short?: boolean;
}

/**
 * Fetch policy experiment history
 */
export function usePolicyExperimentsHistory() {
  const { dateRange } = useWarRoomStore();

  return useQuery<PolicyExperimentSummary[]>({
    queryKey: ["policyExperimentsHistory", dateRange.start, dateRange.end],
    queryFn: async () => {
      const params = new URLSearchParams({
        start_date: dateRange.start,
        end_date: dateRange.end,
        limit: "100",
      });
      const response = await apiClient.get<PolicyExperimentSummary[]>(
        `/api/v1/policy/experiments/history?${params.toString()}`
      );
      return response.data;
    },
    staleTime: 60000, // 1 minute
  });
}

/**
 * Fetch best policy experiment
 */
export function useBestPolicyExperiment() {
  const { dateRange } = useWarRoomStore();

  return useQuery<PolicyExperimentSummary>({
    queryKey: ["bestPolicyExperiment", dateRange.start, dateRange.end],
    queryFn: async () => {
      const params = new URLSearchParams({
        start_date: dateRange.start,
        end_date: dateRange.end,
      });
      const response = await apiClient.get<PolicyExperimentSummary>(
        `/api/v1/policy/experiments/best?${params.toString()}`
      );
      return response.data;
    },
    staleTime: 60000,
  });
}

/**
 * Fetch active risk config
 */
export function useActiveRiskConfig() {
  return useQuery<PolicyActiveConfig>({
    queryKey: ["activeRiskConfig"],
    queryFn: async () => {
      const response = await apiClient.get<PolicyActiveConfig>(
        `/api/v1/policy/risk-config/active`
      );
      return response.data;
    },
    staleTime: 300000, // 5 minutes
  });
}

