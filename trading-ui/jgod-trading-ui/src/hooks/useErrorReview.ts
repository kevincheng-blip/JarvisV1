/**
 * useErrorReview Hook
 * 
 * React Query hook for fetching error review data from the API.
 */

import { useQuery } from "@tanstack/react-query";
import { ErrorReviewItem, ErrorReviewParams } from "../types/errorReview";
import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

export function useErrorReview(params: ErrorReviewParams = {}) {
  const {
    startDate,
    endDate,
    symbol,
    errorType,
    limit = 50,
  } = params;

  return useQuery<ErrorReviewItem[]>({
    queryKey: ["errorReview", startDate, endDate, symbol, errorType, limit],
    queryFn: async () => {
      const searchParams = new URLSearchParams();
      
      if (limit) {
        searchParams.append("limit", limit.toString());
      }
      if (startDate) {
        searchParams.append("start_date", startDate);
      }
      if (endDate) {
        searchParams.append("end_date", endDate);
      }
      if (symbol) {
        searchParams.append("symbol", symbol);
      }
      if (errorType) {
        searchParams.append("error_type", errorType);
      }

      const url = `/api/v1/error-review/recent?${searchParams.toString()}`;
      const response = await apiClient.get<ErrorReviewItem[]>(url);
      return response.data;
    },
    staleTime: 30000, // 30 seconds
    refetchOnWindowFocus: false,
  });
}

