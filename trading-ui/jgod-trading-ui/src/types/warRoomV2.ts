/**
 * War Room V2 Types
 * 
 * TypeScript type definitions for War Room V2 Dashboard.
 */

import type { TopLongItem, TopShortItem } from "./warRoom";
import type { DecisionABTestReport, DecisionRecommendation } from "./decisionAb";
import type { DoctrinePatchSummary } from "./doctrinePatch";
import type { SRankDistributionHistory } from "./observer";

/**
 * Decision Context V2 (完整上下文)
 */
export interface DecisionContextV2 {
  symbol: string;
  final_score: number;
  raw_score: number;
  strategy_scores?: Record<string, number>;
  s_rank_weighted_score?: number;
  s_rank_level?: 'S' | 'A' | 'B' | 'C' | 'D';
  conflict_summary?: string;
  doctrine_alerts?: Array<{
    type: string;
    severity: 'info' | 'warning' | 'critical';
    message: string;
    rule_id?: string;
  }>;
}

/**
 * Executive Summary Card Data
 */
export interface ExecutiveSummaryCard {
  title: string;
  value: number | string;
  color: "green" | "yellow" | "red";
  subtitle?: string;
}

/**
 * AB Test Summary Data
 */
export interface AbTestSummary {
  sharpe_delta: number;
  max_drawdown_delta: number;
  return_delta: number;
  recommendation: DecisionRecommendation;
  equity_curve?: { date: string; equity: number }[];
}

/**
 * War Room V2 Dashboard State
 */
export interface WarRoomV2State {
  criticalAlerts: number;
  pendingPatches: number;
  abTestSummary: AbTestSummary | null;
  topLongPredictions: TopLongItem[];
  topShortPredictions: TopShortItem[];
  sRankDistribution: SRankDistributionHistory[];
  patchQueue: DoctrinePatchSummary[];
}
