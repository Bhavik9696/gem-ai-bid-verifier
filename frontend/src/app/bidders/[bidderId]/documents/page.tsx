"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useBidWorkspace } from "@/lib/api";
import React from "react";

function formatFieldLabel(field: string): string {
  const map: Record<string, string> = {
    pan: "PAN",
    gstin: "GSTIN",
    gstLegalName: "GST Legal Name",
    udyamNumber: "Udyam Number",
    localContentPercentage: "Local Content Percentage",
  };
  if (map[field]) return map[field];
  
  return field
    .replace(/([A-Z])/g, ' $1')
    .replace(/_/g, ' ')
    .replace(/^./, str => str.toUpperCase())
    .trim();
}

export default function DocumentsPage() {
  const { bidderId: bidId } = useParams<{ bidderId: string }>();
  const { bid, assessment, loading, error } = useBidWorkspace(bidId);
  
  if (loading) return <div style={{ padding: 40, color: "#64748b" }}>Loading extracted evidence…</div>;
  if (error || !bid) return <div className="card card-body" role="alert" style={{ color: "#ef4444", marginTop: 24 }}>{error ?? "Bid not found."}</div>;

  const facts = assessment?.extractedFacts ?? [];
  
  return (
    <>
      <div style={{ marginBottom: 24 }}>
        <Link href={`/bidders/${encodeURIComponent(bidId)}`} style={{ display: 'inline-flex', alignItems: 'center', color: '#1a56db', fontSize: 13, textDecoration: 'none', marginBottom: 12, fontWeight: 500 }}>
          <span style={{ marginRight: 6 }}>←</span> Back to {bid.bidderName} Profile
        </Link>
        <h1 style={{ fontSize: 24, fontWeight: 700, color: '#0f172a', margin: 0 }}>Extracted Evidence</h1>
        <p style={{ color: '#64748b', fontSize: 13, marginTop: 4 }}>
          Review the values extracted from {bid.bidderName}'s uploaded documents and the evidence supporting them.
        </p>
      </div>

      <div className="demo-banner">The API returns extracted fields and references, but does not expose uploaded files or document metadata.</div>
      
      {!assessment ? (
        <div className="card card-body" style={{ color: "#64748b", textAlign: "center", padding: 40 }}>
          Run verification before extracted facts are available.
        </div>
      ) : (
        <div className="card">
          <div style={{ overflowX: "auto" }}>
            <table className="data-table" style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  <th>Field</th>
                  <th>Extracted Value</th>
                  <th>Confidence</th>
                  <th>Document Ref</th>
                  <th>Supporting Evidence</th>
                </tr>
              </thead>
              <tbody>
                {facts.map(fact => (
                  <tr key={fact.id} style={{ borderBottom: "1px solid #f1f5f9" }}>
                    <td style={{ fontWeight: 600, color: "#374151", whiteSpace: "nowrap", verticalAlign: "top", paddingTop: 16 }}>
                      {formatFieldLabel(fact.field)}
                    </td>
                    <td style={{ fontWeight: 700, color: "#0f172a", verticalAlign: "top", paddingTop: 16 }}>
                      {fact.value !== null && fact.value !== undefined ? (
                        fact.value
                      ) : (
                        <span style={{ color: '#94a3b8', fontStyle: 'italic', fontWeight: 400 }}>Not found</span>
                      )}
                    </td>
                    <td style={{ verticalAlign: "top", paddingTop: 16 }}>
                      <span className={`badge ${fact.confidence >= 0.8 ? 'badge-green' : fact.confidence >= 0.5 ? 'badge-yellow' : 'badge-red'}`}>
                        {Math.round(fact.confidence * 100)}%
                      </span>
                    </td>
                    <td style={{ verticalAlign: "top", paddingTop: 16 }}>
                      <div style={{ fontSize: 12, fontWeight: 600, color: "#0f172a", whiteSpace: "nowrap" }}>
                        {fact.documentId ?? "—"}
                      </div>
                      {fact.page && (
                        <div style={{ fontSize: 11, color: "#64748b", marginTop: 4 }}>Page {fact.page}</div>
                      )}
                    </td>
                    <td style={{ minWidth: 280, maxWidth: 450, verticalAlign: "top", paddingTop: 16, paddingBottom: 16 }}>
                      {fact.evidence ? (
                        <div style={{ 
                          fontSize: 13, 
                          color: "#475569", 
                          lineHeight: 1.5, 
                          wordBreak: "break-word", 
                          background: "#f8fafc", 
                          padding: "10px 14px", 
                          borderRadius: 6, 
                          border: "1px solid #e2e8f0",
                          fontStyle: "italic"
                        }}>
                          "{fact.evidence}"
                        </div>
                      ) : (
                        <span style={{ color: '#94a3b8', fontStyle: 'italic', fontSize: 13 }}>No evidence text</span>
                      )}
                    </td>
                  </tr>
                ))}
                {!facts.length && (
                  <tr>
                    <td colSpan={5} style={{ textAlign: "center", padding: 32, color: "#64748b" }}>
                      No extracted facts are available for this bid.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  );
}
