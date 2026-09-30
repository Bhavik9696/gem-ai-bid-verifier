"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useBidWorkspace } from "@/lib/api";

function getRecommendationColor(rec: string | null) {
  if (!rec) return 'badge-gray';
  const r = rec.toUpperCase();
  if (r.includes("ACCEPT") || r.includes("PROCEED") || r.includes("APPROVE")) return "badge-green";
  if (r.includes("REJECT") || r.includes("DISQUALIFY")) return "badge-red";
  return "badge-yellow";
}

function getRiskColor(risk: string | null) {
  if (!risk) return "#64748b";
  const r = risk.toUpperCase();
  if (r === "LOW") return "#10b981";
  if (r === "MEDIUM" || r === "MODERATE") return "#f59e0b";
  return "#ef4444";
}

function getSeverityBadge(severity: string | null) {
  if (!severity) return 'badge-gray';
  const s = severity.toUpperCase();
  if (s === "CRITICAL" || s === "HIGH") return "badge-red";
  if (s === "MEDIUM" || s === "MODERATE") return "badge-yellow";
  return "badge-blue";
}

export default function RecommendationPage() {
  const { bidderId: bidId } = useParams<{ bidderId: string }>();
  const { bid, assessment, loading, error } = useBidWorkspace(bidId);
  
  if (loading) return <div style={{ padding: 40, color: "#64748b" }}>Loading recommendation…</div>;
  if (error || !bid) return <div className="card card-body" role="alert" style={{ color: "#ef4444", marginTop: 24 }}>{error ?? "Bid not found."}</div>;

  return (
    <>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: 24, flexWrap: "wrap", gap: 16 }}>
        <div>
          <Link href={`/bidders/${encodeURIComponent(bidId)}`} style={{ display: 'inline-flex', alignItems: 'center', color: '#1a56db', fontSize: 13, textDecoration: 'none', marginBottom: 12, fontWeight: 500 }}>
            <span style={{ marginRight: 6 }}>←</span> Back to {bid.bidderName} Profile
          </Link>
          <h1 style={{ fontSize: 24, fontWeight: 700, color: '#0f172a', margin: 0 }}>System Recommendation</h1>
        </div>
        <Link href={`/bidders/${encodeURIComponent(bidId)}/review`} className="btn btn-primary" style={{ padding: "10px 20px" }}>
          Proceed to Officer Review
        </Link>
      </div>

      {!assessment ? (
        <div className="card card-body" style={{ color: "#64748b", textAlign: "center", padding: 40 }}>
          No recommendation is available until verification has been run.
        </div>
      ) : (
        <>
          {/* Recommendation Summary Section */}
          <div className="card" style={{ marginBottom: 24, overflow: "hidden" }}>
            <div style={{ padding: "24px", background: "linear-gradient(to right, #f8fafc, #ffffff)", borderBottom: "1px solid #e2e8f0", display: "flex", flexWrap: "wrap", gap: 24, justifyContent: "space-between", alignItems: "flex-start" }}>
              <div style={{ flex: "1 1 300px" }}>
                <div style={{ fontSize: 12, fontWeight: 700, color: "#64748b", textTransform: "uppercase", marginBottom: 8 }}>AI Assessment Outcome</div>
                <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12 }}>
                  <span className={`badge ${getRecommendationColor(assessment.recommendation)}`} style={{ fontSize: 16, padding: "6px 12px" }}>
                    {assessment.recommendation?.replace(/_/g, ' ') ?? "UNKNOWN"}
                  </span>
                </div>
                <p style={{ margin: 0, fontSize: 14, color: "#334155", lineHeight: 1.6 }}>
                  {assessment.recommendationSummary ?? "The API did not return a recommendation summary."}
                </p>
                <div style={{ marginTop: 16, fontSize: 12, color: "#94a3b8", display: "flex", alignItems: "center", gap: 6 }}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
                  Evaluated: {new Date(assessment.evaluatedAt).toLocaleString("en-IN", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" })}
                </div>
              </div>
              
              <div style={{ display: "flex", gap: 24, flexWrap: "wrap" }}>
                <div style={{ background: "white", padding: 16, borderRadius: 8, border: "1px solid #e2e8f0", minWidth: 140, textAlign: "center" }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: "#64748b", textTransform: "uppercase", marginBottom: 8 }}>Compliance Score</div>
                  <div style={{ fontSize: 28, fontWeight: 800, color: assessment.complianceScore !== null && assessment.complianceScore >= 80 ? '#10b981' : assessment.complianceScore !== null && assessment.complianceScore >= 50 ? '#f59e0b' : '#ef4444' }}>
                    {assessment.complianceScore !== null ? `${assessment.complianceScore}%` : "—"}
                  </div>
                </div>
                <div style={{ background: "white", padding: 16, borderRadius: 8, border: "1px solid #e2e8f0", minWidth: 140, textAlign: "center" }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: "#64748b", textTransform: "uppercase", marginBottom: 8 }}>Risk Level</div>
                  <div style={{ fontSize: 24, fontWeight: 800, color: getRiskColor(assessment.riskLevel) }}>
                    {assessment.riskLevel?.toUpperCase() ?? "PENDING"}
                  </div>
                </div>
              </div>
            </div>
            
            <div style={{ background: "#eff6ff", padding: "12px 24px", display: "flex", gap: 12, alignItems: "center", borderTop: "1px solid #bfdbfe" }}>
              <span style={{ fontSize: 18 }}>ℹ️</span>
              <p style={{ margin: 0, fontSize: 12, color: "#1e3a8a" }}>
                <strong>Decision Support Only:</strong> This recommendation is generated automatically. The procurement officer retains final authority.
              </p>
            </div>
          </div>

          {/* Evidence for Review Section */}
          <h2 style={{ fontSize: 18, fontWeight: 700, color: "#0f172a", marginBottom: 16 }}>Evidence for Review</h2>
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {assessment.findings.map(finding => (
              <div key={finding.id} className="card" style={{ padding: 20, display: "flex", gap: 16, alignItems: "flex-start" }}>
                <span className={`badge ${getSeverityBadge(finding.severity)}`} style={{ marginTop: 2, flexShrink: 0, minWidth: 70, textAlign: "center" }}>
                  {finding.severity?.toUpperCase() ?? "INFO"}
                </span>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 14, fontWeight: 700, color: "#0f172a", marginBottom: 6 }}>
                    {finding.findingType?.replace(/_/g, ' ') ?? "Finding"}
                  </div>
                  <p style={{ margin: "0 0 12px 0", fontSize: 13, color: "#475569", lineHeight: 1.5 }}>
                    {finding.message}
                  </p>
                  {finding.evidenceReference && (
                    <div style={{ display: "inline-flex", alignItems: "center", gap: 6, background: "#f1f5f9", padding: "6px 12px", borderRadius: 4, fontSize: 12, color: "#64748b", fontStyle: "italic" }}>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                      {finding.evidenceReference}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {!assessment.findings.length && (
              <div className="card" style={{ padding: 32, textAlign: "center", color: "#64748b", fontSize: 14 }}>
                No findings were returned for this assessment.
              </div>
            )}
          </div>
        </>
      )}
    </>
  );
}
