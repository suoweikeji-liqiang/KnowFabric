import { ReactNode } from "react";

interface TabsProps {
  tabs: { id: string; label: string; content: ReactNode }[];
  activeTab: string;
  onChange: (tabId: string) => void;
}

export function Tabs({ tabs, activeTab, onChange }: TabsProps) {
  const current = tabs.find((tab) => tab.id === activeTab) ?? tabs[0];

  return (
    <div className="tabs-shell">
      <div className="tabs-nav" role="tablist" aria-label="详情分组">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            className={`tab-trigger ${tab.id === current.id ? "is-active" : ""}`}
            onClick={() => onChange(tab.id)}
            role="tab"
            type="button"
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div className="tabs-content">{current.content}</div>
    </div>
  );
}
