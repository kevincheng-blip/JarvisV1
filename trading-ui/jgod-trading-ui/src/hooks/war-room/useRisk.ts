/**
 * useRisk Hook
 * 
 * React Query hook for fetching risk and exposure data
 */

import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import type { PortfolioRisk, ExposureResponse } from "../../types/warRoom";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * Fetch aggregate risk overview
 */
export function useAggregateRisk() {
  return useQuery<PortfolioRisk>({
    queryKey: ["aggregateRisk"],
    queryFn: async () => {
      const response = await apiClient.get<PortfolioRisk>(
        `/api/v1/portfolio/risk`
      );
      return response.data;
    },
    staleTime: 60000, // 60 seconds (as per SPEC 13.1)
    refetchOnWindowFocus: false,
  });
}

/**
 * Fetch exposure heatmap data
 */
export function useExposureHeatmap() {
  return useQuery<ExposureResponse>({
    queryKey: ["exposureHeatmap"],
    queryFn: async () => {
      const response = await apiClient.get<ExposureResponse>(
        `/api/v1/portfolio/exposure`
      );
      return response.data;
    },
    staleTime: 60000, // 60 seconds (as per SPEC 13.1)
    refetchOnWindowFocus: false,
  });
}

