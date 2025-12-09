/**
 * useMicrostructure Hook
 * 
 * React Query hook for fetching microstructure factors
 */

import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import type { MicroFactor } from "../../types/warRoom";
import { useWarRoomStore } from "../../store/warRoomStore";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * Fetch microstructure factors for selected symbol
 */
export function useMicrostructureFactors() {
  const { selectedSymbol } = useWarRoomStore();

  return useQuery<MicroFactor | null>({
    queryKey: ["microstructureFactors", selectedSymbol],
    queryFn: async () => {
      if (!selectedSymbol) {
        return null;
      }
      try {
        const response = await apiClient.get<MicroFactor>(
          `/api/v1/factors/microstructure`,
          {
            params: {
              symbol: selectedSymbol,
            },
          }
        );
        return response.data;
      } catch (error: any) {
        // Handle 404 gracefully (as per SPEC 12.2)
        if (error.response?.status === 404) {
          return null; // Return null instead of throwing
        }
        throw error;
      }
    },
    staleTime: 30000, // 30 seconds
    refetchOnWindowFocus: false,
    enabled: !!selectedSymbol, // Only fetch if symbol is selected
  });
}

