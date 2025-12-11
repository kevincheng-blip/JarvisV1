/**
 * Doctrine Patch Types
 * 
 * TypeScript type definitions for Doctrine Patch & Rollout system.
 */

export type PatchStatus = 
  | "PENDING_SIMULATION"
  | "REJECTED_BY_SIM"
  | "PENDING_REVIEW"
  | "APPROVED"
  | "DEPLOYING"
  | "DEPLOYED"
  | "REVERTED";

export type RuleSimStatus = "PENDING" | "APPROVED" | "REJECTED";

export type ChangeType = "ADD" | "UPDATE" | "DELETE";

export type DoctrineChangeItem = {
  change_type: ChangeType;
  section_id: string;
  old_content?: string | null;
  new_content?: string | null;
};

export type DoctrinePatch = {
  patch_id: string;
  created_at: string;
  author_id: string;
  description: string;
  changes: DoctrineChangeItem[];
  status: PatchStatus;
  rule_sim_report_id?: string | null;
  sim_status: RuleSimStatus;
  deployment_version?: number | null;
  deployed_at?: string | null;
  pre_deployment_version?: number | null;
  reviewer_id?: string | null;
  reviewed_at?: string | null;
  reverted_by?: string | null;
  reverted_at?: string | null;
};

export type DoctrinePatchSummary = {
  patch_id: string;
  status: PatchStatus;
  created_at: string;
  author_id: string;
  description: string;
  sim_status: RuleSimStatus;
  rule_sim_report_id?: string | null;
};

export type CreateDoctrinePatchRequest = {
  author_id: string;
  description: string;
  changes: DoctrineChangeItem[];
};

export type ApprovePatchRequest = {
  reviewer_id: string;
  comment?: string | null;
};

export type RejectPatchRequest = {
  reviewer_id: string;
  comment?: string | null;
};

export type DeployPatchRequest = {
  operator_id: string;
};

export type RevertPatchRequest = {
  operator_id: string;
};
