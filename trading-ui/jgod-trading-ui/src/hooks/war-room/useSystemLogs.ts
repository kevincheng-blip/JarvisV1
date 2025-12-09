/**
 * useSystemLogs Hook
 * 
 * React Query hook for fetching system logs
 * 
 * Note: v1.1 uses one-time fetch. Future versions may use WebSocket or polling.
 */

import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import type { SystemLog } from "../../types/warRoom";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * Fetch system logs
 * 
 * v1.1: One-time fetch
 * Future: May use refetchInterval for polling or WebSocket
 */
export function useSystemLogs() {
  return useQuery<SystemLog[]>({
    queryKey: ["systemLogs"],
    queryFn: async () => {
      const response = await apiClient.get<SystemLog[]>(
        `/api/v1/system/logs`
      );
      return response.data;
    },
    staleTime: 30000, // 30 seconds
    refetchOnWindowFocus: false,
    // refetchInterval: 10000, // Future: Enable polling (as per SPEC 13.1)
  });
}

