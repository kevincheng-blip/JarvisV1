/**
 * useDecisionAbTest Hook
 * 
 * React Query hooks for Decision AB Test API.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../api/client";
import type {
  DecisionABTestReport,
  DecisionABTestReportSummary,
  DecisionComparisonRequest,
} from "../types/decisionAb";

/**
 * Mutation: Run Decision V1 vs V2 AB Test
 */
export function useRunDecisionAbTest() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (request: DecisionComparisonRequest) => {
      const response = await apiClient.post<DecisionABTestReport>(
        `/api/v1/ab-test/decision-comparison`,
        request
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["decisionAbReports"] });
    },
  });
}

/**
 * Fetch recent Decision AB Test reports
 */
export function useRecentDecisionAbReports(limit: number = 20) {
  return useQuery<DecisionABTestReportSummary[]>({
    queryKey: ["decisionAbReports", "recent", limit],
    queryFn: async () => {
      const response = await apiClient.get<DecisionABTestReportSummary[]>(
        `/api/v1/ab-test/decision-reports/recent`,
        {
          params: { limit },
        }
      );
      return response.data;
    },
    staleTime: 60000, // 1 minute
    refetchInterval: 90000, // Auto-refetch every 90 seconds
    refetchOnWindowFocus: false,
  });
}

/**
 * Fetch a specific Decision AB Test report by experiment ID
 */
export function useDecisionAbReport(experimentId: string | null, enabled: boolean = true) {
  return useQuery<DecisionABTestReport>({
    queryKey: ["decisionAbReport", experimentId],
    queryFn: async () => {
      if (!experimentId) throw new Error("Experiment ID is required");
      const response = await apiClient.get<DecisionABTestReport>(
        `/api/v1/ab-test/decision-reports/${experimentId}`
      );
      return response.data;
    },
    enabled: enabled && !!experimentId,
    staleTime: 300000, // 5 minutes
    refetchOnWindowFocus: false,
  });
}

