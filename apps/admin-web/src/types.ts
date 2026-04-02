import { ReactNode } from "react";

export type DomainId = "hvac" | "drive";

export type KnowledgeType =
  | "fault_code"
  | "parameter_spec"
  | "application_guidance"
  | "maintenance_procedure"
  | "performance_spec"
  | "symptom"
  | "diagnostic_step"
  | "commissioning_step"
  | "wiring_guidance";

export type ReviewStatus = "pending" | "accepted" | "rejected" | "review_ready";

export type PublishStatus = "draft" | "reviewed" | "published" | "archived";

export type DocumentStatus = "imported" | "parsed" | "chunked" | "failed";

export type CoverageStatus = "covered" | "partial" | "thin" | "missing";

export type PackStatus = "pending" | "ready" | "blocked";

export type ReleaseStatus = "success" | "partial" | "failed";

export interface EvidenceCitation {
  docId: string;
  documentName: string;
  pageNo: number;
  chunkId: string;
  excerpt: string;
  evidenceText: string;
}

export interface KnowledgeAsset {
  id: string;
  title: string;
  canonicalKey: string;
  domainId: DomainId;
  equipmentClass: string;
  equipmentClassLabel?: string;
  type: KnowledgeType;
  reviewStatus: ReviewStatus;
  publishStatus: PublishStatus;
  sourceDocument: string;
  updatedAt: string;
  summary: string;
  trustLevel: string;
  applicability: string[];
  payload: string;
  displayLanguage?: string;
  evidence: EvidenceCitation[];
  relatedAssets: string[];
}

export interface DocumentRecord {
  id: string;
  fileName: string;
  domainId: DomainId;
  equipmentClasses: string[];
  equipmentClassLabels?: string[];
  status: DocumentStatus;
  pageCount: number;
  chunkCount: number;
  importedAt: string;
  sourceType: "manual" | "vendor" | "authority";
  stageSummary: string;
  stageTimeline: string[];
  pageNotes: string[];
  chunkHighlights: string[];
  linkedAssetIds: string[];
  prepareTargets?: Array<{
    domainId: DomainId;
    equipmentClassId: string;
    equipmentClassLabel: string;
    anchorCount: number;
  }>;
}

export interface EquipmentCoverage {
  id: string;
  label: string;
  domainId: DomainId;
  status: CoverageStatus;
  coveredTypes: KnowledgeType[];
  missingTypes: KnowledgeType[];
  assetCount: number;
  documentCount: number;
  updatedAt: string;
  summary: string;
  relatedDocumentIds: string[];
  relatedAssetIds: string[];
}

export interface ReviewCandidate {
  id: string;
  packId?: string;
  workspaceId?: string;
  title: string;
  canonicalKey: string;
  type: KnowledgeType;
  status: ReviewStatus;
  pageNo: number;
  chunkId: string;
  summary: string;
  trustLevel: string;
  payload: string;
  evidence: EvidenceCitation;
  sourceDocument: string;
}

export interface ReviewPack {
  id: string;
  name: string;
  domainId: DomainId;
  equipmentClass: string;
  equipmentClassLabel?: string;
  status: PackStatus;
  updatedAt: string;
  candidateIds: string[];
  acceptedCount?: number;
  pendingCount?: number;
  rejectedCount?: number;
  workspaceId?: string;
}

export interface ReleaseItem {
  name: string;
  type: string;
  result: "success" | "failed";
  note: string;
  packId?: string;
  knowledgeObjectId?: string | null;
  canonicalKey?: string | null;
  docId?: string | null;
  docName?: string | null;
  equipmentClassId?: string | null;
  equipmentClassLabel?: string | null;
}

export interface PublishRecord {
  id: string;
  recordMode?: "apply_run" | "workspace_snapshot";
  workspaceId?: string;
  executedAt: string;
  domainId: DomainId;
  status: ReleaseStatus;
  successCount: number;
  failureCount: number;
  workspace: string;
  operator: string;
  summary: string;
  detailsText?: string | null;
  artifactPaths?: Record<string, string | undefined>;
  items: ReleaseItem[];
  errors: string[];
  linkedPackIds: string[];
}

export interface NavItem {
  path: string;
  label: string;
  badge?: string;
}

export interface TabDefinition {
  id: string;
  label: string;
  content: ReactNode;
}
