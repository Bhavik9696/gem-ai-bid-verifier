"use client";
import { usePathname } from "next/navigation";

const TITLES: Record<string, { title: string; subtitle: string }> = {
  "/dashboard": { title: "Dashboard", subtitle: "Real-time insights for faster, fairer and more transparent procurement." },
  "/tenders": { title: "Tenders", subtitle: "Manage and evaluate tenders imported from GeM." },
  "/tenders/import": { title: "Import Tender", subtitle: "Import tender and bidder data into ComplianceOS." },
  "/tenders/rules": { title: "Tender Rules", subtitle: "Versioned rulebooks for compliance evaluation." },
  "/bidders": { title: "Bidders", subtitle: "Review bidder profiles, compliance scores, and risks." },
  "/documents": { title: "Document Intelligence", subtitle: "AI-powered OCR extraction and document classification." },
  "/verification": { title: "Verification Center", subtitle: "Source connector results across all government registries." },
  "/conflicts": { title: "Conflict Detection", subtitle: "Detected mismatches and anomalies requiring review." },
  "/compliance": { title: "Compliance Rules", subtitle: "Tender-specific rule evaluation results." },
  "/recommendations": { title: "AI Recommendations", subtitle: "Evidence-backed compliance recommendations." },
  "/clarifications": { title: "Clarifications", subtitle: "Bidders requiring additional evidence or clarification." },
  "/review": { title: "Officer Review", subtitle: "Confirm, clarify, or override compliance decisions." },
  "/audit": { title: "Audit Trail", subtitle: "Immutable timeline of all verification and decision events." },
  "/reports": { title: "Reports", subtitle: "Generate and export tender compliance reports." },
  "/admin/connectors": { title: "Connector Status", subtitle: "Monitor source connector health and modes." },
  "/admin/users": { title: "Users & Roles", subtitle: "Role-based access management." },
  "/settings": { title: "Settings", subtitle: "Platform configuration and preferences." },
};

export default function TopBar() {
  const pathname = usePathname();
  const info = TITLES[pathname] ?? { title: "ComplianceOS", subtitle: "GeM AI Bid Verifier" };
  const now = new Date();
  const updated = now.toLocaleString("en-IN", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });

  return (
    <header className="topbar">
      <div className="topbar-left">
        <div>
          <div className="topbar-title">{info.title}</div>
          <div style={{ fontSize: 12, color: "#64748b" }}>{info.subtitle}</div>
        </div>
      </div>
      <div className="topbar-right">
        <div style={{ fontSize: 11, color: "#64748b", display: "flex", alignItems: "center", gap: 6 }}>
          <span>📅</span> Last Updated: {updated}
        </div>
        <div className="system-status">
          <span className="status-dot" />
          System Online
        </div>
        {/* GeM logo area */}
        <div style={{ display: "flex", alignItems: "center", gap: 6, padding: "4px 10px", background: "#f8fafc", borderRadius: 8, border: "1px solid #e2e8f0" }}>
          <span style={{ fontSize: 14 }}>🇮🇳</span>
          <span style={{ fontSize: 11, fontWeight: 700, color: "#0f172a" }}>GeM</span>
        </div>
        <div className="topbar-badge">
          <span className="demo-dot" />
          DEMO MODE
        </div>
        <div className="avatar" title="Officer Sharma">OS</div>
      </div>
    </header>
  );
}
