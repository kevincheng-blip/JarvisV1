/**
 * useSentiment Hook
 * 
 * React Query hook for fetching market sentiment data
 */

import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import type { SentimentResponse } from "../../types/warRoom";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * Fetch market sentiment
 */
export function useMarketSentiment() {
  return useQuery<SentimentResponse>({
    queryKey: ["marketSentiment"],
    queryFn: async () => {
      const response = await apiClient.get<SentimentResponse>(
        `/api/v1/market/sentiment`
      );
      return response.data;
    },
    staleTime: 60000, // 60 seconds (as per SPEC 13.1)
    refetchOnWindowFocus: false,
  });
}

