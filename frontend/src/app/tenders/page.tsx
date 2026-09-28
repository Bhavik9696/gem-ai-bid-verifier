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
      <div className="page-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 16 }}>
        <div><h1>All Tenders</h1><p>Tenders and bids currently available in the core API.</p></div>
        <Link href="/tenders/import" className="btn btn-secondary">Import capability</Link>
      </div>
      <div className="filter-bar">
        <input aria-label="Search tenders" className="form-input" placeholder="Search tenders…" value={query} onChange={event => setQuery(event.target.value)} />
        <span className="badge badge-gray">{filtered.length} tenders</span>
      </div>
      <div className="card">
        <div style={{ overflowX: "auto" }}>
          <table className="data-table">
            <thead><tr><th>Reference</th><th>Title</th><th>Buyer</th><th>Closing date</th><th>Bids</th><th>Status</th><th></th></tr></thead>
            <tbody>
              {filtered.map(tender => (
                <tr key={tender.tenderId}>
                  <td><button className="link-cell" onClick={() => setSelectedId(tender.tenderId)}>{tender.referenceNumber}</button></td>
                  <td>{tender.title}</td><td>{tender.buyerOrganisation}</td><td>{displayDate(tender.bidClosingDate)}</td>
                  <td>{activeId === tender.tenderId ? bids.data?.length ?? "…" : "—"}</td><td>{tender.status}</td>
                  <td><button className="btn btn-secondary btn-sm" onClick={() => setSelectedId(tender.tenderId)}>Details</button></td>
                </tr>
              ))}
              {!filtered.length && <tr><td colSpan={7}>No tenders match this search.</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
      {detail.error && <div className="card card-body mt-4" role="alert">{detail.error}</div>}
      {detail.data && (
        <section className="card mt-4">
          <div className="card-header"><span className="card-title">{detail.data.title}</span><span className="badge badge-blue">Rulebook {detail.data.rulebookVersion}</span></div>
          <div className="card-body">
            <p>{detail.data.referenceNumber} · {detail.data.buyerOrganisation} · closes {displayDate(detail.data.bidClosingDate)}</p>
            <p>Category: {detail.data.category} · Estimated value: {detail.data.estimatedValue === null ? "—" : new Intl.NumberFormat("en-IN", { style: "currency", currency: detail.data.currency, maximumFractionDigits: 0 }).format(detail.data.estimatedValue)}</p>
            <h3>Mandatory documents</h3>
            {detail.data.mandatoryDocuments.length ? <ul>{detail.data.mandatoryDocuments.map(document => <li key={document}>{document}</li>)}</ul> : <p>No mandatory documents listed.</p>}
            <h3>Bids ({bids.data?.length ?? 0})</h3>
            {bids.error && <p role="alert">{bids.error}</p>}
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              {(bids.data ?? []).map(bid => <Link className="btn btn-secondary btn-sm" href={`/bidders/${encodeURIComponent(bid.bidId)}`} key={bid.bidId}>{bid.bidderName} · {bid.bidId}</Link>)}
            </div>
          </div>
        </section>
      )}
    </>
  );
}
