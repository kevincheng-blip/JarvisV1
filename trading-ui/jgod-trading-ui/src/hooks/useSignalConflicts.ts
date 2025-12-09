/**
 * useSignalConflicts Hook
 * 
 * Fetches signal conflict and consensus data from the backend API.
 */

import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import type { SignalConflictItem } from "../types/signalConflict";
import { useWarRoomStore } from "../store/warRoomStore";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * Fetch signal conflicts for a specific date
 */
export function useSignalConflicts(
  date?: string,
  limit: number = 100,
  side: "all" | "long" | "short" = "all"
) {
  const { dateRange } = useWarRoomStore();
  const queryDate = date || dateRange.end;

  return useQuery<SignalConflictItem[]>({
    queryKey: ["signalConflicts", { date: queryDate, limit, side }],
    queryFn: async () => {
      const response = await apiClient.get<SignalConflictItem[]>(
        `/api/v1/predictions/conflicts`,
        {
          params: {
            date: queryDate,
            limit,
            side,
          },
        }
      );
      return response.data;
    },
    staleTime: 30000, // 30 seconds
    refetchOnWindowFocus: false,
    enabled: !!queryDate,
  });
}

