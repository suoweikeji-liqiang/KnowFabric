import {
  CoverageStatus,
  DocumentStatus,
  DomainId,
  KnowledgeType,
  PackStatus,
  PublishStatus,
  ReleaseStatus,
  ReviewStatus,
} from "../types";

export const domainLabels: Record<DomainId, string> = {
  hvac: "暖通空调",
  drive: "变频驱动",
};

export const knowledgeTypeLabels: Record<KnowledgeType, string> = {
  fault_code: "故障代码",
  parameter_spec: "参数规范",
  application_guidance: "应用指导",
  maintenance_procedure: "维护流程",
  performance_spec: "性能规范",
  symptom: "症状",
  diagnostic_step: "诊断步骤",
  commissioning_step: "调试步骤",
  wiring_guidance: "接线指导",
};

export const reviewStatusLabels: Record<ReviewStatus, string> = {
  pending: "待审阅",
  accepted: "已接受",
  rejected: "已拒绝",
  review_ready: "可复核",
};

export const publishStatusLabels: Record<PublishStatus, string> = {
  draft: "草稿",
  reviewed: "已审阅",
  published: "已发布",
  archived: "已归档",
};

export const documentStatusLabels: Record<DocumentStatus, string> = {
  imported: "已导入",
  parsed: "已解析",
  chunked: "已切块",
  failed: "失败",
};

export const sourceTypeLabels = {
  manual: "内部手册",
  vendor: "厂商资料",
  authority: "权威资料",
} as const;

export const coverageStatusLabels: Record<CoverageStatus, string> = {
  covered: "已覆盖",
  partial: "部分覆盖",
  thin: "覆盖偏薄",
  missing: "未覆盖",
};

export const packStatusLabels: Record<PackStatus, string> = {
  pending: "待处理",
  ready: "已就绪",
  blocked: "被阻塞",
};

export const releaseStatusLabels: Record<ReleaseStatus, string> = {
  success: "成功",
  partial: "部分失败",
  failed: "失败",
};
