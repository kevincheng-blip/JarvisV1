/**
 * Doctrine Alert Types
 * 
 * TypeScript type definitions for Doctrine alerts.
 */

export type DoctrineAlertSeverity = "info" | "warning" | "critical";

export type DoctrineAlertSource = "position" | "prediction" | "conflict" | "error";

export type DoctrineRef = {
  book_id: string;
  section_id: string;
  rule_id?: string | null;
};

export type DoctrineAlertItem = {
  id: string;
  symbol: string;
  name?: string | null;
  severity: DoctrineAlertSeverity;
  source: DoctrineAlertSource;
  title: string;
  message: string;
  metric_name: string;
  metric_value?: number | null;
  threshold?: number | null;
  conflict_score?: number | null;
  consensus_score?: number | null;
  final_score?: number | null;
  raw_score?: number | null;
  doctrine_refs: DoctrineRef[];
  tags: string[];
  created_at: string;
};

