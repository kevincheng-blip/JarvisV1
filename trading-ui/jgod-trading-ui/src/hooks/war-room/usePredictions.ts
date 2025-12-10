/**
 * usePredictions Hook
 * 
 * React Query hook for fetching prediction data (Top N Long/Short)
 */

import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import type { TopLongItem, TopShortItem } from "../../types/warRoom";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * Fetch top N long predictions
 * Uses Decision Layer V2 by default
 */
export function useTopLongPredictions(n: number = 30, targetDate?: string, version: "v1" | "v2" = "v2") {
  const today = targetDate || new Date().toISOString().split('T')[0];

  return useQuery<TopLongItem[]>({
    queryKey: ["topLongPredictions", n, today, version],
    queryFn: async () => {
      const params = new URLSearchParams({
        limit: n.toString(),
        version: version,
      });
      if (today) {
        params.append("date", today);
      }
      
      const response = await apiClient.get<TopLongItem[]>(
        `/api/v1/predictions/top-n/long?${params.toString()}`
      );
      return response.data;
    },
    staleTime: 30000, // 30 seconds (as per SPEC 13.1)
    refetchOnWindowFocus: false,
  });
}

/**
 * Fetch top N short predictions
 * Uses Decision Layer V2 by default
 */
export function useTopShortPredictions(n: number = 30, targetDate?: string, version: "v1" | "v2" = "v2") {
  const today = targetDate || new Date().toISOString().split('T')[0];

  return useQuery<TopShortItem[]>({
    queryKey: ["topShortPredictions", n, today, version],
    queryFn: async () => {
      const params = new URLSearchParams({
        limit: n.toString(),
        version: version,
      });
      if (today) {
        params.append("date", today);
      }
      
      const response = await apiClient.get<TopShortItem[]>(
        `/api/v1/predictions/top-n/short?${params.toString()}`
      );
      return response.data;
    },
    staleTime: 30000, // 30 seconds (as per SPEC 13.1)
    refetchOnWindowFocus: false,
  });
}

