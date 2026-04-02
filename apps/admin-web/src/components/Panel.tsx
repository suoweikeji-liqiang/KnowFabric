import { ReactNode } from "react";

interface PanelProps {
  title: string;
  meta?: string;
  actions?: ReactNode;
  children: ReactNode;
  compact?: boolean;
}

export function Panel({ title, meta, actions, children, compact = false }: PanelProps) {
  return (
    <section className={`panel ${compact ? "panel-compact" : ""}`}>
      <header className="panel-header">
        <div>
          <p className="panel-kicker">{title}</p>
          {meta ? <p className="panel-meta">{meta}</p> : null}
        </div>
        {actions ? <div className="panel-actions">{actions}</div> : null}
      </header>
      <div className="panel-body">{children}</div>
    </section>
  );
}
