/**
 * useSentiment Hook
 * 
 * React Query hook for fetching market sentiment data
 */

import { useQuery } from "@tanstack/react-query";
import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

export interface MarketSentiment {
  overall_sentiment: number; // -1 to 1
  bullish_count: number;
  bearish_count: number;
  neutral_count: number;
  sentiment_score: number;
  trend_direction: "bullish" | "bearish" | "neutral";
  timestamp: string;
}

/**
 * Fetch market sentiment
 */
export function useMarketSentiment() {
  return useQuery<MarketSentiment>({
    queryKey: ["marketSentiment"],
    queryFn: async () => {
      const response = await apiClient.get<MarketSentiment>(
        `/api/v1/market/sentiment`
      );
      return response.data;
    },
    staleTime: 60000, // 1 minute
    refetchInterval: 60000,
  });
}

