import { ReactNode } from "react";

interface MasterDetailPageProps {
  title: string;
  description?: string;
  actions?: ReactNode;
  filters?: ReactNode;
  leftPane: ReactNode;
  rightPane: ReactNode;
  footer?: ReactNode;
  split: string;
}

export function MasterDetailPage({
  title,
  description,
  actions,
  filters,
  leftPane,
  rightPane,
  footer,
  split,
}: MasterDetailPageProps) {
  return (
    <div className="page-screen">
      {(actions || filters) ? (
        <section className="page-controls">
          {filters ? <div className="filter-bar">{filters}</div> : null}
          {actions ? <div className="header-actions">{actions}</div> : null}
        </section>
      ) : null}
      <section className="workspace-grid" style={{ gridTemplateColumns: split }}>
        <div className="workspace-column">{leftPane}</div>
        <div className="workspace-column">{rightPane}</div>
      </section>
      {footer ? <footer className="page-footer">{footer}</footer> : null}
    </div>
  );
}
