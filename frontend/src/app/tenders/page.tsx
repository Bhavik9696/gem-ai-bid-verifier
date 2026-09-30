"use client";

import Link from "next/link";
import { useState } from "react";
import { useApiData, type Bid, type Tender, type TenderDetail } from "@/lib/api";

function displayDate(value: string | null) {
  return value ? new Date(value).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric", timeZone: "UTC" }) : "—";
}

export default function TendersPage() {
  const tenders = useApiData<Tender[]>("/api/tenders");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const activeId = selectedId ?? tenders.data?.[0]?.tenderId ?? "";
  const [query, setQuery] = useState("");
  const detail = useApiData<TenderDetail>(activeId ? `/api/tenders/${encodeURIComponent(activeId)}` : null);
  const bids = useApiData<Bid[]>(activeId ? `/api/tenders/${encodeURIComponent(activeId)}/bids` : null);

  const filtered = (tenders.data ?? []).filter(tender =>
    `${tender.title} ${tender.referenceNumber} ${tender.buyerOrganisation}`.toLowerCase().includes(query.toLowerCase()),
  );

  if (tenders.loading) return <p>Loading tenders…</p>;
  if (tenders.error) return <div className="card card-body" role="alert">{tenders.error}</div>;

  return (
    <>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 16, marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, color: '#0f172a', margin: 0 }}>Tender Management</h1>
          <p style={{ color: '#64748b', fontSize: 13, marginTop: 4 }}>Manage and monitor compliance across all procurement tenders.</p>
        </div>
        <Link href="/tenders/import" className="btn btn-primary">
          <span style={{ fontSize: 16 }}>+</span> Import Tender
        </Link>
      </div>

      <div className="stat-cards" style={{ gridTemplateColumns: 'repeat(4, 1fr)', marginBottom: 24 }}>
        <div className="stat-card">
          <div className="stat-card-label">Total Tenders</div>
          <div className="stat-card-value">{tenders.data?.length ?? 0}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Active / Open</div>
          <div className="stat-card-value" style={{ color: '#10b981' }}>{tenders.data?.filter(t => t.status === 'ACTIVE').length ?? 0}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Closed</div>
          <div className="stat-card-value">{tenders.data?.filter(t => t.status === 'CLOSED').length ?? 0}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Other Statuses</div>
          <div className="stat-card-value">{(tenders.data?.length ?? 0) - (tenders.data?.filter(t => t.status === 'ACTIVE').length ?? 0) - (tenders.data?.filter(t => t.status === 'CLOSED').length ?? 0)}</div>
        </div>
      </div>

      <div className="dash-grid dash-grid-2-1">
        {/* Left side: Search & Listing */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div className="card">
            <div className="card-header" style={{ padding: "12px 16px", display: "flex", gap: 12, alignItems: "center" }}>
              <input 
                aria-label="Search tenders" 
                className="form-input" 
                style={{ flex: 1 }}
                placeholder="Search by title, reference, or buyer…" 
                value={query} 
                onChange={event => setQuery(event.target.value)} 
              />
              <span className="badge badge-gray">{filtered.length} found</span>
            </div>
            <div style={{ overflowX: "auto" }}>
              <table className="data-table">
                <thead><tr><th>Reference</th><th>Title</th><th>Buyer</th><th>Closing date</th><th>Status</th></tr></thead>
                <tbody>
                  {filtered.map(tender => (
                    <tr 
                      key={tender.tenderId} 
                      onClick={() => setSelectedId(tender.tenderId)}
                      style={{ 
                        cursor: "pointer", 
                        background: activeId === tender.tenderId ? '#f0f9ff' : 'transparent',
                        borderLeft: activeId === tender.tenderId ? '3px solid #1a56db' : '3px solid transparent'
                      }}
                    >
                      <td className="link-cell" style={{ fontWeight: 600 }}>{tender.referenceNumber}</td>
                      <td>
                        <div style={{ maxWidth: 180, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                          {tender.title}
                        </div>
                      </td>
                      <td>
                        <div style={{ maxWidth: 120, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                          {tender.buyerOrganisation}
                        </div>
                      </td>
                      <td>{displayDate(tender.bidClosingDate)}</td>
                      <td>
                        <span className={`badge ${tender.status === 'ACTIVE' ? 'badge-green' : tender.status === 'CLOSED' ? 'badge-gray' : 'badge-blue'}`}>
                          {tender.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                  {!filtered.length && <tr><td colSpan={5}>No tenders match this search.</td></tr>}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right side: Active Tender Details */}
        <div>
          {detail.error && <div className="card card-body" role="alert">{detail.error}</div>}
          {!detail.error && detail.data && (
            <div className="card" style={{ position: "sticky", top: 80 }}>
              <div className="card-header" style={{ flexDirection: "column", alignItems: "flex-start", gap: 8 }}>
                <div style={{ display: "flex", justifyContent: "space-between", width: "100%", alignItems: "flex-start" }}>
                  <span className="card-title" style={{ fontSize: 16 }}>{detail.data.title}</span>
                  <span className={`badge ${detail.data.status === 'ACTIVE' ? 'badge-green' : detail.data.status === 'CLOSED' ? 'badge-gray' : 'badge-blue'}`}>{detail.data.status}</span>
                </div>
                <div style={{ fontSize: 12, color: "#64748b" }}>Ref: {detail.data.referenceNumber}</div>
              </div>
              <div className="card-body">
                <div style={{ display: "flex", flexDirection: "column", gap: 12, marginBottom: 20 }}>
                  <div>
                    <div style={{ fontSize: 10, fontWeight: 700, color: "#64748b", textTransform: "uppercase" }}>Buyer Organization</div>
                    <div style={{ fontSize: 13, fontWeight: 500 }}>{detail.data.buyerOrganisation}</div>
                  </div>
                  <div style={{ display: "flex", gap: 24 }}>
                    <div>
                      <div style={{ fontSize: 10, fontWeight: 700, color: "#64748b", textTransform: "uppercase" }}>Category</div>
                      <div style={{ fontSize: 13, fontWeight: 500 }}>{detail.data.category}</div>
                    </div>
                    <div>
                      <div style={{ fontSize: 10, fontWeight: 700, color: "#64748b", textTransform: "uppercase" }}>Estimated Value</div>
                      <div style={{ fontSize: 13, fontWeight: 500 }}>
                        {detail.data.estimatedValue === null ? "—" : new Intl.NumberFormat("en-IN", { style: "currency", currency: detail.data.currency, maximumFractionDigits: 0 }).format(detail.data.estimatedValue)}
                      </div>
                    </div>
                  </div>
                  <div style={{ display: "flex", gap: 24 }}>
                    <div>
                      <div style={{ fontSize: 10, fontWeight: 700, color: "#64748b", textTransform: "uppercase" }}>Published</div>
                      <div style={{ fontSize: 13, fontWeight: 500 }}>{displayDate(detail.data.publishedDate)}</div>
                    </div>
                    <div>
                      <div style={{ fontSize: 10, fontWeight: 700, color: "#64748b", textTransform: "uppercase" }}>Closes</div>
                      <div style={{ fontSize: 13, fontWeight: 500 }}>{displayDate(detail.data.bidClosingDate)}</div>
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: 10, fontWeight: 700, color: "#64748b", textTransform: "uppercase" }}>Rulebook</div>
                    <div style={{ fontSize: 13, fontWeight: 500 }}><span className="badge badge-blue">v{detail.data.rulebookVersion}</span></div>
                  </div>
                </div>

                <div style={{ borderTop: "1px solid #e2e8f0", paddingTop: 16, marginBottom: 16 }}>
                  <div style={{ fontSize: 12, fontWeight: 700, marginBottom: 8, color: "#0f172a" }}>Mandatory Documents</div>
                  {detail.data.mandatoryDocuments.length ? (
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                      {detail.data.mandatoryDocuments.map(doc => (
                        <span key={doc} className="badge badge-gray">{doc}</span>
                      ))}
                    </div>
                  ) : (
                    <p style={{ fontSize: 12, color: "#64748b" }}>No mandatory documents listed.</p>
                  )}
                </div>

                <div style={{ borderTop: "1px solid #e2e8f0", paddingTop: 16 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
                    <div style={{ fontSize: 12, fontWeight: 700, color: "#0f172a" }}>Submitted Bids</div>
                    <span className="badge badge-blue">{bids.data?.length ?? 0}</span>
                  </div>
                  
                  {bids.error && <p role="alert" style={{ color: "#ef4444", fontSize: 12 }}>{bids.error}</p>}
                  
                  <div style={{ display: "flex", flexDirection: "column", gap: 6, maxHeight: 200, overflowY: "auto", paddingRight: 4 }}>
                    {(bids.data ?? []).map(bid => (
                      <Link 
                        key={bid.bidId} 
                        href={`/bidders/${encodeURIComponent(bid.bidId)}`}
                        className="quick-action" 
                        style={{ padding: "8px 12px", marginBottom: 0, textDecoration: "none" }}
                      >
                        <div className="qa-left">
                          <div className="qa-text">
                            <div className="qa-label" style={{ fontSize: 12 }}>{bid.bidderName}</div>
                            <div style={{ fontSize: 10, color: "#64748b" }}>{bid.bidId}</div>
                          </div>
                        </div>
                        <span className={`badge ${bid.riskLevel === 'CRITICAL' || bid.riskLevel === 'HIGH' ? 'badge-red' : bid.riskLevel === 'MEDIUM' ? 'badge-yellow' : bid.riskLevel === 'LOW' ? 'badge-green' : 'badge-gray'}`}>
                          {bid.riskLevel ?? "Pending"}
                        </span>
                      </Link>
                    ))}
                    {!bids.data?.length && !bids.error && (
                      <p style={{ fontSize: 12, color: "#64748b", textAlign: "center", padding: "12px 0" }}>
                        No bids received yet.
                      </p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}
          {!detail.data && !detail.error && (
            <div className="card card-body" style={{ textAlign: "center", padding: 40, color: "#64748b" }}>
              Select a tender to view its details.
            </div>
          )}
        </div>
      </div>
    </>
  );
}
