import { HashRouter, Navigate, Route, Routes } from "react-router-dom";

import { Shell } from "./components/Shell";
import { DomainAssetsPage } from "./pages/DomainAssetsPage";
import { DocumentsPage } from "./pages/DocumentsPage";
import { KnowledgeAssetsPage } from "./pages/KnowledgeAssetsPage";
import { PublishRecordsPage } from "./pages/PublishRecordsPage";
import { ReviewCenterPage } from "./pages/ReviewCenterPage";
import { NavItem } from "./types";

const navItems: NavItem[] = [
  {
    path: "/knowledge-assets",
    label: "知识成果",
  },
  {
    path: "/documents",
    label: "文档管理",
  },
  {
    path: "/domain-assets",
    label: "领域资产",
  },
  {
    path: "/review-center",
    label: "审阅中心",
  },
  {
    path: "/publish-records",
    label: "发布记录",
  },
];

export default function App() {
  return (
    <HashRouter>
      <Shell navItems={navItems}>
        <Routes>
          <Route path="/" element={<Navigate replace to="/knowledge-assets" />} />
          <Route path="/knowledge-assets" element={<KnowledgeAssetsPage />} />
          <Route path="/documents" element={<DocumentsPage />} />
          <Route path="/domain-assets" element={<DomainAssetsPage />} />
          <Route path="/review-center" element={<ReviewCenterPage />} />
          <Route path="/publish-records" element={<PublishRecordsPage />} />
        </Routes>
      </Shell>
    </HashRouter>
  );
}
