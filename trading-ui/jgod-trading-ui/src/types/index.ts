/**
 * TypeScript Type Definitions for J-GOD Trading UI
 */

export interface Prediction {
  symbol: string;
  name_zh?: string;
  name_en?: string;
  sector_zh?: string;
  sector_en?: string;
  total_score: number;
  verdict: "STRONG_BUY" | "BUY" | "NEUTRAL" | "AVOID" | "SHORT";
}

export interface Indicator {
  indicator_code: string;
  category: string;
  raw_value: number | null;
  normalized_value: number | null;
  weight: number | null;
  status: string;
}

export interface IndicatorSnapshot {
  symbol: string;
  date: string;
  indicators: Indicator[];
}

export interface CoverageItem {
  symbol: string;
  name: string;
  bar_days: number;
  indicator_days: number;
  coverage: number; // 0~1
}

export interface CoverageSummary {
  start_date: string;
  end_date: string;
  total_symbols: number;
  completed_symbols: number;
  average_coverage: number;
  items: CoverageItem[];
}

// Legacy interface for old coverage endpoint
export interface CoverageResponse {
  symbols: string[];
  dates: string[];
  coverage: Array<{
    symbol: string;
    date: string;
    status: "full" | "partial" | "missing";
    indicator_count: number;
    has_prediction: boolean;
  }>;
}

// Prediction Timeline types
export interface PredictionTimelinePoint {
  date: string;
  score: number;
  signal: string;
}

export interface PredictionTimelineResponse {
  symbol: string;
  start_date: string;
  end_date: string;
  points: PredictionTimelinePoint[];
}

// Latest prediction types
export interface LatestPrediction {
  symbol: string;
  date: string;
  score: number;
  signal: string;
  positive_factors: string[];
  negative_factors: string[];
  risk_flags: string[];
}

