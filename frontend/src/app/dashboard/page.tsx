"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { apiRequest, useApiData, type Bid, type Tender } from "@/lib/api";

export default function DashboardPage() {
  const tenders = useApiData<Tender[]>("/api/tenders");
  const [bidResult, setBidResult] = useState<{ key: string; bids: Bid[]; error: string | null } | null>(null);
  const bidKey = (tenders.data ?? []).map(tender => tender.tenderId).join("|");

  useEffect(() => {
    if (!tenders.data) return;
    let active = true;
    Promise.all(tenders.data.map(tender =>
      apiRequest<Bid[]>(`/api/tenders/${encodeURIComponent(tender.tenderId)}/bids`),
    )).then(result => {
      if (active) setBidResult({ key: bidKey, bids: result.flat(), error: null });
    }).catch(error => {
      if (active) setBidResult({ key: bidKey, bids: [], error: error instanceof Error ? error.message : "Could not load bids." });
    });
    return () => { active = false; };
  }, [tenders.data, bidKey]);

  const bids = bidResult?.key === bidKey ? bidResult.bids : [];
  const bidsError = bidResult?.key === bidKey ? bidResult.error : null;
  const loadingBids = Boolean(tenders.data) && bidResult?.key !== bidKey;
  const assessed = bids.filter(bid => bid.complianceScore !== null);
  const reviewCount = bids.filter(bid => ["HIGH", "CRITICAL"].includes((bid.riskLevel ?? "").toUpperCase())).length;

  const totalBids = bids.length;
  const unassessedBids = totalBids - assessed.length;

  const riskCounts = bids.reduce((acc, bid) => {
    const risk = bid.riskLevel || 'PENDING';
    acc[risk] = (acc[risk] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const statusCounts = bids.reduce((acc, bid) => {
    const status = bid.status || 'UNKNOWN';
    acc[status] = (acc[status] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  if (tenders.loading) return <p>Loading ComplianceOS data…</p>;
  if (tenders.error) return <div className="card card-body"><strong>Backend unavailable</strong><p>{tenders.error}</p></div>;

  return (
    <>
      <div className="demo-banner">Connector results are from the backend demo environment. Check each source mode in its verification record.</div>
      <div className="stat-cards">
        {[
          ["Active Tenders", tenders.data?.length ?? 0],
          ["Total Bids", totalBids],
          ["Bids Assessed", assessed.length],
          ["Action Required", reviewCount],
        ].map(([label, value]) => (
          <div className="stat-card" key={label}>
            <div className="stat-card-label">{label}</div>
            <div className="stat-card-value">{loadingBids ? "…" : value}</div>
            <div className="stat-card-sub">Live total from core API</div>
          </div>
        ))}
      </div>

      {bidsError && <div className="card card-body" role="alert">{bidsError}</div>}

      {/* Analytics Visualizations */}
      <div className="dash-grid dash-grid-3 mt-4">
        {/* Risk Distribution */}
        <section className="card">
          <div className="card-header"><span className="card-title">Risk Distribution</span></div>
          <div className="card-body">
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
              <div className="donut-wrap" style={{ width: 80, height: 80 }}>
                <svg viewBox="0 0 36 36" className="donut-svg">
                  <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#e2e8f0" strokeWidth="4"/>
                  <path strokeDasharray={`${((riskCounts['HIGH'] || 0) + (riskCounts['CRITICAL'] || 0)) / (totalBids || 1) * 100}, 100`} d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#ef4444" strokeWidth="4"/>
                </svg>
                <div className="donut-label" style={{ marginTop: 2 }}>
                  <div className="donut-val" style={{ fontSize: 16 }}>{reviewCount}</div>
                  <div className="donut-sub">High Risk</div>
                </div>
              </div>
              <div style={{ flex: 1, paddingLeft: 16, fontSize: 13, display: 'flex', flexDirection: 'column', gap: 6, justifyContent: 'center' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: '#059669', fontWeight: 600 }}>Low Risk</span> <span>{riskCounts['LOW'] || 0}</span></div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: '#d97706', fontWeight: 600 }}>Medium</span> <span>{riskCounts['MEDIUM'] || 0}</span></div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: '#dc2626', fontWeight: 600 }}>High/Critical</span> <span>{(riskCounts['HIGH'] || 0) + (riskCounts['CRITICAL'] || 0)}</span></div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: '#64748b', fontWeight: 600 }}>Pending</span> <span>{riskCounts['PENDING'] || 0}</span></div>
              </div>
            </div>
          </div>
        </section>

        {/* Assessment Progress */}
        <section className="card">
          <div className="card-header"><span className="card-title">Assessment Progress</span></div>
          <div className="card-body">
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
              <div className="donut-wrap" style={{ width: 80, height: 80 }}>
                <svg viewBox="0 0 36 36" className="donut-svg">
                  <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#e2e8f0" strokeWidth="4"/>
                  <path strokeDasharray={`${assessed.length / (totalBids || 1) * 100}, 100`} d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#3b82f6" strokeWidth="4"/>
                </svg>
                <div className="donut-label" style={{ marginTop: 2 }}>
                  <div className="donut-val" style={{ fontSize: 16 }}>{Math.round(assessed.length / (totalBids || 1) * 100)}%</div>
                  <div className="donut-sub">Assessed</div>
                </div>
              </div>
              <div style={{ flex: 1, paddingLeft: 16, fontSize: 13, display: 'flex', flexDirection: 'column', gap: 6, justifyContent: 'center' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: '#2563eb', fontWeight: 600 }}>Assessed</span> <span>{assessed.length}</span></div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: '#64748b', fontWeight: 600 }}>Unassessed</span> <span>{unassessedBids}</span></div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: '#0f172a', fontWeight: 600 }}>Total Bids</span> <span>{totalBids}</span></div>
              </div>
            </div>
          </div>
        </section>

        {/* Bid Status Breakdown */}
        <section className="card">
          <div className="card-header"><span className="card-title">Bid Statuses</span></div>
          <div className="card-body" style={{ maxHeight: 120, overflowY: 'auto' }}>
            {Object.entries(statusCounts).map(([status, count]) => (
              <div key={status} style={{ marginBottom: 12 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, marginBottom: 4 }}>
                  <strong>{status.replace(/_/g, ' ')}</strong>
                  <span>{count as number}</span>
                </div>
                <div className="progress-bar">
                  <div 
                    className="progress-bar-fill progress-blue" 
                    style={{ width: `${((count as number) / (totalBids || 1)) * 100}%` }}
                  ></div>
                </div>
              </div>
            ))}
            {totalBids === 0 && <p style={{ fontSize: 13 }}>No bids available.</p>}
          </div>
        </section>
      </div>

      <div className="dash-grid dash-grid-2 mt-4">
        <section className="card">
          <div className="card-header"><span className="card-title">Tenders</span><Link href="/tenders" className="card-link">View all →</Link></div>
          <div style={{ overflowX: "auto" }}>
            <table className="data-table">
              <thead><tr><th>Reference</th><th>Title</th><th>Buyer</th><th>Closing</th><th>Status</th></tr></thead>
              <tbody>
                {(tenders.data ?? []).map(tender => (
                  <tr key={tender.tenderId}>
                    <td><Link href="/tenders" className="link-cell">{tender.referenceNumber}</Link></td>
                    <td>{tender.title}</td><td>{tender.buyerOrganisation}</td>
                    <td>{tender.bidClosingDate ?? "—"}</td>
                    <td>
                      <span className={`badge ${tender.status === 'ACTIVE' ? 'badge-green' : 'badge-gray'}`}>
                        {tender.status}
                      </span>
                    </td>
                  </tr>
                ))}
                {!tenders.data?.length && <tr><td colSpan={5}>No tenders available.</td></tr>}
              </tbody>
            </table>
          </div>
        </section>

        <section className="card">
          <div className="card-header"><span className="card-title">Bids requiring attention</span><Link href="/bidders" className="card-link">View bids →</Link></div>
          <div style={{ overflowX: "auto" }}>
            <table className="data-table">
              <thead><tr><th>Bidder</th><th>Bid ID</th><th>Compliance</th><th>Risk</th><th></th></tr></thead>
              <tbody>
                {bids.filter(bid => bid.riskLevel || bid.complianceScore === null).slice(0, 8).map(bid => (
                  <tr key={bid.bidId}>
                    <td>{bid.bidderName}</td><td>{bid.bidId}</td>
                    <td>{bid.complianceScore === null ? "Not assessed" : `${bid.complianceScore}%`}</td>
                    <td>
                      <span className={`badge ${bid.riskLevel === 'CRITICAL' || bid.riskLevel === 'HIGH' ? 'badge-red' : bid.riskLevel === 'MEDIUM' ? 'badge-yellow' : bid.riskLevel === 'LOW' ? 'badge-green' : 'badge-gray'}`}>
                        {bid.riskLevel ?? "Pending"}
                      </span>
                    </td>
                    <td><Link href={`/bidders/${encodeURIComponent(bid.bidId)}`} className="btn btn-secondary btn-sm">Review</Link></td>
                  </tr>
                ))}
                {!bids.length && !loadingBids && <tr><td colSpan={5}>No bids are available for the listed tenders.</td></tr>}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </>
  );
}
