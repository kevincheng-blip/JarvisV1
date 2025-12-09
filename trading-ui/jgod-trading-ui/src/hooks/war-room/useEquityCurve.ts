/**
 * useEquityCurve Hook
 * 
 * React Query hook for fetching equity curve data
 */

import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import type { EquityPoint } from "../../types/warRoom";
import { useWarRoomStore } from "../../store/warRoomStore";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * Fetch equity curve
 */
export function useEquityCurve() {
  const { selectedRunId, dateRange } = useWarRoomStore();

  return useQuery<EquityPoint[]>({
    queryKey: ["equityCurve", selectedRunId, dateRange.start, dateRange.end],
    queryFn: async () => {
      const params: any = {
        start_date: dateRange.start,
        end_date: dateRange.end,
      };
      if (selectedRunId) {
        params.run_id = selectedRunId;
      }
      const response = await apiClient.get<EquityPoint[]>(
        `/api/v1/portfolio/equity-curve`,
        { params }
      );
      return response.data;
    },
    staleTime: 60000, // 60 seconds
    refetchOnWindowFocus: false,
  });
}

