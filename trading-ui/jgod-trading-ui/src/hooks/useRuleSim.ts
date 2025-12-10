/**
 * useRuleSim Hook
 * 
 * React Query hooks for Rule Simulation Engine.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import axios from "axios";
import type {
  RuleSimReportSummary,
  RuleSimReport,
  RuleSimRunRequest,
  RuleSimRunResponse,
} from "../types/ruleSim";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * Fetch recent rule simulation experiments
 */
export function useRuleSimExperiments(limit: number = 20, enabled: boolean = true) {
  return useQuery<RuleSimReportSummary[]>({
    queryKey: ["ruleSimExperiments", limit],
    queryFn: async () => {
      const response = await apiClient.get<RuleSimReportSummary[]>(
        `/api/v1/rule-sim/experiments/recent`,
        {
          params: { limit },
        }
      );
      return response.data;
    },
    staleTime: 30000, // 30 seconds
    refetchOnWindowFocus: false,
    enabled,
  });
}

/**
 * Fetch a specific rule simulation experiment report
 */
export function useRuleSimReport(experimentId: string | null, enabled: boolean = true) {
  return useQuery<RuleSimReport>({
    queryKey: ["ruleSimReport", experimentId],
    queryFn: async () => {
      if (!experimentId) throw new Error("Experiment ID is required");
      const response = await apiClient.get<RuleSimReport>(
        `/api/v1/rule-sim/experiments/${experimentId}`
      );
      return response.data;
    },
    enabled: enabled && !!experimentId,
    staleTime: 60000, // 1 minute
    refetchOnWindowFocus: false,
  });
}

/**
 * Mutation: Run a rule simulation experiment
 */
export function useRunRuleSimExperiment() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (request: RuleSimRunRequest): Promise<RuleSimRunResponse> => {
      const response = await apiClient.post<RuleSimRunResponse>(
        `/api/v1/rule-sim/run`,
        request
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ruleSimExperiments"] });
    },
  });
}

