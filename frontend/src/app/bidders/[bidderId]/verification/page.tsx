"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useBidWorkspace } from "@/lib/api";

export default function VerificationPage() {
  const { bidderId: bidId } = useParams<{ bidderId: string }>();
  const { bid, assessment, loading, error } = useBidWorkspace(bidId);
  if (loading) return <p>Loading source checks…</p>;
  if (error || !bid) return <div className="card card-body" role="alert">{error ?? "Bid not found."}</div>;
  const results = assessment?.verificationResults ?? [];

  return <>
    <Link href={`/bidders/${encodeURIComponent(bidId)}`} className="card-link">← {bid.bidderName}</Link>
    <h1>Source verification</h1>
    {!assessment ? <div className="card card-body">No verification has been run for this bid.</div> : <>
      <div className="stat-cards"><div className="stat-card"><div className="stat-card-label">Checks returned</div><div className="stat-card-value">{results.length}</div></div><div className="stat-card"><div className="stat-card-label">Coverage</div><div className="stat-card-value">{assessment.verificationCoverage}%</div></div></div>
      <div className="card mt-4"><div style={{ overflowX: "auto" }}><table className="data-table">
        <thead><tr><th>Source</th><th>Mode</th><th>Identifier</th><th>Status</th><th>Checked</th><th>Evidence</th><th>Verified facts</th></tr></thead>
        <tbody>{results.map(result => <tr key={result.id}><td>{result.source}</td><td>{result.mode}</td><td>{result.identifier}</td><td>{result.status}</td><td>{new Date(result.checkedAt).toLocaleString("en-IN")}</td><td>{result.evidenceReference ?? "—"}</td><td><pre style={{ whiteSpace: "pre-wrap", margin: 0 }}>{JSON.stringify(result.verifiedFacts, null, 2)}</pre></td></tr>)}
          {!results.length && <tr><td colSpan={7}>The assessment contains no connector results.</td></tr>}</tbody>
      </table></div></div>
    </>}
  </>;
}
