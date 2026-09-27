import Link from "next/link";
import { DEMO_BIDDERS } from "@/lib/mockData";
import { notFound } from "next/navigation";

export default function BidderProfilePage({ params }: { params: { bidderId: string } }) {
  const bidder = DEMO_BIDDERS.find(b => b.id === params.bidderId);
  if (!bidder) return notFound();

  const isCompliant = bidder.status === "Compliant";
  const isHighRisk = bidder.status === "High-Risk";

  return (
    <>
      <div className="demo-banner">⚠️ Demo Mode — Source connector results are from the DEMO dataset, not live government sources.</div>

      {/* Header card */}
      <div className="card mb-4" style={{ padding: 0 }}>
        <div style={{
          height: 8,
          background: isCompliant ? "linear-gradient(90deg,#10b981,#34d399)" :
            isHighRisk ? "linear-gradient(90deg,#ef4444,#f87171)" :
              "linear-gradient(90deg,#f59e0b,#fbbf24)",
        }} />
        <div style={{ padding: "20px 24px", display: "flex", alignItems: "flex-start", gap: 20 }}>
          <div style={{
            width: 64, height: 64, borderRadius: 14, flexShrink: 0,
            background: isCompliant ? "linear-gradient(135deg,#10b981,#34d399)" :
              isHighRisk ? "linear-gradient(135deg,#ef4444,#f87171)" :
                "linear-gradient(135deg,#f59e0b,#fbbf24)",
            display: "flex", alignItems: "center", justifyContent: "center",
            color: "white", fontWeight: 900, fontSize: 24,
          }}>
            {bidder.legalName.charAt(0)}
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 20, fontWeight: 800, color: "#0f172a" }}>{bidder.legalName}</div>
            <div style={{ fontSize: 13, color: "#64748b", marginTop: 2 }}>{bidder.id} · Tender: GEM/2025/B/47821</div>
            <div style={{ display: "flex", gap: 8, marginTop: 10, flexWrap: "wrap" }}>
              <span className={`badge ${isCompliant ? "badge-green" : isHighRisk ? "badge-red" : "badge-yellow"}`} style={{ fontSize: 12 }}>
                {isCompliant ? "✅" : isHighRisk ? "🔴" : "⚠️"} {bidder.statusLabel}
              </span>
              {bidder.flags.map(f => <span key={f} className="badge badge-red" style={{ fontSize: 10 }}>⚠️ {f}</span>)}
            </div>
          </div>
          <div style={{ display: "flex", gap: 16 }}>
            {[
              { label: "Compliance", value: `${bidder.complianceScore}%`, color: bidder.complianceScore >= 90 ? "#059669" : bidder.complianceScore >= 75 ? "#d97706" : "#dc2626" },
              { label: "Verification", value: `${bidder.verificationScore}%`, color: "#0f172a" },
              { label: "Risk Score", value: `${bidder.riskScore}`, color: bidder.riskScore < 25 ? "#059669" : bidder.riskScore < 50 ? "#d97706" : "#dc2626" },
            ].map(s => (
              <div key={s.label} style={{ textAlign: "center" }}>
                <div style={{ fontSize: 11, color: "#64748b", marginBottom: 4 }}>{s.label}</div>
                <div style={{ fontSize: 24, fontWeight: 900, color: s.color }}>{s.value}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Quick nav */}
      <div style={{ display: "flex", gap: 8, marginBottom: 20, flexWrap: "wrap" }}>
        {[
          { label: "Documents", icon: "📄", href: `/bidders/${bidder.id}/documents` },
          { label: "Verification", icon: "🔍", href: `/bidders/${bidder.id}/verification` },
          { label: "Conflicts", icon: "⚠️", href: `/bidders/${bidder.id}/conflicts` },
          { label: "Compliance", icon: "✅", href: `/bidders/${bidder.id}/compliance` },
          { label: "Recommendation", icon: "🤖", href: `/bidders/${bidder.id}/recommendation` },
          { label: "Review", icon: "👨‍⚖️", href: `/bidders/${bidder.id}/review` },
        ].map(n => (
          <Link key={n.label} href={n.href} className="btn btn-secondary" style={{ fontSize: 12 }}>
            {n.icon} {n.label}
          </Link>
        ))}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        {/* Entity details */}
        <div className="card">
          <div className="card-header"><span className="card-title">🏢 Legal Entity Details</span></div>
          <div className="card-body">
            {[
              ["Legal Name", bidder.legalName],
              ["PAN", bidder.pan],
              ["GSTIN", bidder.gstin],
              ["Udyam No.", bidder.udyamNumber ?? "⚠️ Not submitted"],
              ["CIN", bidder.cin],
              ["Authorised Signatory", bidder.authorisedSignatory],
              ["OEM Relationship", bidder.oemRelationship],
              ["Registered Address", bidder.address],
            ].map(([k, v]) => (
              <div key={k} style={{ display: "flex", gap: 12, padding: "8px 0", borderBottom: "1px solid #f1f5f9" }}>
                <span style={{ fontSize: 12, color: "#64748b", minWidth: 140 }}>{k}</span>
                <span style={{ fontSize: 12, fontWeight: 600, color: v?.includes("⚠️") ? "#dc2626" : "#0f172a" }}>{v}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Identity relationship */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div className="card">
            <div className="card-header"><span className="card-title">🔗 Identity Relationship</span></div>
            <div className="card-body">
              <div className="identity-graph">
                <div className={`id-node ${bidder.conflicts === 0 ? "verified" : ""}`}>
                  <div className="id-node-label">PAN</div>
                  <div className="id-node-val">{bidder.pan}</div>
                </div>
                <div className="id-connector" />
                <div className={`id-node ${bidder.conflicts > 0 ? "conflict" : "verified"}`}>
                  <div className="id-node-label">GSTIN</div>
                  <div className="id-node-val" style={{ fontSize: 10 }}>{bidder.gstin}</div>
                </div>
                <div className="id-connector" />
                <div className={`id-node ${!bidder.udyamNumber ? "conflict" : "verified"}`}>
                  <div className="id-node-label">Udyam</div>
                  <div className="id-node-val" style={{ fontSize: 10 }}>{bidder.udyamNumber?.slice(0, 10) ?? "N/A"}</div>
                </div>
                <div className="id-connector" />
                <div className="id-node verified">
                  <div className="id-node-label">CIN</div>
                  <div className="id-node-val" style={{ fontSize: 10 }}>{bidder.cin.slice(0, 10)}</div>
                </div>
              </div>
              <div style={{ marginTop: 10, display: "flex", gap: 10, flexWrap: "wrap" }}>
                <span style={{ fontSize: 10, color: "#166534" }}>🟢 Verified match</span>
                <span style={{ fontSize: 10, color: "#991b1b" }}>🔴 Conflict / Missing</span>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-header"><span className="card-title">📊 Compliance Breakdown</span></div>
            <div className="card-body">
              {[
                { label: "Mandatory Eligibility (60%)", score: bidder.complianceScore >= 90 ? 60 : bidder.complianceScore >= 75 ? 45 : 30, max: 60, color: "#1a56db" },
                { label: "Statutory Compliance (25%)", score: bidder.complianceScore >= 90 ? 25 : 20, max: 25, color: "#10b981" },
                { label: "Tender Documentation (15%)", score: bidder.complianceScore >= 90 ? 15 : 12, max: 15, color: "#f59e0b" },
              ].map(r => (
                <div key={r.label} style={{ marginBottom: 12 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 4 }}>
                    <span style={{ color: "#374151" }}>{r.label}</span>
                    <span style={{ fontWeight: 700 }}>{r.score}/{r.max}</span>
                  </div>
                  <div className="progress-bar">
                    <div className="progress-bar-fill" style={{ width: `${(r.score / r.max) * 100}%`, background: r.color }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
