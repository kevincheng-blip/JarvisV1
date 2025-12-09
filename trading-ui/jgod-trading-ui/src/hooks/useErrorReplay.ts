/**
 * useErrorReplay Hook
 * 
 * Fetches error replay report data from the backend API.
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

export interface ReplayMeta {
  error_id: string;
  symbol: string;
  date: string;
  timeframe: string;
  error_type?: string;
  human_summary?: string;
  pnl_impact?: number;
}

export interface PricePoint {
  ts: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface FactorPoint {
  ts: string;
  raw_score?: number;
  final_score?: number;
  factor_values: Record<string, number>;
}

export interface TradePoint {
  ts: string;
  action: "BUY" | "SELL";
  price: number;
  quantity: number;
}

export interface ReplayDiagnosis {
  root_cause: string;
  contributing_factors: string[];
  missed_signals: string[];
  doctrine_refs: string[];
}

export interface ReplayReport {
  meta: ReplayMeta;
  price_series: PricePoint[];
  factor_series: FactorPoint[];
  trades: TradePoint[];
  diagnosis: ReplayDiagnosis;
}

/**
 * Fetch error replay report
 */
export function useErrorReplay(errorId: string | null) {
  return useQuery<ReplayReport>({
    queryKey: ["errorReplay", errorId],
    queryFn: async () => {
      if (!errorId) {
        throw new Error("Error ID is required");
      }
      const response = await apiClient.get<ReplayReport>(
        `/api/v1/error-replay/${errorId}`
      );
      return response.data;
    },
    enabled: !!errorId, // Only fetch if errorId is provided
    staleTime: 60000, // 1 minute
    refetchOnWindowFocus: false,
  });
}

