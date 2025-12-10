/**
 * Knowledge Brain Observer Types
 * 
 * TypeScript type definitions for Observer API.
 */

export type KnowledgeGovernanceSummary = {
  timestamp: string; // ISO datetime string
  total_sections: number;
  pending_review_count: number;
  critical_alerts_active: number;
  sections_modified_last_7d: number;
  simulations_last_30d: number;
  sim_approve_rate_30d: number;
  sim_maxdd_increase_rate_30d: number;
  s_rank_recalculations_last_24h: number;
  s_rank_strategy_degradation_7d: number;
  s_rank_distribution: {
    S: number;
    A: number;
    B: number;
    C: number;
    D: number;
  };
};

export type StabilityAlert = {
  severity: "CRITICAL" | "WARNING" | "INFO";
  message: string;
  timestamp: string; // ISO datetime string
};

export type SRankDistributionHistory = {
  date: string; // ISO date string
  distribution: {
    S: number;
    A: number;
    B: number;
    C: number;
    D: number;
  };
};

