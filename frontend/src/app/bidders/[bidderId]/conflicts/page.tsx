"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useBidWorkspace } from "@/lib/api";

export default function FindingsPage() {
  const { bidderId: bidId } = useParams<{ bidderId: string }>();
  const { bid, assessment, loading, error } = useBidWorkspace(bidId);
  if (loading) return <p>Loading assessment findings…</p>;
  if (error || !bid) return <div className="card card-body" role="alert">{error ?? "Bid not found."}</div>;
  const findings = assessment?.findings ?? [];

  return <>
    <Link href={`/bidders/${encodeURIComponent(bidId)}`} className="card-link">← {bid.bidderName}</Link>
    <h1>Assessment findings</h1>
    {!assessment ? <div className="card card-body">No assessment has been run yet.</div> : findings.length ? findings.map(finding => (
      <article className="card card-body mb-4" key={finding.id}>
        <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}><strong>{finding.findingType}</strong><span className="badge badge-red">{finding.severity}</span></div>
        <p>{finding.message}</p><small>Evidence: {finding.evidenceReference ?? "Not provided"}</small>
      </article>
    )) : <div className="card card-body">The backend reported no findings for this assessment.</div>}
  </>;
}
