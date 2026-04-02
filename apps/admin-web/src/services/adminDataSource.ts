import {
  listKnowledgeAssets,
  getRelatedDocumentsForAsset,
} from "../data/repository";
import {
  DocumentRecord,
  EquipmentCoverage,
  KnowledgeAsset,
  PublishRecord,
  ReviewCandidate,
  ReviewPack,
} from "../types";
import { fetchJson } from "./http";

export interface KnowledgeAssetsSnapshot {
  assets: KnowledgeAsset[];
  relatedDocumentsForAsset: (asset: KnowledgeAsset | null) => DocumentRecord[];
}

export interface DocumentsSnapshot {
  documents: DocumentRecord[];
  linkedAssetsForDocument: (document: DocumentRecord | null) => KnowledgeAsset[];
}

export interface DomainAssetsSnapshot {
  coverage: EquipmentCoverage[];
  documentsForCoverage: (item: EquipmentCoverage | null) => DocumentRecord[];
  assetsForCoverage: (item: EquipmentCoverage | null) => KnowledgeAsset[];
}

export interface ReviewCenterSnapshot {
  workspaceId?: string;
  packs: ReviewPack[];
  candidates: ReviewCandidate[];
  candidatesForPack: (pack: ReviewPack | null) => ReviewCandidate[];
}

export interface PublishRecordsSnapshot {
  workspaceId?: string;
  latestRecordId?: string | null;
  records: PublishRecord[];
  linkedPacksForRecord: (record: PublishRecord | null) => ReviewPack[];
}

export interface AdminDataSource {
  getKnowledgeAssetsSnapshot(): Promise<KnowledgeAssetsSnapshot>;
  getDocumentsSnapshot(): Promise<DocumentsSnapshot>;
  getDomainAssetsSnapshot(): Promise<DomainAssetsSnapshot>;
  getReviewCenterSnapshot(): Promise<ReviewCenterSnapshot>;
  getPublishRecordsSnapshot(): Promise<PublishRecordsSnapshot>;
}

interface ConsoleKnowledgeAssetsResponse {
  assets: KnowledgeAsset[];
  relatedDocumentsByAsset: Record<string, DocumentRecord[]>;
}

interface ConsoleDocumentsResponse {
  documents: DocumentRecord[];
  linkedAssetsByDocument: Record<string, KnowledgeAsset[]>;
}

interface ConsoleDomainAssetsResponse {
  coverage: EquipmentCoverage[];
  documentsByCoverage: Record<string, DocumentRecord[]>;
  assetsByCoverage: Record<string, KnowledgeAsset[]>;
}

interface ConsoleReviewCenterResponse {
  workspaceId?: string;
  packs: ReviewPack[];
  candidates: ReviewCandidate[];
  candidatesByPack: Record<string, ReviewCandidate[]>;
}

interface ConsolePublishRecordsResponse {
  workspaceId?: string;
  latestRecordId?: string | null;
  records: PublishRecord[];
  linkedPacksByRecord: Record<string, ReviewPack[]>;
}

function createMockAdminDataSource(): AdminDataSource {
  return {
    async getKnowledgeAssetsSnapshot() {
      return {
        assets: listKnowledgeAssets(),
        relatedDocumentsForAsset: getRelatedDocumentsForAsset,
      };
    },
    async getDocumentsSnapshot() {
      throw new Error("未配置 mock documents 数据源");
    },
    async getDomainAssetsSnapshot() {
      throw new Error("未配置 mock domain assets 数据源");
    },
    async getReviewCenterSnapshot() {
      throw new Error("未配置 mock review center 数据源");
    },
    async getPublishRecordsSnapshot() {
      throw new Error("未配置 mock publish records 数据源");
    },
  };
}

function createBackendAdminDataSource(): AdminDataSource {
  return {
    async getKnowledgeAssetsSnapshot() {
      const payload = await fetchJson<ConsoleKnowledgeAssetsResponse>("/api/console/knowledge-assets");
      return {
        assets: payload.assets,
        relatedDocumentsForAsset: (asset) => (asset ? payload.relatedDocumentsByAsset[asset.id] || [] : []),
      };
    },
    async getDocumentsSnapshot() {
      const payload = await fetchJson<ConsoleDocumentsResponse>("/api/console/documents");
      return {
        documents: payload.documents,
        linkedAssetsForDocument: (document) =>
          document ? payload.linkedAssetsByDocument[document.id] || [] : [],
      };
    },
    async getDomainAssetsSnapshot() {
      const payload = await fetchJson<ConsoleDomainAssetsResponse>("/api/console/domain-assets");
      return {
        coverage: payload.coverage,
        documentsForCoverage: (item) => (item ? payload.documentsByCoverage[item.id] || [] : []),
        assetsForCoverage: (item) => (item ? payload.assetsByCoverage[item.id] || [] : []),
      };
    },
    async getReviewCenterSnapshot() {
      const payload = await fetchJson<ConsoleReviewCenterResponse>("/api/console/review-center");
      return {
        workspaceId: payload.workspaceId,
        packs: payload.packs,
        candidates: payload.candidates,
        candidatesForPack: (pack) => (pack ? payload.candidatesByPack[pack.id] || [] : []),
      };
    },
    async getPublishRecordsSnapshot() {
      const payload = await fetchJson<ConsolePublishRecordsResponse>("/api/console/publish-records");
      return {
        workspaceId: payload.workspaceId,
        latestRecordId: payload.latestRecordId,
        records: payload.records,
        linkedPacksForRecord: (record) => (record ? payload.linkedPacksByRecord[record.id] || [] : []),
      };
    },
  };
}

let singleton: AdminDataSource | null = null;

export function getAdminDataSource(): AdminDataSource {
  if (!singleton) {
    const sourceMode = import.meta.env.VITE_ADMIN_DATA_SOURCE;
    singleton = sourceMode === "mock" ? createMockAdminDataSource() : createBackendAdminDataSource();
  }
  return singleton;
}
