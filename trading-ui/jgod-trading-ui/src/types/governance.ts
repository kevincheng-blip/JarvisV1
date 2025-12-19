export interface GovernanceModuleStatus {
  status?: string;
  score?: number | null;
  updated_at?: string | null;
  is_stub?: boolean;
  reasons?: string[] | null;
  metrics?: Record<string, any> | null;
}

export interface GovernanceSummary {
  drift_status: string;
  execution_confidence: GovernanceModuleStatus;
  cluster_risk: GovernanceModuleStatus;
  regime: GovernanceModuleStatus;
  market_complexity: string | number;
  ai_action:
    | "FULL_TRUST"
    | "CAUTIOUS_USE"
    | "OBSERVE_ONLY"
    | "REDUCE_EXPOSURE"
    | "BLOCK_AI"
    | string;
  primary_reason_code?: string;
  human_sentence?: string;
  recommended_human_action?: string;
  action_confidence?: string;
  explain?: Record<string, any> | null;
  recommended_ops?: {
    mode: "FULL_TRUST" | "CAUTIOUS_USE" | "OBSERVE_ONLY" | "REDUCE_EXPOSURE" | "BLOCK_AI";
    suggested_exposure_cap: number | null;
    notes: string[];
  };
  guardrails?: {
    max_position_pct: number;
    max_turnover: number;
    allow_new_positions: boolean;
    allow_leverage: boolean;
  };
  updated_at?: string | null;
  is_stub?: boolean;
  reasons?: string[] | null;
  decision_context?: {
    type?: string;
    regime?: string;
    cluster?: string;
  } | null;
}


