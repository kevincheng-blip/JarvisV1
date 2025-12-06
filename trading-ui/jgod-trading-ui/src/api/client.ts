/**
 * API Client for J-GOD Simulation API
 */

import axios from "axios";
import type { CoverageResponse, IndicatorSnapshot, Prediction, PredictionTimelineResponse } from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

export const api = {
  /**
   * Get predictions for all symbols on a specific date
   */
  getPredictions: async (date: string, universe: string = "tw_top50_2024"): Promise<Prediction[]> => {
    const response = await client.get<Prediction[]>(`/api/predictions/${date}`, {
      params: { universe },
    });
    return response.data;
  },

  /**
   * Get prediction for a specific symbol on a date
   */
  getPrediction: async (date: string, symbol: string): Promise<any> => {
    const response = await client.get(`/api/predictions/${date}/${symbol}`);
    return response.data;
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
   */
  getPredictionTimeline: async (params: {
    symbol: string;
    startDate: string; // YYYY-MM-DD
    endDate: string;   // YYYY-MM-DD
  }): Promise<PredictionTimelineResponse> => {
    const response = await client.get<PredictionTimelineResponse>(
      `/api/predictions/timeline/${params.symbol}`,
      {
        params: {
          start_date: params.startDate,
          end_date: params.endDate,
        },
      }
    );
    return response.data;
  },
};

