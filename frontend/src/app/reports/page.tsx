"use client";
import { useState } from "react";
import { DEMO_BIDDERS } from "@/lib/mockData";

const REPORTS = [
  {
    id: "TR-001", title: "Tender Compliance Report",
    desc: "Complete compliance evaluation summary for all bidders in GEM/2025/B/47821.",
    type: "Compliance", icon: "✅", status: "Ready",
  },
  {
    id: "TR-002", title: "Risk Assessment Report",
    desc: "Risk scoring, conflict summary, and high-risk bidder details.",
    type: "Risk", icon: "⚠️", status: "Ready",
  },
  {
    id: "TR-003", title: "Verification Report",
    desc: "Source connector results, mode (DEMO/LIVE), and verification status per bidder.",
    type: "Verification", icon: "🔍", status: "Ready",
  },
  {
    id: "TR-004", title: "Audit Trail Report",
    desc: "Full event timeline with timestamps, actors, and decision records.",
    type: "Audit", icon: "📅", status: "Ready",
  },
  {
    id: "TR-005", title: "Bidder Evaluation Report",
    desc: "Individual bidder profile, extracted fields, and rule results.",
    type: "Bidder", icon: "👥", status: "Ready",
  },
];

export default function ReportsPage() {
  const [generating, setGenerating] = useState<string | null>(null);
  const [done, setDone] = useState<string[]>([]);

  function generate(id: string) {
    setGenerating(id);
    setTimeout(() => {
      setGenerating(null);
      setDone(p => [...p, id]);
    }, 1500);
  }

  return (
    <>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 12, marginBottom: 24 }}>
        {[
          { label: "Reports Ready", value: REPORTS.length, color: "#059669", bg: "#f0fdf4" },
          { label: "Tender", value: "GEM/2025/B/47821", color: "#1e40af", bg: "#eff6ff" },
          { label: "Bidders Evaluated", value: "3", color: "#7c3aed", bg: "#f5f3ff" },
        ].map(c => (
          <div key={c.label} style={{ background: c.bg, border: `1px solid ${c.color}22`, borderRadius: 10, padding: "14px 18px" }}>
            <div style={{ fontSize: 11, color: c.color, fontWeight: 700 }}>{c.label}</div>
            <div style={{ fontSize: 22, fontWeight: 900, color: c.color }}>{c.value}</div>
          </div>
        ))}
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 14, marginBottom: 24 }}>
        {REPORTS.map(r => (
          <div key={r.id} className="card" style={{ padding: 0 }}>
            <div style={{ padding: "16px 20px", display: "flex", alignItems: "center", gap: 16 }}>
              <div style={{ fontSize: 28, flexShrink: 0 }}>{r.icon}</div>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 700, fontSize: 15, color: "#0f172a" }}>{r.title}</div>
                <div style={{ fontSize: 12, color: "#64748b", marginTop: 2 }}>{r.desc}</div>
                <div style={{ display: "flex", gap: 8, marginTop: 6 }}>
                  <span className="badge badge-blue" style={{ fontSize: 10 }}>{r.type}</span>
                  <span className="badge badge-gray" style={{ fontSize: 10 }}>{r.id}</span>
                </div>
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                {done.includes(r.id) ? (
                  <>
                    <button className="btn btn-success btn-sm">✅ Download PDF</button>
                    <button className="btn btn-secondary btn-sm">📊 Export CSV</button>
                  </>
                ) : (
                  <button
                    className="btn btn-primary btn-sm"
                    onClick={() => generate(r.id)}
                    disabled={generating === r.id}
                  >
                    {generating === r.id ? "⏳ Generating..." : "📄 Generate"}
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Bidder-wise summary */}
      <div className="card">
        <div className="card-header"><span className="card-title">👥 Per-Bidder Evaluation Summary</span></div>
        <div style={{ overflowX: "auto" }}>
          <table className="data-table">
            <thead>
              <tr><th>Bidder</th><th>Bid ID</th><th>Compliance</th><th>Risk</th><th>Conflicts</th><th>Status</th><th>Report</th></tr>
            </thead>
            <tbody>
              {DEMO_BIDDERS.map(b => (
                <tr key={b.id}>
                  <td style={{ fontWeight: 600 }}>{b.legalName}</td>
                  <td style={{ fontFamily: "monospace", fontSize: 11 }}>{b.id}</td>
                  <td style={{ fontWeight: 700, color: b.complianceScore >= 90 ? "#059669" : b.complianceScore >= 75 ? "#d97706" : "#dc2626" }}>
                    {b.complianceScore}%
                  </td>
                  <td>
                    <span className={`badge ${b.riskLevel === "Low" ? "badge-green" : b.riskLevel === "High" ? "badge-red" : "badge-orange"}`}>
                      {b.riskLevel}
                    </span>
                  </td>
                  <td style={{ textAlign: "center", fontWeight: 700, color: b.conflicts > 0 ? "#dc2626" : "#059669" }}>
                    {b.conflicts}
                  </td>
                  <td>
                    <span className={`badge ${b.status === "Compliant" ? "badge-green" : b.status === "High-Risk" ? "badge-red" : "badge-yellow"}`}>
                      {b.statusLabel}
                    </span>
                  </td>
                  <td>
                    <button className="btn btn-secondary btn-sm" onClick={() => alert(`Generating for ${b.legalName}...`)}>
                      Generate Report
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
