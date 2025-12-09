/**
 * usePredictions Hook
 * 
 * React Query hook for fetching prediction data (Top N Long/Short)
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

export interface PredictionItem {
  symbol: string;
  name_zh?: string;
  name_en?: string;
  final_score: number;
  raw_score: number;
  strategy_score: number;
  signal: string;
  sector?: string;
  date: string;
}

/**
 * Fetch top N long predictions
 */
export function useTopLongPredictions(n: number = 30) {
  const today = new Date().toISOString().split('T')[0];

  return useQuery<PredictionItem[]>({
    queryKey: ["topLongPredictions", n, today],
    queryFn: async () => {
      const response = await apiClient.get<PredictionItem[]>(
        `/api/v1/predictions/top-n/long`,
        {
          params: {
            n,
            date: today,
          },
        }
      );
      return response.data;
    },
    staleTime: 300000, // 5 minutes
  });
}

/**
 * Fetch top N short predictions
 */
export function useTopShortPredictions(n: number = 30) {
  const today = new Date().toISOString().split('T')[0];

  return useQuery<PredictionItem[]>({
    queryKey: ["topShortPredictions", n, today],
    queryFn: async () => {
      const response = await apiClient.get<PredictionItem[]>(
        `/api/v1/predictions/top-n/short`,
        {
          params: {
            n,
            date: today,
          },
        }
      );
      return response.data;
    },
    staleTime: 300000,
  });
}

