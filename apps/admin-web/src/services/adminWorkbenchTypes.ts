import { DomainId, KnowledgeType } from "../types";

export type ReviewDecision = "accepted" | "rejected" | "pending";

export interface ReviewPackCurationPayload {
  title?: string;
  summary?: string;
  canonical_key?: string;
  structured_payload?: Record<string, unknown>;
  applicability?: Record<string, unknown>;
  trust_level?: string;
  review_status?: string;
  evidence_text?: string;
  evidence_role?: string;
}

export interface ReviewPackCandidateEntry {
  candidate_id: string;
  knowledge_object_type?: KnowledgeType;
  canonical_key_candidate?: string;
  page_no?: number;
  chunk_id?: string;
  text_excerpt?: string;
  evidence_text?: string;
  review_decision?: ReviewDecision;
  curation?: ReviewPackCurationPayload;
}

export interface ReviewPackDetail {
  workspace_id?: string;
  domain_id?: DomainId;
  doc_id?: string;
  doc_name?: string;
  candidate_entries: ReviewPackCandidateEntry[];
  review_summary?: {
    accepted_count?: number;
    rejected_count?: number;
    pending_count?: number;
    status?: string;
  };
}

export interface RunApplyReadyResult {
  workspace_id?: string;
  publish_record_id?: string;
  generated_at?: string;
  summary?: {
    applied?: number;
    failed?: number;
  };
}
