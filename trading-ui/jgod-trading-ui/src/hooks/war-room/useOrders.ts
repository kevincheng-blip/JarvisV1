/**
 * useOrders Hook
 * 
 * React Query hook for fetching final orders data
 */

import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import type { FinalOrder } from "../../types/warRoom";
import { useWarRoomStore } from "../../store/warRoomStore";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * Fetch final orders
 */
export function useFinalOrders(targetDate?: string) {
  return useQuery<FinalOrder[]>({
    queryKey: ["finalOrders", targetDate],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (targetDate) {
        params.append("date", targetDate);
      }
      
      const response = await apiClient.get<FinalOrder[]>(
        `/api/v1/orders/final${params.toString() ? `?${params.toString()}` : ''}`
      );
      return response.data;
    },
    staleTime: 30000, // 30 seconds
    refetchOnWindowFocus: false,
  });
}

