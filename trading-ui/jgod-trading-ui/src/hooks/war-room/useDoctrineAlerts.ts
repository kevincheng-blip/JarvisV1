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
 */
export function useDoctrineAlerts() {
  return useQuery<DoctrineAlert[]>({
    queryKey: ["doctrineAlerts"],
    queryFn: async () => {
      const response = await apiClient.get<DoctrineAlert[]>(
        `/api/v1/doctrine/alerts`
      );
      return response.data;
    },
    staleTime: 30000, // 30 seconds
    refetchOnWindowFocus: false,
  });
}

