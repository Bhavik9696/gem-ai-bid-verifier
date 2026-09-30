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
  const [searchQuery, setSearchQuery] = useState("");
  const bids = useApiData<Bid[]>(tenderId ? `/api/tenders/${encodeURIComponent(tenderId)}/bids` : null);

  const rows = (bids.data ?? []).filter(bid => {
    if (searchQuery && !`${bid.bidderName} ${bid.bidId}`.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false;
    }
    if (filter === "All") return true;
    if (filter === "Not assessed") return bid.complianceScore === null;
    return bid.riskLevel?.toLowerCase() === filter.toLowerCase();
  });

  if (tenders.loading) return <p>Loading tenders…</p>;
  if (tenders.error) return <div className="card card-body" role="alert">{tenders.error}</div>;

  const totalBids = bids.data?.length ?? 0;
  const assessedBids = (bids.data ?? []).filter(b => b.complianceScore !== null).length;
  const highRiskBids = (bids.data ?? []).filter(b => ["HIGH", "CRITICAL"].includes((b.riskLevel ?? "").toUpperCase())).length;

  return (
    <>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: 24, flexWrap: "wrap", gap: 16 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, color: '#0f172a', margin: 0 }}>Bidder Management</h1>
          <p style={{ color: '#64748b', fontSize: 13, marginTop: 4 }}>Review bidder profiles, compliance assessments, and verification outcomes.</p>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          <label style={{ fontSize: 11, fontWeight: 700, color: '#64748b', textTransform: 'uppercase' }}>Select Tender Context</label>
          <select className="form-select" aria-label="Select tender" value={tenderId} onChange={event => setSelectedTenderId(event.target.value)} style={{ minWidth: 320 }}>
            {(tenders.data ?? []).map(tender => <option key={tender.tenderId} value={tender.tenderId}>{tender.referenceNumber} · {tender.title}</option>)}
          </select>
        </div>
      </div>

      <div className="stat-cards" style={{ gridTemplateColumns: 'repeat(4, 1fr)', marginBottom: 24 }}>
        <div className="stat-card">
          <div className="stat-card-label">Total Bids</div>
          <div className="stat-card-value">{totalBids}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Assessed</div>
          <div className="stat-card-value" style={{ color: '#10b981' }}>{assessedBids}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Pending Assessment</div>
          <div className="stat-card-value">{totalBids - assessedBids}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">High / Critical Risk</div>
          <div className="stat-card-value" style={{ color: '#ef4444' }}>{highRiskBids}</div>
        </div>
      </div>

      <div className="card">
        <div className="card-header" style={{ padding: "12px 16px", display: "flex", flexWrap: "wrap", gap: 16, alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ display: "flex", gap: 8, alignItems: "center", overflowX: "auto" }}>
            {["All", "Not assessed", "Low", "Moderate", "High", "Critical"].map(option => (
              <button 
                key={option} 
                className={`filter-btn${filter === option ? " active" : ""}`} 
                onClick={() => setFilter(option)}
              >
                {option}
              </button>
            ))}
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <input 
              className="form-input" 
              placeholder="Search bidders or ID…" 
              value={searchQuery} 
              onChange={e => setSearchQuery(e.target.value)} 
              style={{ minWidth: 260 }}
            />
            <span className="badge badge-gray">{rows.length} bids</span>
          </div>
        </div>

        {bids.loading && <div style={{ padding: 20, color: "#64748b" }}>Loading bids…</div>}
        {bids.error && <div className="card-body" role="alert" style={{ color: "#ef4444" }}>{bids.error}</div>}
        {!bids.loading && !bids.error && (
          <div style={{ overflowX: "auto" }}>
            <table className="data-table">
              <thead><tr><th>Bidder</th><th>Bid ID</th><th>Submitted</th><th>Amount</th><th>Compliance</th><th>Risk</th><th>Recommendation</th><th></th></tr></thead>
              <tbody>
                {rows.map(bid => (
                  <tr key={bid.bidId}>
                    <td style={{ fontWeight: 600, color: '#0f172a' }}>{bid.bidderName}</td>
                    <td style={{ color: '#64748b' }}>{bid.bidId}</td>
                    <td>{bid.submittedAt ? new Date(bid.submittedAt).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric", timeZone: "UTC" }) : "—"}</td>
                    <td style={{ fontWeight: 500 }}>{new Intl.NumberFormat("en-IN", { style: "currency", currency: bid.currency, maximumFractionDigits: 0 }).format(bid.bidAmount)}</td>
                    <td>
                      {bid.complianceScore === null ? (
                        <span style={{ color: '#94a3b8', fontStyle: 'italic' }}>Not assessed</span>
                      ) : (
                        <span style={{ fontWeight: 600, color: bid.complianceScore >= 80 ? '#10b981' : bid.complianceScore >= 50 ? '#f59e0b' : '#ef4444' }}>
                          {bid.complianceScore}%
                        </span>
                      )}
                    </td>
                    <td><span className={`badge ${riskBadge(bid.riskLevel)}`}>{bid.riskLevel ?? "Pending"}</span></td>
                    <td style={{ fontSize: 12 }}>{bid.recommendation ? bid.recommendation.replace(/_/g, ' ') : "—"}</td>
                    <td style={{ textAlign: "right" }}>
                      <Link href={`/bidders/${encodeURIComponent(bid.bidId)}`} className="btn btn-secondary btn-sm" style={{ whiteSpace: "nowrap" }}>
                        View Profile
                      </Link>
                    </td>
                  </tr>
                ))}
                {!rows.length && <tr><td colSpan={8} style={{ textAlign: "center", padding: 24, color: "#64748b" }}>No bids match this filter.</td></tr>}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}
