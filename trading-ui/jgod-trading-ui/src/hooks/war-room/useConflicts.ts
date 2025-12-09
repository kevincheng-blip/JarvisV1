/**
 * useConflicts Hook
 * 
 * React Query hook for fetching signal conflict data
 */

import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import type { ConflictItem } from "../../types/warRoom";
import { useWarRoomStore } from "../../store/warRoomStore";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * Fetch signal conflicts for selected symbol
 */
export function useSignalConflicts() {
  const { selectedSymbol } = useWarRoomStore();

  return useQuery<ConflictItem | null>({
    queryKey: ["signalConflicts", selectedSymbol],
    queryFn: async () => {
      if (!selectedSymbol) {
        return null;
      }
      const response = await apiClient.get<ConflictItem>(
        `/api/v1/predictions/conflicts`,
        {
          params: {
            symbol: selectedSymbol,
          },
        }
      );
      return response.data;
    },
    staleTime: 30000, // 30 seconds
    refetchOnWindowFocus: false,
    enabled: !!selectedSymbol, // Only fetch if symbol is selected
  });
}

