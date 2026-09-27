"use client";
import { useState } from "react";
import Link from "next/link";
import { DEMO_BIDDERS, DEMO_RECOMMENDATIONS } from "@/lib/mockData";
import { notFound } from "next/navigation";

export default function ReviewPage({ params }: { params: { bidderId: string } }) {
  const bidder = DEMO_BIDDERS.find(b => b.id === params.bidderId);
  if (!bidder) return notFound();
  const rec = DEMO_RECOMMENDATIONS[params.bidderId as keyof typeof DEMO_RECOMMENDATIONS];

  const [action, setAction] = useState<"" | "confirm" | "clarify" | "override">("");
  const [reason, setReason] = useState("");
  const [comment, setComment] = useState("");
  const [submitted, setSubmitted] = useState(false);

  function submit() {
    if ((action === "override" || action === "clarify") && !reason.trim()) return;
    setSubmitted(true);
  }

  if (submitted) {
    return (
      <div className="card" style={{ textAlign: "center", padding: 48, maxWidth: 540, margin: "40px auto" }}>
        <div style={{ fontSize: 48, marginBottom: 16 }}>
          {action === "confirm" ? "✅" : action === "clarify" ? "💬" : "🔴"}
        </div>
        <h2 style={{ fontSize: 22, fontWeight: 800, color: "#0f172a", margin: "0 0 8px" }}>
          {action === "confirm" ? "Bid Confirmed Compliant" : action === "clarify" ? "Clarification Requested" : "Bid Marked High-Risk"}
        </h2>
        <p style={{ color: "#64748b", margin: "0 0 24px" }}>
          Your decision has been recorded in the audit trail with a timestamp and officer identity.
        </p>
        {reason && <div style={{ background: "#f8fafc", borderRadius: 8, padding: "10px 14px", fontSize: 13, color: "#374151", marginBottom: 20, textAlign: "left" }}>
          <strong>Reason:</strong> {reason}
        </div>}
        <div style={{ display: "flex", gap: 10, justifyContent: "center" }}>
          <Link href="/audit" className="btn btn-secondary">View Audit Trail</Link>
          <Link href="/bidders" className="btn btn-primary">Back to Bidders</Link>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="demo-banner">⚠️ Demo Mode — Officer decisions are recorded in the demo audit trail only.</div>
      <div style={{ marginBottom: 16 }}>
        <Link href={`/bidders/${bidder.id}/recommendation`} style={{ fontSize: 12, color: "#1a56db" }}>← Back to Recommendation</Link>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        {/* Summary */}
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <div className="card">
            <div className="card-header"><span className="card-title">📋 Bid Summary</span></div>
            <div className="card-body">
              {[
                ["Bidder", bidder.legalName],
                ["Bid ID", bidder.id],
                ["Tender", "GEM/2025/B/47821"],
                ["Compliance Score", `${bidder.complianceScore}%`],
                ["Risk Level", bidder.riskLevel],
                ["AI Recommendation", rec.status],
                ["Conflicts", String(bidder.conflicts)],
              ].map(([k, v]) => (
                <div key={k} style={{ display: "flex", justifyContent: "space-between", padding: "7px 0", borderBottom: "1px solid #f1f5f9", fontSize: 13 }}>
                  <span style={{ color: "#64748b" }}>{k}</span>
                  <span style={{ fontWeight: 600, color: "#0f172a" }}>{v}</span>
                </div>
              ))}
            </div>
          </div>

          <div style={{ background: "#fffbeb", border: "1px solid #fde68a", borderRadius: 10, padding: "14px 18px" }}>
            <div style={{ fontWeight: 700, color: "#92400e", marginBottom: 6 }}>⚖️ Procurement Officer's Authority</div>
            <p style={{ fontSize: 12, color: "#374151", margin: 0, lineHeight: 1.6 }}>
              The AI Recommendation is decision-support only. You have full authority to confirm, request clarification, or override. Your reasoning will be recorded in the audit trail.
            </p>
          </div>
        </div>

        {/* Decision panel */}
        <div className="card">
          <div className="card-header"><span className="card-title">👨‍⚖️ Officer Decision</span></div>
          <div className="card-body">
            <p style={{ fontSize: 13, color: "#374151", margin: "0 0 16px" }}>Select an action for <strong>{bidder.legalName}</strong>:</p>

            {/* Action buttons */}
            <div style={{ display: "flex", flexDirection: "column", gap: 10, marginBottom: 20 }}>
              {[
                { key: "confirm", label: "🟢 Confirm Compliant", sub: "Accepts the AI recommendation and confirms the bid meets all eligibility conditions.", color: "#059669", bg: "#f0fdf4", border: "#bbf7d0" },
                { key: "clarify", label: "🟡 Request Clarification", sub: "Issue a formal clarification notice to the bidder for missing or unclear evidence.", color: "#d97706", bg: "#fffbeb", border: "#fde68a" },
                { key: "override", label: "🔴 Override / Reject", sub: "Override the AI recommendation. Mandatory reason required.", color: "#dc2626", bg: "#fef2f2", border: "#fecaca" },
              ].map(a => (
                <div key={a.key} onClick={() => setAction(a.key as any)}
                  style={{ padding: "14px 16px", borderRadius: 10, border: `2px solid ${action === a.key ? a.color : "#e2e8f0"}`,
                    background: action === a.key ? a.bg : "white", cursor: "pointer", transition: "all 0.15s" }}>
                  <div style={{ fontWeight: 700, fontSize: 14, color: a.color }}>{a.label}</div>
                  <div style={{ fontSize: 12, color: "#64748b", marginTop: 3 }}>{a.sub}</div>
                </div>
              ))}
            </div>

            {(action === "clarify" || action === "override") && (
              <div className="form-group" style={{ marginBottom: 12 }}>
                <label className="form-label">
                  {action === "override" ? "⚠️ Override Reason (mandatory)" : "💬 Clarification Note (mandatory)"}
                </label>
                <textarea
                  className="form-input"
                  rows={4}
                  placeholder={action === "override" ? "Explain why you are overriding the AI recommendation..." : "Describe what clarification is required from the bidder..."}
                  value={reason}
                  onChange={e => setReason(e.target.value)}
                  style={{ resize: "vertical" }}
                />
              </div>
            )}

            {action && (
              <div className="form-group" style={{ marginBottom: 16 }}>
                <label className="form-label">Additional Comments (optional)</label>
                <textarea className="form-input" rows={2} placeholder="Internal notes..." value={comment} onChange={e => setComment(e.target.value)} style={{ resize: "none" }} />
              </div>
            )}

            <div style={{ display: "flex", gap: 10 }}>
              <button
                className={`btn btn-lg ${action === "confirm" ? "btn-success" : action === "clarify" ? "btn-warning" : action === "override" ? "btn-danger" : "btn-secondary"}`}
                style={{ flex: 1 }}
                disabled={!action || ((action === "override" || action === "clarify") && !reason.trim())}
                onClick={submit}
              >
                {action ? `Confirm: ${action.charAt(0).toUpperCase() + action.slice(1)} →` : "Select an action above"}
              </button>
              <Link href={`/bidders/${bidder.id}`} className="btn btn-secondary btn-lg">Cancel</Link>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
