/**
 * Doctrine Service V2 Types
 * 
 * TypeScript type definitions for Doctrine Management Console.
 */

export type SectionStatus = "APPROVED" | "DRAFT" | "PENDING_REVIEW" | "DEPRECATED";

export type ChangeType = "CREATE" | "UPDATE" | "APPROVE" | "REJECT" | "ROLLBACK";

export type SectionRevision = {
  version_id: string;
  timestamp: string;
  operator: string;
  change_type: ChangeType;
  content?: string | null;
  metadata: Record<string, any>;
};

export type DoctrineSection = {
  section_id: string;
  title: string;
  current_version_id: string;
  draft_version_id?: string | null;
  status: SectionStatus;
  created_at: string;
  updated_at: string;
  revision_history: SectionRevision[];
  source: string; // "manual" or "self-repair"
  severity?: string | null;
  metadata: Record<string, any>;
};

export type SectionsResponse = {
  sections: DoctrineSection[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
};

export type VersionContentResponse = {
  section_id: string;
  version_id: string;
  content: string;
};

export type DiffResponse = {
  diff: string;
  from_version_id: string;
  to_version_id: string;
};

