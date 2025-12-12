/**
 * API Client for J-GOD Simulation API
 */

import axios from "axios";
import type { CoverageResponse, IndicatorSnapshot, LatestPrediction, Prediction, PredictionTimelineResponse } from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Dev-only: Log request URLs
if (import.meta.env.DEV) {
  client.interceptors.request.use((config) => {
    const fullUrl = `${config.baseURL}${config.url}`;
    console.debug(`[API] ${config.method?.toUpperCase()} ${fullUrl}`, config.params || {});
    return config;
  });
}

// Export client for use in hooks
export const apiClient = client;

export const api = {
  /**
   * Get predictions for all symbols on a specific date
   * Note: Uses top-n/long endpoint as fallback since /api/predictions/{date} doesn't exist
   */
  getPredictions: async (date: string, universe: string = "tw_top50_2024"): Promise<Prediction[]> => {
    try {
      const response = await client.get<Prediction[]>(`/api/top-n/long`, {
        params: { date, limit: 200 },
      });
      return response.data || [];
    } catch (error: any) {
      // Return empty array for 404 or other errors (empty state, not error)
      if (error.response?.status === 404) {
        return [];
      }
      throw error;
    }
  },

  /**
   * Get prediction for a specific symbol on a date
   * Note: Uses latest endpoint since /api/predictions/{date}/{symbol} doesn't exist
   */
  getPrediction: async (date: string, symbol: string): Promise<any> => {
    try {
      const response = await client.get(`/api/v1/predictions/latest/${symbol}`, {
        params: { date },
      });
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 404) {
        throw new Error(`No prediction found for ${symbol} on ${date}`);
      }
      throw error;
    }
  },

  /**
   * Get 100-indicator snapshot for a symbol on a date
   */
  getIndicators: async (date: string, symbol: string): Promise<IndicatorSnapshot> => {
    const response = await client.get<IndicatorSnapshot>(`/api/indicators/${symbol}/${date}`);
    return response.data;
  },

  /**
   * Get universe coverage status (new endpoint with summary)
   */
  getCoverage: async (
    startDate: string,
    endDate: string,
  ): Promise<any> => {
    const response = await client.get("/api/universe/coverage", {
      params: {
        start_date: startDate,
        end_date: endDate,
      },
    });
    return response.data;
  },

  /**
   * Get universe coverage detail (legacy endpoint)
   */
  getCoverageDetail: async (
    universe: string = "tw_top50_2024",
    fromDate?: string,
    toDate?: string,
  ): Promise<CoverageResponse> => {
    const response = await client.get<CoverageResponse>("/api/universe/coverage-detail", {
      params: {
        universe,
        from_date: fromDate,
        to_date: toDate,
      },
    });
    return response.data;
  },

  /**
   * Get prediction timeline for a specific symbol within a date range
   * Note: Endpoint doesn't exist yet, returns empty timeline gracefully
   */
  getPredictionTimeline: async (params: {
    symbol: string;
    startDate: string; // YYYY-MM-DD
    endDate: string;   // YYYY-MM-DD
  }): Promise<PredictionTimelineResponse> => {
    try {
      // TODO: Implement timeline endpoint in backend
      // For now, return empty timeline to prevent 404 errors
      return {
        symbol: params.symbol,
        startDate: params.startDate,
        endDate: params.endDate,
        points: [],
      };
    } catch (error: any) {
      // Return empty timeline for any error (empty state, not error)
      return {
        symbol: params.symbol,
        startDate: params.startDate,
        endDate: params.endDate,
        points: [],
      };
    }
  },

  /**
   * Get latest prediction for a specific symbol
   */
  getLatestPrediction: async (symbol: string, date?: string): Promise<LatestPrediction> => {
    const params: any = {};
    if (date) {
      params.date = date;
    }
    const response = await client.get<LatestPrediction>(
      `/api/v1/predictions/latest/${symbol}`,
      { params }
    );
    return response.data;
  },
};

