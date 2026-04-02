import { ReactNode } from "react";
import { NavLink, useLocation } from "react-router-dom";

import { NavItem } from "../types";

interface ShellProps {
  navItems: NavItem[];
  children: ReactNode;
}

export function Shell({ navItems, children }: ShellProps) {
  const location = useLocation();
  const current = navItems.find((item) => item.path === location.pathname) ?? navItems[0];

  return (
    <div className="admin-shell">
      <aside className="sidebar">
        <div className="brand-block">
          <div className="brand-mark">KF</div>
          <div>
            <p className="eyebrow">KnowFabric</p>
            <h2>知识资产管理后台</h2>
          </div>
        </div>
        <nav className="sidebar-nav" aria-label="主导航">
          {navItems.map((item) => (
            <NavLink key={item.path} to={item.path} className={({ isActive }) => `nav-link ${isActive ? "is-active" : ""}`}>
              <strong>{item.label}</strong>
              {item.badge ? <span className="nav-badge">{item.badge}</span> : null}
            </NavLink>
          ))}
        </nav>
      </aside>

      <section className="main-shell">
        <header className="topbar">
          <div className="topbar-title">
            <h3>{current.label}</h3>
          </div>
          <div className="topbar-search">
            <input
              aria-label="全局搜索"
              placeholder="搜索文档、设备类、知识对象或 Chunk ID"
              type="search"
            />
          </div>
          <div className="topbar-meta">
            <button className="user-chip" type="button">
              Lin
            </button>
          </div>
        </header>
        <main className="page-slot">{children}</main>
      </section>
    </div>
  );
}
