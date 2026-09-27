import Link from "next/link";
import { DEMO_BIDDERS, DEMO_COMPLIANCE_RULES } from "@/lib/mockData";
import { notFound } from "next/navigation";

const RESULT_CONFIG: Record<string, { cls: string; icon: string }> = {
  PASS: { cls: "badge-green", icon: "✅" },
  FAIL: { cls: "badge-red", icon: "❌" },
  NEEDS_CLARIFICATION: { cls: "badge-yellow", icon: "⚠️" },
  NOT_APPLICABLE: { cls: "badge-gray", icon: "—" },
};

export default function CompliancePage({ params }: { params: { bidderId: string } }) {
  const bidder = DEMO_BIDDERS.find(b => b.id === params.bidderId);
  if (!bidder) return notFound();
  const rules = DEMO_COMPLIANCE_RULES[params.bidderId as keyof typeof DEMO_COMPLIANCE_RULES] ?? [];

  const pass = rules.filter(r => r.result === "PASS").length;
  const fail = rules.filter(r => r.result === "FAIL").length;
  const clarify = rules.filter(r => r.result === "NEEDS_CLARIFICATION").length;

  return (
    <>
      <div className="demo-banner">⚠️ Demo Mode · {bidder.legalName} · Rules Engine v1.0</div>
      <div style={{ marginBottom: 16, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <Link href={`/bidders/${bidder.id}`} style={{ fontSize: 12, color: "#1a56db" }}>← Back to Profile</Link>
        <div style={{ display: "flex", gap: 8 }}>
          <span className="badge badge-green">Pass: {pass}</span>
          <span className="badge badge-red">Fail: {fail}</span>
          <span className="badge badge-yellow">Clarify: {clarify}</span>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 12, marginBottom: 20 }}>
        {[
          { label: "Total Rules", value: rules.length, color: "#1e40af", bg: "#eff6ff" },
          { label: "Passed", value: pass, color: "#059669", bg: "#f0fdf4" },
          { label: "Failed", value: fail, color: "#dc2626", bg: "#fef2f2" },
          { label: "Needs Clarification", value: clarify, color: "#d97706", bg: "#fffbeb" },
        ].map(c => (
          <div key={c.label} style={{ background: c.bg, border: `1px solid ${c.color}22`, borderRadius: 10, padding: "14px 18px" }}>
            <div style={{ fontSize: 11, color: c.color, fontWeight: 700 }}>{c.label}</div>
            <div style={{ fontSize: 28, fontWeight: 900, color: c.color }}>{c.value}</div>
          </div>
        ))}
      </div>

      <div className="card">
        <div className="card-header">
          <span className="card-title">✅ Compliance Rules Evaluation <span className="badge badge-gray" style={{ fontSize: 10, marginLeft: 8 }}>RULEBOOK-GEM-47821-v1.0</span></span>
        </div>
        <div style={{ overflowX: "auto" }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Rule</th>
                <th>Priority</th>
                <th>Result</th>
                <th>Tender Clause</th>
                <th>Evidence</th>
              </tr>
            </thead>
            <tbody>
              {rules.map(r => {
                const cfg = RESULT_CONFIG[r.result] ?? RESULT_CONFIG["NOT_APPLICABLE"];
                return (
                  <tr key={r.id}>
                    <td>
                      <div style={{ fontWeight: 600, fontSize: 13 }}>{r.name}</div>
                      <div style={{ fontSize: 10, color: "#94a3b8", fontFamily: "monospace" }}>{r.id}</div>
                    </td>
                    <td>
                      <span className={`badge ${r.severity === "mandatory" ? "badge-red" : "badge-blue"}`} style={{ fontSize: 10 }}>
                        {r.severity.toUpperCase()}
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${cfg.cls}`}>{cfg.icon} {r.result.replace("_", " ")}</span>
                    </td>
                    <td style={{ fontSize: 12, color: "#1a56db" }}>{r.clause}</td>
                    <td style={{ fontSize: 11, color: "#64748b" }}>{r.evidence}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {fail > 0 && (
        <div style={{ marginTop: 14, background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 10, padding: "14px 18px" }}>
          <div style={{ fontWeight: 700, color: "#dc2626", marginBottom: 6 }}>🔴 Mandatory Gate Failure Detected</div>
          <p style={{ fontSize: 13, color: "#374151", margin: 0, lineHeight: 1.6 }}>
            One or more mandatory eligibility rules have failed. This triggers a <strong>High-Risk</strong> classification.
            The Procurement Officer must review and either seek clarification or mark this bid as non-compliant.
          </p>
        </div>
      )}
    </>
  );
}
