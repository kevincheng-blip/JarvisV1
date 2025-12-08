/**
 * Error Review Types
 * 
 * Type definitions for Error Review API and components.
 */

export interface DoctrineHitLite {
  book_id: string;
  section_id: string;
  summary: string | null;
  core_principles: string[] | null;
  risk_rules: string[] | null;
  tags: string[] | null;
}

export interface ErrorReviewItem {
  id: string;
  timestamp: string; // ISO datetime string
  symbol: string;
  error_type: string | null;
  pnl_impact: number | null;
  human_summary: string | null;
  doctrine_hits: DoctrineHitLite[];
  classification: string;
  timeframe: string | null;
  side: string | null;
  predicted_outcome: string | null;
  actual_outcome: string | null;
}

export interface ErrorReviewParams {
  startDate?: string; // YYYY-MM-DD
  endDate?: string; // YYYY-MM-DD
  symbol?: string;
  errorType?: string;
  limit?: number;
}

