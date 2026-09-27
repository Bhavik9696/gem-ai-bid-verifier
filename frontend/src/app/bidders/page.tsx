import Link from "next/link";
import { DEMO_BIDDERS } from "@/lib/mockData";

const RISK_CONF: Record<string, { cls: string; dot: string }> = {
  Low: { cls: "risk-low", dot: "#10b981" },
  High: { cls: "risk-high", dot: "#ef4444" },
  Critical: { cls: "risk-critical", dot: "#7c3aed" },
};

export default function BiddersPage() {
  return (
    <>
      <div className="demo-banner">⚠️ Demo Mode — Showing bidders for tender GEM/2025/B/47821</div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 800, color: "#0f172a", margin: 0 }}>Bidders</h1>
          <p style={{ fontSize: 13, color: "#64748b", margin: "4px 0 0" }}>Tender: Supply of IT Equipment · GEM/2025/B/47821</p>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          <span className="badge badge-gray">Bids: 3</span>
          <span className="badge badge-green">Ready: 1</span>
          <span className="badge badge-yellow">Review: 1</span>
          <span className="badge badge-red">Critical: 1</span>
        </div>
      </div>

      <div className="filter-bar">
        {["All", "Compliant", "High-Risk", "Needs Clarification", "Critical"].map((f, i) => (
          <button key={f} className={`filter-btn${i === 0 ? " active" : ""}`}>{f}</button>
        ))}
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        {DEMO_BIDDERS.map(b => {
          const risk = RISK_CONF[b.riskLevel] ?? { cls: "", dot: "#94a3b8" };
          return (
            <div key={b.id} className="card" style={{ padding: 0 }}>
              <div style={{ padding: "16px 20px", display: "flex", alignItems: "center", gap: 20 }}>
                {/* Avatar */}
                <div style={{
                  width: 48, height: 48, borderRadius: 10, flexShrink: 0,
                  background: b.status === "Compliant" ? "linear-gradient(135deg,#10b981,#34d399)" :
                    b.status === "High-Risk" ? "linear-gradient(135deg,#ef4444,#f87171)" :
                      "linear-gradient(135deg,#f59e0b,#fbbf24)",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  color: "white", fontWeight: 800, fontSize: 16,
                }}>
                  {b.legalName.charAt(0)}
                </div>

                {/* Identity */}
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 700, fontSize: 15, color: "#0f172a" }}>{b.legalName}</div>
                  <div style={{ fontSize: 11, color: "#94a3b8", display: "flex", gap: 10, marginTop: 2 }}>
                    <span>{b.id}</span>
                    <span>·</span>
                    <span>PAN: {b.pan}</span>
                    <span>·</span>
                    <span>GSTIN: {b.gstin}</span>
                  </div>
                  {b.flags.length > 0 && (
                    <div style={{ display: "flex", gap: 6, marginTop: 6, flexWrap: "wrap" }}>
                      {b.flags.map(f => <span key={f} className="badge badge-red" style={{ fontSize: 10 }}>⚠️ {f}</span>)}
                    </div>
                  )}
                </div>

                {/* Scores */}
                <div style={{ display: "flex", gap: 24, alignItems: "center" }}>
                  <div style={{ textAlign: "center" }}>
                    <div style={{ fontSize: 11, color: "#64748b", marginBottom: 4 }}>Compliance</div>
                    <div style={{ fontWeight: 800, fontSize: 20, color: b.complianceScore >= 90 ? "#059669" : b.complianceScore >= 75 ? "#d97706" : "#dc2626" }}>
                      {b.complianceScore}%
                    </div>
                  </div>
                  <div style={{ textAlign: "center" }}>
                    <div style={{ fontSize: 11, color: "#64748b", marginBottom: 4 }}>Verification</div>
                    <div style={{ fontWeight: 800, fontSize: 20, color: "#0f172a" }}>{b.verificationScore}%</div>
                  </div>
                  <div style={{ textAlign: "center" }}>
                    <div style={{ fontSize: 11, color: "#64748b", marginBottom: 4 }}>Risk</div>
                    <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                      <span style={{ width: 8, height: 8, borderRadius: "50%", background: risk.dot, display: "inline-block" }} />
                      <span className={risk.cls} style={{ fontSize: 14 }}>{b.riskLevel}</span>
                    </div>
                  </div>
                  <div>
                    <span className={`badge ${b.status === "Compliant" ? "badge-green" : b.status === "High-Risk" ? "badge-red" : "badge-yellow"}`} style={{ fontSize: 11 }}>
                      {b.statusLabel}
                    </span>
                  </div>
                </div>

                {/* Actions */}
                <div style={{ display: "flex", flexDirection: "column", gap: 6, marginLeft: 8 }}>
                  <Link href={`/bidders/${b.id}`} className="btn btn-primary btn-sm">View Profile →</Link>
                  <Link href={`/bidders/${b.id}/review`} className="btn btn-secondary btn-sm">Officer Review</Link>
                </div>
              </div>

              {/* Progress strip */}
              <div style={{ height: 4, background: "#f1f5f9" }}>
                <div className={`progress-bar-fill ${b.complianceScore >= 90 ? "progress-green" : b.complianceScore >= 75 ? "progress-yellow" : "progress-red"}`}
                  style={{ height: "100%", width: `${b.complianceScore}%`, borderRadius: 0 }} />
              </div>
            </div>
          );
        })}
      </div>
    </>
  );
}
