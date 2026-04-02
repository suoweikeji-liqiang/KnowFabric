import { fetchJson } from "./http";
import type { ReviewPackDetail, RunApplyReadyResult } from "./adminWorkbenchTypes";

function withWorkspace(path: string, workspaceId?: string): string {
  if (!workspaceId) {
    return path;
  }
  const separator = path.includes("?") ? "&" : "?";
  return `${path}${separator}workspace_id=${encodeURIComponent(workspaceId)}`;
}

export async function parseDocument(docId: string): Promise<unknown> {
  return fetchJson(`/api/workbench/documents/${encodeURIComponent(docId)}/parse`, {
    method: "POST",
  });
}

export async function chunkDocument(docId: string): Promise<unknown> {
  return fetchJson(`/api/workbench/documents/${encodeURIComponent(docId)}/chunk`, {
    method: "POST",
  });
}

export async function runApplyReady(workspaceId?: string): Promise<RunApplyReadyResult> {
  return fetchJson(withWorkspace("/api/workbench/apply/run", workspaceId), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(workspaceId ? { workspace_id: workspaceId } : {}),
  });
}

export async function fetchReviewPack(packFile: string, workspaceId?: string): Promise<ReviewPackDetail> {
  return fetchJson(withWorkspace(`/api/workbench/review-packs/${encodeURIComponent(packFile)}`, workspaceId));
}

export async function saveReviewPack(
  packFile: string,
  payload: ReviewPackDetail,
  workspaceId?: string,
): Promise<ReviewPackDetail> {
  return fetchJson(withWorkspace(`/api/workbench/review-packs/${encodeURIComponent(packFile)}`, workspaceId), {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(workspaceId ? { ...payload, workspace_id: workspaceId } : payload),
  });
}

export async function bootstrapReviewPack(packFile: string, workspaceId?: string): Promise<ReviewPackDetail> {
  return fetchJson(withWorkspace(`/api/workbench/review-packs/${encodeURIComponent(packFile)}/bootstrap`, workspaceId), {
    method: "POST",
  });
}

export async function prepareReviewBundle(payload: {
  domain_id: string;
  doc_id: string;
  equipment_class_id?: string | null;
}): Promise<{
  workspace_id?: string;
  review_workspace?: {
    packs?: Array<{
      pack_file?: string;
    }>;
  };
}> {
  return fetchJson("/api/workbench/review-bundle/prepare", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}
