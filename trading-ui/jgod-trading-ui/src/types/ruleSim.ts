/**
 * Rule Simulation Types
 * 
 * TypeScript type definitions for Rule Simulation Engine.
 */

export type RuleSimTargetType = "doctrine_section" | "doctrine_file" | "alert_rules_yaml";

export type RuleSimStatus = "PENDING" | "RUNNING" | "SUCCESS" | "FAILED";

export type RuleSimArm = "BASELINE" | "VARIANT";

export type RuleSimRecommendation = "APPROVE" | "CAUTION" | "REJECT";

export type RuleSetRef = {
  id: string;
  type: RuleSimTargetType;
  description?: string | null;
  doctrine_section_ids?: string[] | null;
  alert_config_path?: string | null;
};

export type RuleSimStatusSummary = {
  status: RuleSimStatus;
  started_at?: string | null;
  finished_at?: string | null;
  error_message?: string | null;
};

export type RuleSimArmMetrics = {
  arm: RuleSimArm;
  sharpe: number;
  max_drawdown: number;
  total_return: number;
  win_rate: number;
  turnover: number;
  var_95?: number | null;
  alert_trigger_count?: number | null;
  doctrine_violation_count?: number | null;
};

export type RuleSimDeltaMetrics = {
  sharpe_delta: number;
  max_drawdown_delta: number;
  total_return_delta: number;
  win_rate_delta: number;
  turnover_delta: number;
  alert_trigger_delta?: number | null;
  doctrine_violation_delta?: number | null;
};

export type RuleSimReportSummary = {
  experiment_id: string;
  created_at: string;
  target_ruleset: RuleSetRef;
  status: RuleSimStatus;
  baseline_sharpe: number;
  variant_sharpe: number;
  sharpe_delta: number;
  recommendation: RuleSimRecommendation;
};

export type RuleSimRunRequest = {
  target_ruleset: RuleSetRef;
  baseline_version_id?: string | null;
  variant_version_id?: string | null;
  start_date: string; // YYYY-MM-DD
  end_date: string; // YYYY-MM-DD
  universe?: string[] | null;
  path_a_config_name?: string;
  note?: string | null;
};

export type RuleSimRunResponse = {
  experiment_id: string;
  status: RuleSimStatusSummary;
};

export type RuleSimReport = {
  experiment_id: string;
  config: {
    experiment_id: string;
    created_at: string;
    created_by: string;
    target_ruleset: RuleSetRef | null;
    baseline_version_id?: string | null;
    variant_version_id?: string | null;
    start_date: string;
    end_date: string;
    universe: string[];
    path_a_config_name: string;
    note?: string | null;
  };
  status: RuleSimStatusSummary;
  baseline_metrics: RuleSimArmMetrics;
  variant_metrics: RuleSimArmMetrics;
  deltas: RuleSimDeltaMetrics;
  key_findings: string[];
  recommendation: RuleSimRecommendation;
  created_at: string;
};

