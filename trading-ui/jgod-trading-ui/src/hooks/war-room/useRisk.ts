/**
 * useRisk Hook
 * 
 * React Query hook for fetching risk and exposure data
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

export interface AggregateRisk {
  total_exposure: number;
  long_exposure: number;
  short_exposure: number;
  net_exposure: number;
  leverage: number;
  var_95: number;
  max_drawdown: number;
  concentration_risk: number;
}

export interface ExposureHeatmapItem {
  symbol: string;
  weight: number;
  side: "long" | "short";
  sector?: string;
}

/**
 * Fetch aggregate risk overview
 */
export function useAggregateRisk() {
  return useQuery<AggregateRisk>({
    queryKey: ["aggregateRisk"],
    queryFn: async () => {
      const response = await apiClient.get<AggregateRisk>(
        `/api/v1/portfolio/risk`
      );
      return response.data;
    },
    staleTime: 30000, // 30 seconds
    refetchInterval: 30000,
  });
}

/**
 * Fetch exposure heatmap data
 */
export function useExposureHeatmap() {
  return useQuery<ExposureHeatmapItem[]>({
    queryKey: ["exposureHeatmap"],
    queryFn: async () => {
      const response = await apiClient.get<ExposureHeatmapItem[]>(
        `/api/v1/portfolio/exposure`
      );
      return response.data;
    },
    staleTime: 30000,
    refetchInterval: 30000,
  });
}

