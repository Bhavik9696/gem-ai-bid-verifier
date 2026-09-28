"use client";

import Link from "next/link";
import { useApiData, type Tender } from "@/lib/api";

export default function ImportPage() {
  const tenders = useApiData<Tender[]>("/api/tenders");
  return <>
    <div className="page-header"><h1>Data ingestion</h1><p>Review tenders already seeded or imported into the core API.</p></div>
    <div className="card card-body" style={{ borderLeft: "4px solid #d97706" }}>
      <h2>Import is not available in the current backend</h2>
      <p>The API currently supports listing tenders and bids, running verification, reading assessments and audit events, and recording officer decisions. It does not expose tender/bid import or document-upload endpoints, so this screen does not report simulated uploads as successful.</p>
      <Link className="btn btn-primary" href="/tenders">Browse API tenders</Link>
    </div>
    {tenders.loading && <p>Loading available tenders…</p>}
    {tenders.error && <div className="card card-body" role="alert">{tenders.error}</div>}
    {tenders.data && <div className="card mt-4"><div style={{ overflowX: "auto" }}><table className="data-table">
      <thead><tr><th>Reference</th><th>Tender</th><th>Buyer</th><th>Status</th><th></th></tr></thead>
      <tbody>{tenders.data.map(tender => <tr key={tender.tenderId}><td>{tender.referenceNumber}</td><td>{tender.title}</td><td>{tender.buyerOrganisation}</td><td>{tender.status}</td><td><Link href="/tenders" className="btn btn-secondary btn-sm">Open</Link></td></tr>)}
        {!tenders.data.length && <tr><td colSpan={5}>No tenders are available.</td></tr>}</tbody>
    </table></div></div>}
  </>;
}
