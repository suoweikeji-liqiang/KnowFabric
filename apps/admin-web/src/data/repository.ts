import {
  documents,
  equipmentCoverage,
  knowledgeAssets,
  publishRecords,
  reviewCandidates,
  reviewPacks,
} from "./mockData";
import {
  DocumentRecord,
  EquipmentCoverage,
  KnowledgeAsset,
  PublishRecord,
  ReviewCandidate,
  ReviewPack,
} from "../types";

export function listKnowledgeAssets(): KnowledgeAsset[] {
  return knowledgeAssets.slice();
}

export function listDocuments(): DocumentRecord[] {
  return documents.slice();
}

export function listEquipmentCoverage(): EquipmentCoverage[] {
  return equipmentCoverage.slice();
}

export function listReviewPacks(): ReviewPack[] {
  return reviewPacks.slice();
}

export function listReviewCandidates(): ReviewCandidate[] {
  return reviewCandidates.slice();
}

export function listPublishRecords(): PublishRecord[] {
  return publishRecords.slice();
}

export function getRelatedDocumentsForAsset(asset: KnowledgeAsset | null): DocumentRecord[] {
  if (!asset) {
    return [];
  }
  return documents.filter((doc) => asset.evidence.some((item) => item.docId === doc.id));
}

export function getLinkedAssetsForDocument(document: DocumentRecord | null): KnowledgeAsset[] {
  if (!document) {
    return [];
  }
  return knowledgeAssets.filter((asset) => document.linkedAssetIds.includes(asset.id));
}

export function getCoverageDocuments(item: EquipmentCoverage | null): DocumentRecord[] {
  if (!item) {
    return [];
  }
  return documents.filter((doc) => item.relatedDocumentIds.includes(doc.id));
}

export function getCoverageAssets(item: EquipmentCoverage | null): KnowledgeAsset[] {
  if (!item) {
    return [];
  }
  return knowledgeAssets.filter((asset) => item.relatedAssetIds.includes(asset.id));
}

export function getReviewCandidatesForPack(pack: ReviewPack | null): ReviewCandidate[] {
  if (!pack) {
    return [];
  }
  return reviewCandidates.filter((candidate) => pack.candidateIds.includes(candidate.id));
}

export function getLinkedReviewPacks(record: PublishRecord | null): ReviewPack[] {
  if (!record) {
    return [];
  }
  return reviewPacks.filter((pack) => record.linkedPackIds.includes(pack.id));
}
