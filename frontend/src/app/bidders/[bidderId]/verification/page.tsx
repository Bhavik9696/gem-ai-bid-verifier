"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useBidWorkspace } from "@/lib/api";
import React, { useState } from "react";

function formatValue(key: string, value: any): React.ReactNode {
  if (value === null || value === undefined) return <span style={{ color: '#94a3b8', fontStyle: 'italic' }}>Not available</span>;
  if (typeof value === 'boolean') return value ? "Yes" : "No";
  if (typeof value === 'string') {
    if (value.match(/^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2})?/)) {
      return new Date(value).toLocaleString("en-IN", { day: "2-digit", month: "short", year: "numeric", timeZone: "UTC" });
    }
    return value;
  }
  if (Array.isArray(value)) {
    return value.length > 0 ? (
      <ul style={{ margin: 0, paddingLeft: 16 }}>
        {value.map((v, i) => <li key={i}>{formatValue('', v)}</li>)}
      </ul>
    ) : "None";
  }
  if (typeof value === 'object') {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 4, marginTop: 4 }}>
        {Object.entries(value).map(([k, v]) => (
          <div key={k} style={{ display: 'grid', gridTemplateColumns: '140px 1fr', gap: 8 }}>
            <div style={{ fontWeight: 600, color: '#64748b', fontSize: 11, textTransform: 'capitalize' }}>
              {k.replace(/([A-Z])/g, ' $1').replace(/_/g, ' ')}:
            </div>
            <div style={{ fontSize: 12 }}>{formatValue(k, v)}</div>
          </div>
        ))}
      </div>
    );
  }
  return String(value);
}

function VerificationRow({ result }: { result: any }) {
  const [expanded, setExpanded] = useState(false);
  
  let summary = "";
  if (typeof result.verifiedFacts === 'object' && result.verifiedFacts !== null) {
    const keys = Object.keys(result.verifiedFacts);
    if (keys.length === 0) summary = "No facts verified";
    else summary = `${keys.length} verified facts`;
  } else {
    summary = String(result.verifiedFacts).slice(0, 50) + (String(result.verifiedFacts).length > 50 ? "..." : "");
  }

  return (
    <>
      <tr style={{ borderBottom: expanded ? "none" : "1px solid #f1f5f9" }}>
        <td style={{ fontWeight: 600, color: '#0f172a' }}>{result.source.replace(/_/g, ' ')}</td>
        <td><span className="badge badge-gray">{result.mode}</span></td>
        <td style={{ fontWeight: 500 }}>{result.identifier}</td>
        <td>
          <span className={`badge ${result.status === 'VERIFIED' ? 'badge-green' : result.status === 'FAILED' ? 'badge-red' : 'badge-yellow'}`}>
            {result.status}
          </span>
        </td>
        <td style={{ whiteSpace: "nowrap" }}>{new Date(result.checkedAt).toLocaleString("en-IN", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" })}</td>
        <td style={{ maxWidth: 180, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {result.evidenceReference ?? "—"}
        </td>
        <td>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12 }}>
            <span style={{ fontSize: 12, color: "#64748b", whiteSpace: "nowrap" }}>
              {summary}
            </span>
            <button 
              className="btn btn-secondary btn-sm" 
              onClick={() => setExpanded(!expanded)}
              style={{ whiteSpace: "nowrap" }}
            >
              {expanded ? "Hide Facts" : "View Facts"}
            </button>
          </div>
        </td>
      </tr>
      {expanded && (
        <tr style={{ background: "#f8fafc" }}>
          <td colSpan={7} style={{ padding: "16px 24px", borderTop: "none", borderBottom: "1px solid #e2e8f0" }}>
            <div style={{ background: "white", border: "1px solid #e2e8f0", borderRadius: 8, padding: 16 }}>
              {typeof result.verifiedFacts === 'object' && result.verifiedFacts !== null ? (
                <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                  {Object.entries(result.verifiedFacts).map(([k, v]) => (
                    <div key={k} style={{ display: "flex", gap: 16, borderBottom: "1px solid #f1f5f9", paddingBottom: 8, flexWrap: "wrap" }}>
                      <div style={{ width: 200, fontWeight: 700, color: "#0f172a", fontSize: 12, textTransform: "capitalize", flexShrink: 0 }}>
                        {k.replace(/([A-Z])/g, ' $1').replace(/_/g, ' ')}
                      </div>
                      <div style={{ fontSize: 13, color: "#374151", flex: 1, minWidth: 200, wordBreak: "break-word" }}>
                        {formatValue(k, v)}
                      </div>
                    </div>
                  ))}
                  {Object.keys(result.verifiedFacts).length === 0 && (
                    <div style={{ color: '#64748b', fontSize: 13, fontStyle: 'italic' }}>No verified facts returned.</div>
                  )}
                </div>
              ) : (
                <div style={{ fontSize: 13, wordBreak: "break-word" }}>{formatValue('', result.verifiedFacts)}</div>
              )}
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

export default function VerificationPage() {
  const { bidderId: bidId } = useParams<{ bidderId: string }>();
  const { bid, assessment, loading, error } = useBidWorkspace(bidId);
  
  if (loading) return <div style={{ padding: 40, color: "#64748b" }}>Loading source checks…</div>;
  if (error || !bid) return <div className="card card-body" role="alert" style={{ color: "#ef4444", marginTop: 24 }}>{error ?? "Bid not found."}</div>;
  
  const results = assessment?.verificationResults ?? [];

  return (
    <>
      <div style={{ marginBottom: 24 }}>
        <Link href={`/bidders/${encodeURIComponent(bidId)}`} style={{ display: 'inline-flex', alignItems: 'center', color: '#1a56db', fontSize: 13, textDecoration: 'none', marginBottom: 12, fontWeight: 500 }}>
          <span style={{ marginRight: 6 }}>←</span> Back to {bid.bidderName} Profile
        </Link>
        <h1 style={{ fontSize: 24, fontWeight: 700, color: '#0f172a', margin: 0 }}>Source Verification</h1>
        <p style={{ color: '#64748b', fontSize: 13, marginTop: 4 }}>
          Review external and demo connector checks performed against {bid.bidderName}'s submitted facts.
        </p>
      </div>

      {!assessment ? (
        <div className="card card-body" style={{ color: "#64748b", textAlign: "center", padding: 40 }}>
          No verification has been run for this bid.
        </div>
      ) : (
        <>
          <div className="stat-cards" style={{ gridTemplateColumns: 'repeat(2, 1fr)', maxWidth: 600, marginBottom: 24 }}>
            <div className="stat-card">
              <div className="stat-card-label">Checks Returned</div>
              <div className="stat-card-value">{results.length}</div>
            </div>
            <div className="stat-card">
              <div className="stat-card-label">Coverage</div>
              <div className="stat-card-value" style={{ color: assessment.verificationCoverage >= 80 ? '#10b981' : assessment.verificationCoverage >= 50 ? '#f59e0b' : '#ef4444' }}>
                {assessment.verificationCoverage}%
              </div>
            </div>
          </div>
          
          <div className="card mt-4">
            <div style={{ overflowX: "auto" }}>
              <table className="data-table" style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr>
                    <th>Source</th>
                    <th>Mode</th>
                    <th>Identifier</th>
                    <th>Status</th>
                    <th>Checked</th>
                    <th>Evidence</th>
                    <th>Verified Facts</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map(result => <VerificationRow key={result.id} result={result} />)}
                  {!results.length && (
                    <tr>
                      <td colSpan={7} style={{ textAlign: "center", padding: 32, color: "#64748b" }}>
                        The assessment contains no connector results.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </>
  );
}
