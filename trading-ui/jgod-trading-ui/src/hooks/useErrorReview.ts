/**
 * useErrorReview Hook
 * 
 * React Query hook for fetching error review data from the API.
 */

import { useQuery } from "@tanstack/react-query";
import { ErrorReviewItem, ErrorReviewParams } from "../types/errorReview";
import { apiClient } from "../api/client";

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

