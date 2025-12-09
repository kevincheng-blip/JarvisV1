/**
 * useDoctrineAlerts Hook
 * 
 * React Query hook for fetching Doctrine alerts
 */

import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import type { DoctrineAlert } from "../../types/warRoom";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * Fetch Doctrine alerts
 * 
 * @param symbol - 可選的股票代號，用於過濾該股票的警示
 */
export function useDoctrineAlerts(symbol?: string | null) {
  return useQuery<DoctrineAlert[]>({
    queryKey: ["doctrineAlerts", symbol],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (symbol) {
        params.append("symbol", symbol);
      }
      
      const response = await apiClient.get<DoctrineAlert[]>(
        `/api/v1/doctrine/alerts${params.toString() ? `?${params.toString()}` : ''}`
      );
      return response.data;
    },
    staleTime: 30000, // 30 seconds
    refetchOnWindowFocus: false,
  });
}

