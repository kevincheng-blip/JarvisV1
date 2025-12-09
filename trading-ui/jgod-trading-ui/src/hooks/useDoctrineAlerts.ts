/**
 * useDoctrineAlerts Hook
 * 
 * Fetches Doctrine alerts from the backend API.
 */

import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import type { DoctrineAlertItem, DoctrineAlertSeverity, DoctrineAlertSource } from "../types/doctrineAlert";

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
export function useDoctrineAlerts(
  symbol?: string | null,
  severity?: DoctrineAlertSeverity | "all",
  source?: DoctrineAlertSource | "all",
  enabled: boolean = true
) {
  return useQuery<DoctrineAlertItem[]>({
    queryKey: ["doctrineAlerts", { symbol, severity, source }],
    queryFn: async () => {
      const response = await apiClient.get<DoctrineAlertItem[]>(
        `/api/v1/doctrine/alerts`,
        {
          params: {
            symbol: symbol || undefined,
            severity: severity || "all",
            source: source || "all",
            limit: 200,
          },
        }
      );
      return response.data;
    },
    staleTime: 30000, // 30 seconds
    refetchOnWindowFocus: false,
    enabled: enabled,
  });
}

