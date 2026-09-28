"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useBidWorkspace } from "@/lib/api";

export default function DocumentsPage() {
  const { bidderId: bidId } = useParams<{ bidderId: string }>();
  const { bid, assessment, loading, error } = useBidWorkspace(bidId);
  if (loading) return <p>Loading extracted evidence…</p>;
  if (error || !bid) return <div className="card card-body" role="alert">{error ?? "Bid not found."}</div>;

  const facts = assessment?.extractedFacts ?? [];
  return <>
    <Link href={`/bidders/${encodeURIComponent(bidId)}`} className="card-link">← {bid.bidderName}</Link>
    <h1>Extracted evidence</h1>
    <div className="demo-banner">The API returns extracted fields and references, but does not expose uploaded files or document metadata.</div>
    {!assessment ? <div className="card card-body">Run verification before extracted facts are available.</div> : (
      <div className="card"><div style={{ overflowX: "auto" }}><table className="data-table">
        <thead><tr><th>Field</th><th>Value</th><th>Confidence</th><th>Document ID</th><th>Page</th><th>Evidence</th></tr></thead>
        <tbody>{facts.map(fact => <tr key={fact.id}><td>{fact.field}</td><td>{fact.value ?? "—"}</td><td>{Math.round(fact.confidence * 100)}%</td><td>{fact.documentId ?? "—"}</td><td>{fact.page}</td><td>{fact.evidence ?? "—"}</td></tr>)}
          {!facts.length && <tr><td colSpan={6}>No extracted facts are available for this bid.</td></tr>}</tbody>
      </table></div></div>
    )}
  </>;
}
