"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { section: null, items: [{ href: "/dashboard", label: "Dashboard", icon: "🏠" }] },
  {
    section: "Tenders",
    items: [
      { href: "/tenders", label: "All Tenders", icon: "📋" },
      { href: "/tenders/import", label: "Import Tender", icon: "⬆️" },
      { href: "/tenders/rules", label: "Tender Rules", icon: "📐" },
    ],
  },
  {
    section: "Evaluation",
    items: [
      { href: "/bidders", label: "Bidders", icon: "👥" },
      { href: "/documents", label: "Documents", icon: "📄" },
      { href: "/verification", label: "Verification", icon: "🔍" },
      { href: "/conflicts", label: "Conflicts", icon: "⚠️" },
      { href: "/compliance", label: "Compliance", icon: "✅" },
    ],
  },
  {
    section: "Decision",
    items: [
      { href: "/recommendations", label: "Recommendations", icon: "🤖" },
      { href: "/clarifications", label: "Clarifications", icon: "💬" },
      { href: "/review", label: "Officer Review", icon: "👨‍⚖️" },
    ],
  },
  {
    section: "Reporting",
    items: [
      { href: "/audit", label: "Audit Trail", icon: "📅" },
      { href: "/reports", label: "Reports", icon: "📊" },
    ],
  },
  {
    section: "Admin",
    items: [
      { href: "/admin/connectors", label: "Connectors", icon: "🔌" },
      { href: "/admin/users", label: "Users & Roles", icon: "👤" },
      { href: "/settings", label: "Settings", icon: "⚙️" },
    ],
  },
];

export default function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="sidebar">
      {/* Brand */}
      <div className="sidebar-brand">
        <div className="brand-icon">🛡️</div>
        <div className="brand-text">
          <div className="brand-title">ComplianceOS</div>
          <div className="brand-sub">GeM Bid Verifier</div>
        </div>
      </div>

      {/* GeM Badge */}
      <div className="gem-badge">
        <span className="gem-badge-emblem">🇮🇳</span>
        <div className="gem-badge-text">
          <div className="gem-badge-title">Government of India</div>
          <div className="gem-badge-sub">GeM · Government e-Marketplace</div>
        </div>
      </div>

      {/* Nav */}
      <nav style={{ flex: 1 }}>
        {NAV.map((group, gi) => (
          <div key={gi} className="nav-section">
            {group.section && (
              <div className="nav-section-label">{group.section}</div>
            )}
            {group.items.map((item) => {
              const active =
                pathname === item.href ||
                (item.href !== "/dashboard" && pathname.startsWith(item.href));
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`nav-item${active ? " active" : ""}`}
                >
                  <span className="nav-icon">{item.icon}</span>
                  {item.label}
                </Link>
              );
            })}
          </div>
        ))}
      </nav>

      {/* Footer tagline */}
      <div className="sidebar-footer">
        <div className="sidebar-tagline">
          Better Decisions.<br />
          <span>Greater Impact.</span>
        </div>
      </div>
    </aside>
  );
}
