import { ReactNode } from "react";

type StatusTone =
  | "neutral"
  | "pending"
  | "success"
  | "warning"
  | "danger"
  | "cool";

interface StatusBadgeProps {
  label: ReactNode;
  tone: StatusTone;
}

export function StatusBadge({ label, tone }: StatusBadgeProps) {
  return <span className={`status-badge status-${tone}`}>{label}</span>;
}
