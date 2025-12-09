/**
 * usePositionHealth Hook
 * 
 * React Query hook for fetching position health data
 */

import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import type { PositionHealth } from "../../types/warRoom";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * Fetch position health
 */
export function usePositionHealth() {
  return useQuery<PositionHealth>({
    queryKey: ["positionHealth"],
    queryFn: async () => {
      const response = await apiClient.get<PositionHealth>(
        `/api/v1/portfolio/positions/health`
      );
      return response.data;
    },
    staleTime: 60000, // 60 seconds
    refetchOnWindowFocus: false,
  });
}

