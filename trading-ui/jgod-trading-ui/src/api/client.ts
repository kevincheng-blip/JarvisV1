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

  // Doctrine Patch API wrappers
  /**
   * Get doctrine patch queue
   * Returns empty array on 404 (no patches), throws on 5xx/network errors
   */
  getDoctrinePatchQueue: async (status?: string | null): Promise<any[]> => {
    try {
      const response = await client.get("/api/v1/doctrine/patches/queue", {
        params: status ? { status } : {},
      });
      return response.data || [];
    } catch (error: any) {
      // 404: return empty array (empty state, not error)
      if (error.response?.status === 404) {
        return [];
      }
      throw error;
    }
  },

  /**
   * Get doctrine patch by ID
   * Throws on 404 (patch not found is an error)
   */
  getDoctrinePatch: async (patchId: string): Promise<any> => {
    const response = await client.get(`/api/v1/doctrine/patches/${patchId}`);
    return response.data;
  },

  /**
   * Create a new doctrine patch
   */
  createDoctrinePatch: async (request: {
    author_id: string;
    description: string;
    changes: Array<{
      change_type: string;
      rule_id: string;
      old_text?: string | null;
      new_text?: string | null;
    }>;
  }): Promise<any> => {
    const response = await client.post("/api/v1/doctrine/patches", request);
    return response.data;
  },

  /**
   * Run Rule Sim for a patch
   */
  runDoctrinePatchSim: async (patchId: string): Promise<any> => {
    const response = await client.post(`/api/v1/doctrine/patches/${patchId}/run-sim`);
    return response.data;
  },

  /**
   * Approve a patch
   */
  approveDoctrinePatch: async (patchId: string, request: {
    reviewer_id: string;
    comment?: string | null;
  }): Promise<any> => {
    const response = await client.post(
      `/api/v1/doctrine/patches/${patchId}/approve`,
      request
    );
    return response.data;
  },

  /**
   * Reject a patch
   */
  rejectDoctrinePatch: async (patchId: string, request: {
    reviewer_id: string;
    comment?: string | null;
  }): Promise<any> => {
    const response = await client.post(
      `/api/v1/doctrine/patches/${patchId}/reject`,
      request
    );
    return response.data;
  },

  /**
   * Deploy a patch
   */
  deployDoctrinePatch: async (patchId: string, request: {
    operator_id: string;
  }): Promise<any> => {
    const response = await client.post(
      `/api/v1/doctrine/patches/${patchId}/deploy`,
      request
    );
    return response.data;
  },

  /**
   * Revert a patch
   */
  revertDoctrinePatch: async (patchId: string, request: {
    operator_id: string;
  }): Promise<any> => {
    const response = await client.post(
      `/api/v1/doctrine/patches/${patchId}/revert`,
      request
    );
    return response.data;
  },

  // S-Rank V2 API wrappers
  /**
   * Get S-Rank V2 strategy recommendation for a symbol
   * Returns recommendation with top K strategies, weights, and rationale
   */
  getSRankV2Recommendation: async (
    symbol: string,
    limit: number = 60,
    k: number = 5,
    mode: "signals" | "performance" = "performance"
  ): Promise<{
    symbol: string;
    start_date: string | null;
    end_date: string | null;
    metrics: {
      n_points: number;
      score_std: number;
      max_abs_delta: number;
      trend_slope: number;
      stability_grade: "NO_DATA" | "STABLE" | "WATCH" | "VOLATILE";
    };
    items: Array<{
      strategy: string;
      weight: number;
      score: number;
    }>;
    weights: Record<string, number>;
    rationale: Record<string, string>;
  }> => {
    const response = await client.get(
      `/api/v1/s-rank-v2/recommendation/${symbol}`,
      { params: { limit, k, mode } }
    );
    return response.data;
  },

  // Strategy Performance API wrappers
  /**
   * Get latest strategy performance snapshot for a symbol
   */
  getStrategyPerfLatest: async (symbol: string): Promise<{
    snapshot_id: string;
    created_at: string;
    symbol: string;
    limit: number;
    window: number;
    items: Array<{
      strategy_id: string;
      n_points: number;
      avg_return_proxy: number;
      sharpe_proxy: number;
      max_drawdown_proxy: number;
      turnover_proxy: number;
      decay_slope: number;
      grade: "NO_DATA" | "GOOD" | "WATCH" | "BAD";
    }>;
  }> => {
    const response = await client.get(`/api/v1/strategy-perf/latest/${symbol}`);
    return response.data;
  },

  /**
   * Recompute and save strategy performance snapshot
   */
  recomputeStrategyPerf: async (
    symbol: string,
    limit: number = 60,
    window: number = 20
  ): Promise<{
    snapshot_id: string;
    created_at: string;
    symbol: string;
    limit: number;
    window: number;
    items: Array<{
      strategy_id: string;
      n_points: number;
      avg_return_proxy: number;
      sharpe_proxy: number;
      max_drawdown_proxy: number;
      turnover_proxy: number;
      decay_slope: number;
      grade: "NO_DATA" | "GOOD" | "WATCH" | "BAD";
    }>;
  }> => {
    const response = await client.post(
      `/api/v1/strategy-perf/recompute/${symbol}`,
      null,
      { params: { limit, window } }
    );
    return response.data;
  },

  // Decision V3 API wrappers
  /**
   * Get Decision V3 for a symbol
   * Returns decision result with primary/secondary strategies, risk plan, confidence, and explanation
   */
  getDecisionV3: async (
    symbol: string,
    options: {
      mode?: "signals" | "performance";
      limit?: number;
      k?: number;
    } = {}
  ): Promise<{
    symbol: string;
    as_of_date: string | null;
    selected_primary_strategy: string | null;
    selected_secondary_strategies: string[];
    weights: Array<{
      strategy_id: string;
      weight: number;
      grade?: string | null;
      metrics?: Record<string, number> | null;
      rationale?: string | null;
    }>;
    risk_plan: {
      position_scale: number;
      risk_state: "RISK_ON" | "RISK_OFF" | "CAUTION";
      reasons: string[];
    };
    confidence: number;
    explain: string;
  }> => {
    try {
      const response = await client.get(
        `/api/v1/decision-v3/decide/${symbol}`,
        {
          params: {
            mode: options.mode || "performance",
            limit: options.limit || 60,
            k: options.k || 5,
          },
        }
      );
      return response.data;
    } catch (error: any) {
      // Backend guarantees 200, but if 404 occurs, return null for empty state
      if (error.response?.status === 404) {
        throw new Error("Decision V3 not found");
      }
      throw error;
    }
  },

  /**
   * Get latest Decision V3 snapshot for a symbol
   */
  getDecisionV3Latest: async (symbol: string): Promise<{
    snapshot_id: string;
    created_at: string;
    symbol: string;
    mode: string;
    limit: number;
    k: number;
    result: {
      symbol: string;
      as_of_date: string | null;
      selected_primary_strategy: string | null;
      selected_secondary_strategies: string[];
      weights: Array<{
        strategy_id: string;
        weight: number;
        grade?: string | null;
        metrics?: Record<string, number> | null;
        rationale?: string | null;
      }>;
      risk_plan: {
        position_scale: number;
        risk_state: "RISK_ON" | "RISK_OFF" | "CAUTION";
        reasons: string[];
      };
      confidence: number;
      explain: string;
    };
  }> => {
    try {
      const response = await client.get(`/api/v1/decision-v3/latest/${symbol}`);
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 404) {
        throw new Error("Decision V3 snapshot not found");
      }
      throw error;
    }
  },

  /**
   * Recompute and save Decision V3 snapshot
   */
  recomputeDecisionV3: async (
    symbol: string,
    options: {
      mode?: "signals" | "performance";
      limit?: number;
      k?: number;
    } = {}
  ): Promise<{
    snapshot_id: string;
    created_at: string;
    symbol: string;
    mode: string;
    limit: number;
    k: number;
    result: {
      symbol: string;
      as_of_date: string | null;
      selected_primary_strategy: string | null;
      selected_secondary_strategies: string[];
      weights: Array<{
        strategy_id: string;
        weight: number;
        grade?: string | null;
        metrics?: Record<string, number> | null;
        rationale?: string | null;
      }>;
      risk_plan: {
        position_scale: number;
        risk_state: "RISK_ON" | "RISK_OFF" | "CAUTION";
        reasons: string[];
      };
      confidence: number;
      explain: string;
    };
  }> => {
    const response = await client.post(
      `/api/v1/decision-v3/recompute/${symbol}`,
      null,
      {
        params: {
          mode: options.mode || "performance",
          limit: options.limit || 60,
          k: options.k || 5,
        },
      }
    );
    return response.data;
  },

  /**
   * List Decision V3 snapshots for a symbol
   */
  listDecisionV3Snapshots: async (
    symbol: string,
    n: number = 20
  ): Promise<{
    symbol: string;
    items: Array<{
      snapshot_id: string;
      created_at: string;
      symbol: string;
      mode: string;
      primary_strategy: string | null;
      confidence: number;
      risk_state: string;
    }>;
    total: number;
  }> => {
    const response = await client.get(`/api/v1/decision-v3/list/${symbol}`, {
      params: { n },
    });
    return response.data;
  },

  // Decision V3 Evaluation APIs
  recomputeDecisionV3Eval: async (
    symbol: string,
    options: {
      mode?: string;
      limit?: number;
      k?: number;
      window?: number;
    } = {}
  ): Promise<{
    eval_id: string;
    created_at: string;
    symbol: string;
    mode: string;
    limit: number;
    k: number;
    window: number;
    evaluation: {
      symbol: string;
      mode: string;
      limit: number;
      k: number;
      window: number;
      decision: {
        primary_strategy: string | null;
        risk_plan: {
          position_scale: number;
          risk_state: string;
        };
        confidence: number;
      };
      inputs_summary: {
        mode: string;
        limit: number;
        k: number;
        stability_grade: string;
        perf_grade: string;
      };
      metrics: {
        n_points: number;
        hit_rate_proxy: number;
        avg_return_proxy: number;
        max_drawdown_proxy: number;
        turnover_proxy: number;
        decision_consistency: number;
        verdict: string;
        recommendation_next_step: string;
      };
    };
  }> => {
    try {
      const response = await client.post(
        `/api/v1/decision-v3/eval/recompute/${symbol}`,
        {},
        {
          params: {
            mode: options.mode || "performance",
            limit: options.limit || 60,
            k: options.k || 5,
            window: options.window || 20,
          },
        }
      );
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 404) {
        throw new Error(`Evaluation not found for ${symbol}`);
      }
      throw error;
    }
  },

  getDecisionV3EvalLatest: async (symbol: string): Promise<{
    eval_id: string;
    created_at: string;
    symbol: string;
    mode: string;
    limit: number;
    k: number;
    window: number;
    evaluation: {
      symbol: string;
      mode: string;
      limit: number;
      k: number;
      window: number;
      decision: {
        primary_strategy: string | null;
        risk_plan: {
          position_scale: number;
          risk_state: string;
        };
        confidence: number;
      };
      inputs_summary: {
        mode: string;
        limit: number;
        k: number;
        stability_grade: string;
        perf_grade: string;
      };
      metrics: {
        n_points: number;
        hit_rate_proxy: number;
        avg_return_proxy: number;
        max_drawdown_proxy: number;
        turnover_proxy: number;
        decision_consistency: number;
        verdict: string;
        recommendation_next_step: string;
      };
    };
  } | null> => {
    try {
      const response = await client.get(`/api/v1/decision-v3/eval/latest/${symbol}`);
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 404) {
        return null;
      }
      throw error;
    }
  },

  listDecisionV3Evals: async (
    symbol: string,
    n: number = 20
  ): Promise<{
    symbol: string;
    items: Array<{
      eval_id: string;
      created_at: string;
      symbol: string;
      verdict: string;
      metrics_summary: {
        hit_rate_proxy: number;
        avg_return_proxy: number;
        max_drawdown_proxy: number;
      };
    }>;
    total: number;
  }> => {
    try {
      const response = await client.get(`/api/v1/decision-v3/eval/list/${symbol}`, {
        params: { n },
      });
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 404) {
        return { symbol, items: [], total: 0 };
      }
      throw error;
    }
  },

  // Decision V3 Compare APIs
  recomputeDecisionV3Compare: async (
    symbol: string,
    options: {
      mode?: string;
      limit?: number;
      k?: number;
      window?: number;
    } = {}
  ): Promise<{
    compare_id: string;
    created_at: string;
    symbol: string;
    mode: string;
    limit: number;
    k: number;
    window: number;
    compare: {
      symbol: string;
      mode: string;
      limit: number;
      k: number;
      window: number;
      winner: string;
      delta_metrics: {
        hit_rate_proxy: number;
        avg_return_proxy: number;
        max_drawdown_proxy: number;
        turnover_proxy: number;
        decision_consistency: number;
      };
      summary: string;
      recommendation_next_step: string;
    };
  }> => {
    try {
      const response = await client.post(
        `/api/v1/decision-v3/compare/recompute/${symbol}`,
        {},
        {
          params: {
            mode: options.mode || "performance",
            limit: options.limit || 60,
            k: options.k || 5,
            window: options.window || 20,
          },
        }
      );
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 404) {
        throw new Error(`Compare not found for ${symbol}`);
      }
      throw error;
    }
  },

  getDecisionV3CompareLatest: async (symbol: string): Promise<{
    compare_id: string;
    created_at: string;
    symbol: string;
    mode: string;
    limit: number;
    k: number;
    window: number;
    compare: {
      symbol: string;
      mode: string;
      limit: number;
      k: number;
      window: number;
      winner: string;
      delta_metrics: {
        hit_rate_proxy: number;
        avg_return_proxy: number;
        max_drawdown_proxy: number;
        turnover_proxy: number;
        decision_consistency: number;
      };
      summary: string;
      recommendation_next_step: string;
    };
  } | null> => {
    try {
      const response = await client.get(`/api/v1/decision-v3/compare/latest/${symbol}`);
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 404) {
        return null;
      }
      throw error;
    }
  },

  listDecisionV3Compares: async (
    symbol: string,
    n: number = 20
  ): Promise<{
    symbol: string;
    items: Array<{
      compare_id: string;
      created_at: string;
      symbol: string;
      winner: string;
      summary_short: string;
    }>;
    total: number;
  }> => {
    try {
      const response = await client.get(`/api/v1/decision-v3/compare/list/${symbol}`, {
        params: { n },
      });
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 404) {
        return { symbol, items: [], total: 0 };
      }
      throw error;
    }
  },

  recomputeDecisionV3Arena: async (
    symbol: string,
    options: {
      mode?: string;
      limit?: number;
      k?: number;
      window?: number;
    } = {}
  ): Promise<{
    arena_id: string;
    created_at: string;
    symbol: string;
    mode: string;
    window: number;
    limit: number;
    k: number;
    arena: {
      symbol: string;
      mode: string;
      window: number;
      limit: number;
      k: number;
      scoreboard: Array<{
        challenger_id: string;
        composite_score: number;
        metrics: {
          hit_rate_proxy: number;
          avg_return_proxy: number;
          max_drawdown_proxy: number;
          turnover_proxy: number;
          decision_consistency: number;
        };
        pareto_dominated: boolean;
      }>;
      winner_id: string;
      is_regression: boolean;
      auto_tuning: {
        best_config: {
          risk_mapping: Record<string, number>;
          composite_weights: Record<string, number>;
        } | null;
        top_variants: Array<{
          config: {
            risk_mapping: Record<string, number>;
            composite_weights: Record<string, number>;
          };
          score: number;
        }>;
        notes: string;
      } | null;
      summary: string;
      recommendation_next_step: string;
    };
  }> => {
    try {
      const response = await client.post(
        `/api/v1/decision-v3/arena/recompute/${symbol}`,
        {},
        {
          params: {
            mode: options.mode || "performance",
            limit: options.limit || 60,
            k: options.k || 5,
            window: options.window || 20,
          },
        }
      );
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 404) {
        throw new Error(`Arena not found for ${symbol}`);
      }
      throw error;
    }
  },

  getDecisionV3ArenaLatest: async (symbol: string): Promise<{
    arena_id: string;
    created_at: string;
    symbol: string;
    mode: string;
    window: number;
    limit: number;
    k: number;
    arena: {
      symbol: string;
      mode: string;
      window: number;
      limit: number;
      k: number;
      scoreboard: Array<{
        challenger_id: string;
        composite_score: number;
        metrics: {
          hit_rate_proxy: number;
          avg_return_proxy: number;
          max_drawdown_proxy: number;
          turnover_proxy: number;
          decision_consistency: number;
        };
        pareto_dominated: boolean;
      }>;
      winner_id: string;
      is_regression: boolean;
      auto_tuning: {
        best_config: {
          risk_mapping: Record<string, number>;
          composite_weights: Record<string, number>;
        } | null;
        top_variants: Array<{
          config: {
            risk_mapping: Record<string, number>;
            composite_weights: Record<string, number>;
          };
          score: number;
        }>;
        notes: string;
      } | null;
      summary: string;
      recommendation_next_step: string;
    };
  } | null> => {
    try {
      const response = await client.get(`/api/v1/decision-v3/arena/latest/${symbol}`);
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 404) {
        return null;
      }
      throw error;
    }
  },

  listDecisionV3Arena: async (
    symbol: string,
    n: number = 20
  ): Promise<{
    symbol: string;
    items: Array<{
      arena_id: string;
      created_at: string;
      winner_id: string;
      is_regression: boolean;
    }>;
    total: number;
  }> => {
    try {
      const response = await client.get(`/api/v1/decision-v3/arena/list/${symbol}`, {
        params: { n },
      });
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 404) {
        return { symbol, items: [], total: 0 };
      }
      throw error;
    }
  },

  // Execution API wrappers
  /**
   * Get latest execution ledger for a symbol
   * Returns ledger snapshot with NAV, cash, positions, P&L
   */
  getExecutionLedgerLatest: async (symbol: string): Promise<{
    snapshot_id: string;
    created_at: string;
    symbol: string;
    ledger: {
      symbol: string;
      cash: number;
      position: {
        qty: number;
        avg_cost: number;
        market_value: number;
        unrealized_pnl: number;
      };
      realized_pnl: number;
      unrealized_pnl: number;
      nav: number;
      last_price: number;
      updated_at: string;
    };
    is_default: boolean;
  }> => {
    try {
      const response = await client.get(`/api/v1/execution/ledger/latest/${symbol}`);
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 404) {
        // Return default ledger state
        return {
          snapshot_id: "",
          created_at: new Date().toISOString(),
          symbol,
          ledger: {
            symbol,
            cash: 1000000.0,
            position: {
              qty: 0,
              avg_cost: 0.0,
              market_value: 0.0,
              unrealized_pnl: 0.0,
            },
            realized_pnl: 0.0,
            unrealized_pnl: 0.0,
            nav: 1000000.0,
            last_price: 0.0,
            updated_at: new Date().toISOString(),
          },
          is_default: true,
        };
      }
      throw error;
    }
  },

  /**
   * Recompute (reset) execution ledger for a symbol
   */
  recomputeExecutionLedger: async (
    symbol: string,
    initialCash: number = 1000000.0
  ): Promise<{
    snapshot_id: string;
    created_at: string;
    symbol: string;
    ledger: {
      symbol: string;
      cash: number;
      position: {
        qty: number;
        avg_cost: number;
        market_value: number;
        unrealized_pnl: number;
      };
      realized_pnl: number;
      unrealized_pnl: number;
      nav: number;
      last_price: number;
      updated_at: string;
    };
    is_default: boolean;
  }> => {
    const response = await client.post(
      `/api/v1/execution/ledger/recompute/${symbol}`,
      null,
      { params: { initial_cash: initialCash } }
    );
    return response.data;
  },

  /**
   * Simulate order from latest Decision V3
   */
  simulateExecutionOrder: async (
    symbol: string,
    params: {
      mode?: "signals" | "performance";
      limit?: number;
      k?: number;
    } = {}
  ): Promise<{
    symbol: string;
    ledger: {
      symbol: string;
      cash: number;
      position: {
        qty: number;
        avg_cost: number;
        market_value: number;
        unrealized_pnl: number;
      };
      realized_pnl: number;
      unrealized_pnl: number;
      nav: number;
      last_price: number;
      updated_at: string;
    };
    decision_v3: any;
    order_request: {
      symbol: string;
      side: "BUY" | "SELL" | "HOLD";
      qty: number;
      reason: string;
      target_position_scale: number;
      current_position_scale: number;
    };
    price: number;
    has_data: boolean;
  }> => {
    try {
      const response = await client.post(
        `/api/v1/execution/order/simulate/${symbol}`,
        null,
        {
          params: {
            mode: params.mode || "performance",
            limit: params.limit || 60,
            k: params.k || 5,
          },
        }
      );
      return response.data;
    } catch (error: any) {
      // Backend guarantees 200, but handle gracefully
      if (error.response?.status === 404) {
        return {
          symbol,
          ledger: {
            symbol,
            cash: 1000000.0,
            position: {
              qty: 0,
              avg_cost: 0.0,
              market_value: 0.0,
              unrealized_pnl: 0.0,
            },
            realized_pnl: 0.0,
            unrealized_pnl: 0.0,
            nav: 1000000.0,
            last_price: 0.0,
            updated_at: new Date().toISOString(),
          },
          decision_v3: {},
          order_request: {
            symbol,
            side: "HOLD",
            qty: 0,
            reason: "資料不足",
            target_position_scale: 0.0,
            current_position_scale: 0.0,
          },
          price: 0.0,
          has_data: false,
        };
      }
      throw error;
    }
  },
};

