/**
 * Decision AB Test Types
 * 
 * TypeScript type definitions for Decision AB Test Dashboard.
 */

export interface ArmBacktestResult {
  version: 'v1' | 'v2';
  sharpe_ratio: number;
  max_drawdown: number;
  total_return: number;
  volatility: number;
  win_rate: number;
  turnover: number;
  equity_curve: { date: string; equity: number }[];
}

export type DecisionRecommendation =
  | 'V2_PREFERRED'
  | 'V2_NOT_RECOMMENDED'
  | 'V1_PREFERRED'
  | 'NO_SIGNIFICANT_CHANGE';

export interface DecisionABTestReport {
  experiment_id: string;
  created_at: string;
  config: {
    start_date: string;
    end_date: string;
    capital: number;
    path_a_config_name: string;
  };
  baseline: ArmBacktestResult;
  variant: ArmBacktestResult;
  sharpe_delta: number;
  max_drawdown_delta: number;
  return_delta: number;
  volatility_delta: number;
  win_rate_delta: number;
  turnover_delta: number;
  recommendation: DecisionRecommendation;
  notes?: string;
}

export interface DecisionABTestReportSummary {
  experiment_id: string;
  created_at: string;
  path_a_config_name: string;
  sharpe_delta: number;
  return_delta: number;
  max_drawdown_delta: number;
  recommendation: DecisionRecommendation;
}

export interface DecisionComparisonRequest {
  start_date: string;
  end_date: string;
  capital?: number;
  path_a_config_name: string;
  note?: string;
}

