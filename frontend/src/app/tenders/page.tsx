import Link from "next/link";
import { DEMO_TENDERS } from "@/lib/mockData";

const STATUS_COLOR: Record<string, string> = {
  "Published": "badge-blue",
  "Under Evaluation": "badge-yellow",
  "Awarded": "badge-green",
  "Cancelled": "badge-red",
};

export default function TendersPage() {
  return (
    <>
      <div className="demo-banner">⚠️ Demo Mode — Tender data is from the prototype dataset.</div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <div className="page-header" style={{ margin: 0 }}>
          <h1>All Tenders</h1>
          <p>Manage and evaluate tenders imported from GeM.</p>
        </div>
        <Link href="/tenders/import" className="btn btn-primary">⬆️ Import Tender</Link>
      </div>

      {/* Summary cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 14, marginBottom: 20 }}>
        {[
          { label: "Total", value: "842", color: "#1a56db", bg: "#eff6ff" },
          { label: "Under Evaluation", value: "231", color: "#d97706", bg: "#fffbeb" },
          { label: "Awarded", value: "128", color: "#059669", bg: "#f0fdf4" },
          { label: "Cancelled", value: "42", color: "#dc2626", bg: "#fef2f2" },
        ].map(c => (
          <div key={c.label} style={{ background: c.bg, border: `1px solid ${c.color}22`, borderRadius: 10, padding: "14px 18px" }}>
            <div style={{ fontSize: 11, color: c.color, fontWeight: 700, marginBottom: 4 }}>{c.label}</div>
            <div style={{ fontSize: 28, fontWeight: 900, color: c.color }}>{c.value}</div>
          </div>
        ))}
      </div>

      <div className="filter-bar">
        {["All", "Published", "Under Evaluation", "Awarded", "Cancelled"].map((f, i) => (
          <button key={f} className={`filter-btn${i === 0 ? " active" : ""}`}>{f}</button>
        ))}
        <input className="form-input" placeholder="Search tenders..." style={{ marginLeft: "auto", width: 220, fontSize: 12, padding: "6px 12px" }} />
      </div>

      <div className="card">
        <div style={{ overflowX: "auto" }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Tender ID</th>
                <th>Title</th>
                <th>Department</th>
                <th>Closing Date</th>
                <th>Bidders</th>
                <th>Status</th>
                <th>Compliance</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {DEMO_TENDERS.map(t => (
                <tr key={t.id}>
                  <td><span style={{ fontFamily: "monospace", fontSize: 11, color: "#1a56db", fontWeight: 600 }}>{t.id}</span></td>
                  <td style={{ fontWeight: 600, fontSize: 13 }}>{t.title}</td>
                  <td style={{ fontSize: 12, color: "#64748b" }}>{t.department}</td>
                  <td style={{ fontSize: 12 }}>{t.closingDate}</td>
                  <td style={{ textAlign: "center", fontWeight: 700 }}>{t.bidderCount}</td>
                  <td><span className={`badge ${STATUS_COLOR[t.status] ?? "badge-gray"}`}>{t.status}</span></td>
                  <td>
                    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                      <div className="progress-bar" style={{ width: 60 }}>
                        <div className={`progress-bar-fill ${t.complianceProgress >= 90 ? "progress-green" : t.complianceProgress > 0 ? "progress-yellow" : "progress-blue"}`}
                          style={{ width: `${t.complianceProgress}%` }} />
                      </div>
                      <span style={{ fontSize: 11, fontWeight: 600 }}>{t.complianceProgress}%</span>
                    </div>
                  </td>
                  <td>
                    <div style={{ display: "flex", gap: 6 }}>
                      <Link href="/bidders" className="btn btn-secondary btn-sm">View</Link>
                      {t.status === "Under Evaluation" && (
                        <Link href="/bidders" className="btn btn-primary btn-sm">Evaluate →</Link>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Tender details */}
      <div className="card mt-4">
        <div className="card-header">
          <span className="card-title">📋 Tender Detail – GEM/2025/B/47821</span>
          <Link href="/tenders/rules" className="card-link">View Rulebook →</Link>
        </div>
        <div className="card-body">
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
            <div>
              <h3 style={{ fontSize: 16, fontWeight: 700, margin: "0 0 12px" }}>Supply of IT Equipment</h3>
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {[
                  ["Department", "Ministry of Electronics & IT"],
                  ["Closing Date", "30 Sep 2026"],
                  ["Estimated Value", "₹45,00,000"],
                  ["Category", "Electronics"],
                  ["Rulebook", "RULEBOOK-GEM-47821-v1.0"],
                ].map(([k, v]) => (
                  <div key={k} style={{ display: "flex", gap: 12, fontSize: 13 }}>
                    <span style={{ color: "#64748b", minWidth: 120 }}>{k}:</span>
                    <span style={{ fontWeight: 600, color: "#0f172a" }}>{v}</span>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <h4 style={{ fontSize: 13, fontWeight: 700, color: "#374151", margin: "0 0 10px" }}>Eligibility Criteria</h4>
              <ul style={{ margin: 0, padding: "0 0 0 18px", display: "flex", flexDirection: "column", gap: 6 }}>
                {[
                  "Must be registered on GeM portal",
                  "MSME or Udyam registration mandatory",
                  "Active GST registration",
                  "Make in India – 50% local content mandatory",
                  "OEM authorisation letter required",
                  "No blacklisting or debarment",
                ].map(e => <li key={e} style={{ fontSize: 12, color: "#374151" }}>{e}</li>)}
              </ul>
            </div>
          </div>
          <div style={{ marginTop: 16 }}>
            <h4 style={{ fontSize: 13, fontWeight: 700, color: "#374151", margin: "0 0 10px" }}>Key Tender Clauses</h4>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {[
                { ref: "Clause 4.2, Page 7", text: "GST registration must be active on bid closing date." },
                { ref: "Clause 5.1, Page 9", text: "Udyam/MSME registration must be valid." },
                { ref: "Clause 6.3, Page 11", text: "OEM authorisation letter must be valid and not expired." },
                { ref: "Clause 7.1, Page 12", text: "Make in India local content ≥ 50%." },
                { ref: "Clause 8.2, Page 14", text: "No debarment or blacklisting by any government authority." },
              ].map(c => (
                <div key={c.ref} style={{ display: "flex", gap: 12, padding: "8px 12px", background: "#f8fafc", borderRadius: 6, fontSize: 12 }}>
                  <span style={{ color: "#1a56db", fontWeight: 700, minWidth: 150 }}>{c.ref}</span>
                  <span style={{ color: "#374151" }}>{c.text}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
