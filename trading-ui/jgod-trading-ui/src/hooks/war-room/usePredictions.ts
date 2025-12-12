/**
 * usePredictions Hook
 * 
 * React Query hook for fetching prediction data (Top N Long/Short)
 */

import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import type { TopLongItem, TopShortItem } from "../../types/warRoom";
import type { DecisionContextV2 } from "../../types/warRoomV2";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Dev-only: Log request URLs
if (import.meta.env.DEV) {
  apiClient.interceptors.request.use((config) => {
    const fullUrl = `${config.baseURL}${config.url}`;
    console.debug(`[API] ${config.method?.toUpperCase()} ${fullUrl}`, config.params || {});
    return config;
  });
}

/**
 * Fetch top N long predictions
 * Uses Decision Layer V2 by default
 */
export function useTopLongPredictions(
  options?: {
    limit?: number;
    targetDate?: string;
    version?: "v1" | "v2";
  }
) {
  const { limit = 5, targetDate, version = "v2" } = options || {};
  const today = targetDate || new Date().toISOString().split('T')[0];

  return useQuery<TopLongItem[]>({
    queryKey: ["topLongPredictions", limit, today, version],
    queryFn: async () => {
      const params = new URLSearchParams({
        limit: limit.toString(),
        version: version,
      });
      if (today) {
        params.append("date", today);
      }
      
      // Backend endpoint is /api/top-n/long (no version prefix)
      const endpoint = `/api/top-n/long?${params.toString()}`;
      const response = await apiClient.get<TopLongItem[]>(endpoint);
      return response.data;
    },
    staleTime: 30000, // 30 seconds
    refetchInterval: 45000, // Auto-refetch every 45 seconds
    refetchOnWindowFocus: false,
  });
}

/**
 * Fetch top N short predictions
 * Uses Decision Layer V2 by default
 */
export function useTopShortPredictions(
  options?: {
    limit?: number;
    targetDate?: string;
    version?: "v1" | "v2";
  }
) {
  const { limit = 5, targetDate, version = "v2" } = options || {};
  const today = targetDate || new Date().toISOString().split('T')[0];

  return useQuery<TopShortItem[]>({
    queryKey: ["topShortPredictions", limit, today, version],
    queryFn: async () => {
      const params = new URLSearchParams({
        limit: limit.toString(),
        version: version,
      });
      if (today) {
        params.append("date", today);
      }
      
      // Backend endpoint is /api/top-n/short (no version prefix)
      const endpoint = `/api/top-n/short?${params.toString()}`;
      const response = await apiClient.get<TopShortItem[]>(endpoint);
      return response.data;
    },
    staleTime: 30000, // 30 seconds
    refetchInterval: 45000, // Auto-refetch every 45 seconds
    refetchOnWindowFocus: false,
  });
}

/**
 * Fetch Decision Context V2 for a specific symbol
 */
export function useFinalScoreV2(symbol: string | null, date: string | null, enabled: boolean = true) {
  return useQuery<DecisionContextV2>({
    queryKey: ["finalScoreV2", symbol, date],
    queryFn: async () => {
      if (!symbol) throw new Error("Symbol is required");
      
      const params = new URLSearchParams({
        symbol: symbol,
      });
      if (date) {
        params.append("date", date);
      }
      
      // Note: /api/v2/predictions/final-score doesn't exist in backend
      // Using latest endpoint as fallback
      const response = await apiClient.get<DecisionContextV2>(
        `/api/v1/predictions/latest/${symbol}?${params.toString()}`
      );
      return response.data;
    },
    staleTime: 60000, // 1 minute
    refetchOnWindowFocus: false,
    enabled: enabled && !!symbol,
  });
}

