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
   * Get prediction timeline for a specific symbol
   * Returns empty timeline on 404 (no data), throws on 5xx/network errors
   */
  getPredictionTimeline: async (params: {
    symbol: string;
    startDate: string; // YYYY-MM-DD
    endDate: string;   // YYYY-MM-DD
  }): Promise<PredictionTimelineResponse> => {
    try {
      const response = await client.get<{
        symbol: string;
        start_date: string;
        end_date: string;
        items: Array<{
          date: string;
          raw_score: number;
          final_score: number;
          signal: string;
        }>;
      }>(
        `/api/v1/predictions/timeline/${params.symbol}`,
        {
          params: {
            limit: 60, // Default limit
          },
        }
      );
      
      // Transform backend response to frontend format
      return {
        symbol: response.data.symbol,
        start_date: response.data.start_date || params.startDate,
        end_date: response.data.end_date || params.endDate,
        points: response.data.items.map((item) => ({
          date: item.date,
          score: item.final_score || item.raw_score,
          signal: item.signal,
        })),
      };
    } catch (error: any) {
      // 404: return empty timeline (empty state, not error)
      if (error.response?.status === 404) {
        return {
          symbol: params.symbol,
          start_date: params.startDate,
          end_date: params.endDate,
          points: [],
        };
      }
      // 5xx or network errors: throw (show error state)
      throw error;
    }
  },

  /**
   * Get latest prediction for a specific symbol
   * Returns null on 404 (no data), throws on 5xx/network errors
   */
  getLatestPrediction: async (symbol: string, date?: string): Promise<LatestPrediction | null> => {
    try {
      const params: any = {};
      if (date) {
        params.date = date;
      }
      const response = await client.get<LatestPrediction>(
        `/api/v1/predictions/latest/${symbol}`,
        { params }
      );
      return response.data;
    } catch (error: any) {
      // 404: return null (empty state, not error)
      if (error.response?.status === 404) {
        return null;
      }
      // 5xx or network errors: throw (show error state)
      throw error;
    }
  },

  /**
   * Get prediction stability metrics for a symbol
   * Returns stability metrics including grade, std, max_delta, trend_slope
   */
  getPredictionStability: async (symbol: string, limit: number = 60): Promise<{
    symbol: string;
    n_points: number;
    score_std: number;
    max_abs_delta: number;
    trend_slope: number;
    stability_grade: "NO_DATA" | "STABLE" | "WATCH" | "VOLATILE";
    thresholds: Record<string, number>;
  }> => {
    const response = await client.get(
      `/api/v1/observer/prediction-stability/${symbol}`,
      { params: { limit } }
    );
    return response.data;
  },
};

