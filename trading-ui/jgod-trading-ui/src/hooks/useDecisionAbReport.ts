/**
 * useDecisionAbReport Hook
 * 
 * Fetches Decision Layer AB test results from the backend API.
 */

import { useQuery } from "@tanstack/react-query";
import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

export interface ArmMetrics {
  sharpe: number;
  max_drawdown: number;
  total_return: number;
  win_rate: number;
  avg_trade_return: number;
  num_trades: number;
  turnover: number;
  vol_annualized: number;
}

export interface ArmResult {
  experiment_id: string;
  mode: string;
  start_date: string;
  end_date: string;
  metrics: ArmMetrics;
}

export interface DecisionAbResult {
  experiment_id: string;
  created_at: string;
  raw_only: ArmResult;
  decision_on: ArmResult;
  delta_sharpe: number;
  delta_max_drawdown: number;
  delta_total_return: number;
  delta_win_rate: number;
  delta_turnover: number;
}

/**
 * Fetch recent Decision AB test results
 */
export function useDecisionAbRecent(limit: number = 5) {
  return useQuery<DecisionAbResult[]>({
    queryKey: ["decisionAbRecent", limit],
    queryFn: async () => {
      const response = await apiClient.get<DecisionAbResult[]>(
        `/api/v1/decision/ab-report/recent`,
        { params: { limit } }
      );
      return response.data;
    },
    staleTime: 60000, // 1 minute
    refetchOnWindowFocus: false,
  });
}

