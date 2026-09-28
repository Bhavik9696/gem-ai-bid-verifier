"use client";

"use client";
import Link from "next/link";
import { useState } from "react";
import { useApiData, type Bid, type Tender } from "@/lib/api";

function riskBadge(risk: string | null) {
  if (!risk) return "badge-gray";
  const value = risk.toUpperCase();
  if (value === "LOW") return "badge-green";
  if (value === "MODERATE" || value === "MEDIUM") return "badge-yellow";
  return "badge-red";
}

export default function BiddersPage() {
  const tenders = useApiData<Tender[]>("/api/tenders");
  const [selectedTenderId, setSelectedTenderId] = useState<string | null>(null);
  const tenderId = selectedTenderId ?? tenders.data?.[0]?.tenderId ?? "";
  const [filter, setFilter] = useState("All");
  const bids = useApiData<Bid[]>(tenderId ? `/api/tenders/${encodeURIComponent(tenderId)}/bids` : null);

  const rows = (bids.data ?? []).filter(bid => {
    if (filter === "All") return true;
    if (filter === "Not assessed") return bid.complianceScore === null;
    return bid.riskLevel?.toLowerCase() === filter.toLowerCase();
  });

  if (tenders.loading) return <p>Loading tenders…</p>;
  if (tenders.error) return <div className="card card-body" role="alert">{tenders.error}</div>;

  return (
    <>
      <div className="demo-banner">Bid records come from the core API. A missing assessment is shown as pending, not inferred.</div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 16, marginBottom: 20 }}>
        <div><h1 style={{ margin: 0 }}>Bids</h1><p style={{ color: "#64748b" }}>Open a bid to run or review its compliance assessment.</p></div>
        <select className="form-select" aria-label="Select tender" value={tenderId} onChange={event => setSelectedTenderId(event.target.value)}>
          {(tenders.data ?? []).map(tender => <option key={tender.tenderId} value={tender.tenderId}>{tender.referenceNumber} · {tender.title}</option>)}
        </select>
      </div>
      <div className="filter-bar">
        {["All", "Not assessed", "Low", "Moderate", "High", "Critical"].map(option => <button key={option} className={`filter-btn${filter === option ? " active" : ""}`} onClick={() => setFilter(option)}>{option}</button>)}
        <span className="badge badge-gray">{rows.length} bids</span>
      </div>
      {bids.loading && <p>Loading bids…</p>}
      {bids.error && <div className="card card-body" role="alert">{bids.error}</div>}
      {!bids.loading && !bids.error && (
        <div className="card">
          <div style={{ overflowX: "auto" }}>
            <table className="data-table">
              <thead><tr><th>Bidder</th><th>Bid ID</th><th>Submitted</th><th>Amount</th><th>Compliance</th><th>Risk</th><th>Recommendation</th><th></th></tr></thead>
              <tbody>
                {rows.map(bid => (
                  <tr key={bid.bidId}>
                    <td style={{ fontWeight: 600 }}>{bid.bidderName}</td><td>{bid.bidId}</td>
                    <td>{bid.submittedAt ? new Date(bid.submittedAt).toLocaleString("en-IN") : "—"}</td>
                    <td>{new Intl.NumberFormat("en-IN", { style: "currency", currency: bid.currency, maximumFractionDigits: 0 }).format(bid.bidAmount)}</td>
                    <td>{bid.complianceScore === null ? "Not assessed" : `${bid.complianceScore}%`}</td>
                    <td><span className={`badge ${riskBadge(bid.riskLevel)}`}>{bid.riskLevel ?? "Pending"}</span></td>
                    <td>{bid.recommendation ?? "—"}</td>
                    <td><Link href={`/bidders/${encodeURIComponent(bid.bidId)}`} className="btn btn-primary btn-sm">Open bid</Link></td>
                  </tr>
                ))}
                {!rows.length && <tr><td colSpan={8}>No bids match this filter.</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  );
}
