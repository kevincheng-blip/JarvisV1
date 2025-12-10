/**
 * S-Rank Factor Types
 * 
 * TypeScript type definitions for S-Rank Factor Engine.
 */

export type RankLevel = "S" | "A" | "B" | "C" | "D";

export type StrategyPerformanceSnapshot = {
  strategy_id: string;
  sharpe_ratio: number;
  max_drawdown: number;
  total_return: number;
  avg_holding_period_days: number;
  last_run_date: string;
  is_active: boolean;
  market_correlation: number;
};

export type SignalQualityFactors = {
  signal_strength_confidence: number;
  factor_decay_rate: number;
  consistency_score: number;
};

export type SRankFactor = {
  strategy_id: string;
  performance_snapshot: StrategyPerformanceSnapshot;
  quality_factors: SignalQualityFactors;
  s_rank_score: number;
  rank_level: RankLevel;
  calculated_at: string;
};

