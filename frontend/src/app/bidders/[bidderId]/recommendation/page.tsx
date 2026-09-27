"use client";
import { useState } from "react";
import Link from "next/link";
import { DEMO_BIDDERS, DEMO_RECOMMENDATIONS } from "@/lib/mockData";
import { notFound } from "next/navigation";

export default function RecommendationPage({ params }: { params: { bidderId: string } }) {
  const bidder = DEMO_BIDDERS.find(b => b.id === params.bidderId);
  if (!bidder) return notFound();
  const rec = DEMO_RECOMMENDATIONS[params.bidderId as keyof typeof DEMO_RECOMMENDATIONS];
  const [expanded, setExpanded] = useState(true);

  const colorMap = { green: { bg: "#f0fdf4", border: "#bbf7d0", text: "#166534", badge: "badge-green", icon: "✅" },
    red: { bg: "#fef2f2", border: "#fecaca", text: "#991b1b", badge: "badge-red", icon: "🔴" },
    yellow: { bg: "#fffbeb", border: "#fde68a", text: "#92400e", badge: "badge-yellow", icon: "⚠️" } };
  const c = colorMap[rec.color as keyof typeof colorMap];

  return (
    <>
      <div className="demo-banner">⚠️ Demo Mode · AI Recommendation powered by Qwen/Llama — not a legal decision.</div>
      <div style={{ marginBottom: 16, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <Link href={`/bidders/${bidder.id}`} style={{ fontSize: 12, color: "#1a56db" }}>← Back to Profile</Link>
        <Link href={`/bidders/${bidder.id}/review`} className="btn btn-primary btn-sm">Proceed to Officer Review →</Link>
      </div>

      {/* Main recommendation card */}
      <div style={{ background: c.bg, border: `2px solid ${c.border}`, borderRadius: 14, padding: "24px 28px", marginBottom: 20 }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <span style={{ fontSize: 36 }}>{c.icon}</span>
            <div>
              <div style={{ fontSize: 10, fontWeight: 700, color: c.text, letterSpacing: 1.5, textTransform: "uppercase", marginBottom: 2 }}>
                AI Recommendation
              </div>
              <div style={{ fontSize: 24, fontWeight: 900, color: c.text }}>{rec.label}</div>
            </div>
          </div>
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <span className={`badge ${c.badge}`} style={{ fontSize: 12, padding: "6px 14px" }}>{rec.status}</span>
            <span className="badge badge-gray" style={{ fontSize: 10 }}>🤖 AI-Assisted</span>
          </div>
        </div>
        <div style={{ fontSize: 14, color: "#374151", lineHeight: 1.7, borderTop: `1px solid ${c.border}`, paddingTop: 12 }}>
          {rec.summary}
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>
        {/* Why section */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">🔍 Why This Recommendation?</span>
            <button className="btn btn-secondary btn-sm" onClick={() => setExpanded(!expanded)}>
              {expanded ? "Collapse" : "Expand"}
            </button>
          </div>
          {expanded && (
            <div className="card-body">
              <ol style={{ margin: 0, padding: "0 0 0 18px", display: "flex", flexDirection: "column", gap: 10 }}>
                {rec.reasons.map((r, i) => (
                  <li key={i} style={{ fontSize: 13, color: "#374151", lineHeight: 1.6 }}>
                    <span style={{ fontWeight: 600 }}>{r}</span>
                  </li>
                ))}
              </ol>
            </div>
          )}
        </div>

        {/* AI Note */}
        <div className="card">
          <div className="card-header"><span className="card-title">🤖 AI Analysis Note</span></div>
          <div className="card-body">
            <div style={{ background: "#f8fafc", borderRadius: 8, padding: "14px 16px", fontSize: 13, color: "#374151", lineHeight: 1.7, borderLeft: "3px solid #1a56db" }}>
              {rec.aiNote}
            </div>
            <div style={{ marginTop: 12, padding: "8px 12px", background: "#fff7ed", borderRadius: 6, fontSize: 11, color: "#92400e" }}>
              ⚠️ AI may classify and summarise evidence, but does not make the final procurement decision. The Procurement Officer has full authority.
            </div>
          </div>
        </div>
      </div>

      {/* Evidence chain */}
      <div className="card">
        <div className="card-header"><span className="card-title">📎 Evidence Chain</span></div>
        <div className="card-body">
          <div style={{ display: "flex", gap: 0, alignItems: "center", flexWrap: "wrap" }}>
            {[
              { label: "Bid Document", sub: "Submitted data", icon: "📄" },
              { label: "OCR Extraction", sub: "Field confidence ≥ 90%", icon: "🔬" },
              { label: "Source Connectors", sub: "GST, PAN, Udyam, OEM", icon: "🔌" },
              { label: "Conflict Engine", sub: "Entity matching", icon: "⚠️" },
              { label: "Rules Engine", sub: "v1.0 rulebook applied", icon: "⚖️" },
              { label: "AI Recommendation", sub: rec.label, icon: "🤖" },
            ].map((e, i, arr) => (
              <div key={e.label} style={{ display: "flex", alignItems: "center" }}>
                <div style={{ background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: 8, padding: "8px 12px", textAlign: "center", minWidth: 100 }}>
                  <div style={{ fontSize: 18 }}>{e.icon}</div>
                  <div style={{ fontSize: 11, fontWeight: 700, color: "#0f172a", margin: "2px 0" }}>{e.label}</div>
                  <div style={{ fontSize: 9, color: "#64748b" }}>{e.sub}</div>
                </div>
                {i < arr.length - 1 && <div style={{ fontSize: 16, color: "#94a3b8", margin: "0 4px" }}>→</div>}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Action buttons */}
      <div style={{ marginTop: 16, display: "flex", gap: 12 }}>
        <Link href={`/bidders/${bidder.id}/review`} className="btn btn-success">🟢 Confirm Recommendation</Link>
        <Link href={`/bidders/${bidder.id}/review`} className="btn btn-warning">🟡 Request Clarification</Link>
        <Link href={`/bidders/${bidder.id}/review`} className="btn btn-danger">🔴 Override / Reject</Link>
      </div>
    </>
  );
}
