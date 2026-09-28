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

  if (tenders.loading) return <p>Loading ComplianceOS data…</p>;
  if (tenders.error) return <div className="card card-body"><strong>Backend unavailable</strong><p>{tenders.error}</p></div>;

  return (
    <>
      <div className="demo-banner">Connector results are from the backend demo environment. Check each source mode in its verification record.</div>
      <div className="stat-cards">
        {[
          ["Tenders", tenders.data?.length ?? 0],
          ["Bids", bids.length],
          ["Assessed", assessed.length],
          ["High / Critical risk", reviewCount],
        ].map(([label, value]) => (
          <div className="stat-card" key={label}>
            <div className="stat-card-label">{label}</div>
            <div className="stat-card-value">{loadingBids ? "…" : value}</div>
            <div className="stat-card-sub">Live totals from the core API</div>
          </div>
        ))}
      </div>

      {bidsError && <div className="card card-body" role="alert">{bidsError}</div>}
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
                    <td>{tender.bidClosingDate ?? "—"}</td><td>{tender.status}</td>
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
                    <td>{bid.riskLevel ?? "Pending"}</td>
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
