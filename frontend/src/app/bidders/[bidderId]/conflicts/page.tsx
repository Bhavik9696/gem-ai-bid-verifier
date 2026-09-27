import Link from "next/link";
import { DEMO_BIDDERS, DEMO_CONFLICTS } from "@/lib/mockData";
import { notFound } from "next/navigation";

export default function ConflictsPage({ params }: { params: { bidderId: string } }) {
  const bidder = DEMO_BIDDERS.find(b => b.id === params.bidderId);
  if (!bidder) return notFound();
  const conflicts = DEMO_CONFLICTS[params.bidderId as keyof typeof DEMO_CONFLICTS] ?? [];

  return (
    <>
      <div className="demo-banner">⚠️ Demo Mode · {bidder.legalName} · {bidder.id}</div>
      <div style={{ marginBottom: 16, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <Link href={`/bidders/${bidder.id}`} style={{ fontSize: 12, color: "#1a56db" }}>← Back to Profile</Link>
        <div style={{ display: "flex", gap: 8 }}>
          <span className="badge badge-red">Conflicts: {conflicts.length}</span>
          <span className="badge badge-gray">Bidder: {bidder.legalName}</span>
        </div>
      </div>

      {conflicts.length === 0 ? (
        <div className="card" style={{ textAlign: "center", padding: 48 }}>
          <div style={{ fontSize: 48, marginBottom: 12 }}>✅</div>
          <h3 style={{ fontSize: 18, fontWeight: 700, color: "#059669", margin: "0 0 8px" }}>No Conflicts Detected</h3>
          <p style={{ color: "#64748b" }}>All entity identities match across source connectors. No anomalies found.</p>
        </div>
      ) : (
        <>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 12, marginBottom: 20 }}>
            {[
              { label: "Total Conflicts", value: conflicts.length, color: "#dc2626", bg: "#fef2f2" },
              { label: "Severity", value: conflicts.some(c => c.severity === "high") ? "HIGH" : "MEDIUM", color: "#dc2626", bg: "#fef2f2" },
              { label: "Recommendation", value: "Officer Review", color: "#7c3aed", bg: "#fdf4ff" },
            ].map(c => (
              <div key={c.label} style={{ background: c.bg, border: `1px solid ${c.color}22`, borderRadius: 10, padding: "14px 18px" }}>
                <div style={{ fontSize: 11, color: c.color, fontWeight: 700 }}>{c.label}</div>
                <div style={{ fontSize: 20, fontWeight: 900, color: c.color }}>{c.value}</div>
              </div>
            ))}
          </div>

          {conflicts.map(c => (
            <div key={c.id} className={`conflict-card ${c.severity}`}>
              <div className="conflict-header">
                <div className="conflict-title">
                  {c.severity === "high" ? "🔴" : "🟠"} {c.title}
                </div>
                <div style={{ display: "flex", gap: 8 }}>
                  <span className={`badge ${c.severity === "high" ? "badge-red" : "badge-yellow"}`}>{c.severity.toUpperCase()}</span>
                  <span className="badge badge-yellow">{c.mode}</span>
                </div>
              </div>
              <p style={{ fontSize: 13, color: "#374151", margin: "8px 0", lineHeight: 1.5 }}>{c.description}</p>
              <div className="conflict-body">
                <div className="conflict-side">
                  <div className="conflict-side-label">📄 Bidder Submission</div>
                  <div className="conflict-side-val">{c.bidSubmission}</div>
                </div>
                <div className="conflict-side">
                  <div className="conflict-side-label">🏛️ Source Record ({c.source})</div>
                  <div className="conflict-side-val" style={{ color: "#dc2626" }}>{c.sourceRecord}</div>
                </div>
              </div>
              <div style={{ marginTop: 12, display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
                <span style={{ fontSize: 11, color: "#64748b" }}>Evidence: {c.evidence}</span>
                <span style={{ fontSize: 11, color: "#64748b" }}>·</span>
                <span style={{ fontSize: 11, color: "#64748b" }}>Rule: <code style={{ background: "#f1f5f9", padding: "1px 5px", borderRadius: 3 }}>{c.relatedRule}</code></span>
              </div>
              <div style={{ marginTop: 10, background: "#fff7ed", border: "1px solid #fed7aa", borderRadius: 6, padding: "8px 12px", fontSize: 12, color: "#92400e" }}>
                💡 {c.recommendation}
              </div>
            </div>
          ))}
        </>
      )}
    </>
  );
}
