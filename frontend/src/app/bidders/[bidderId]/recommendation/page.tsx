"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useBidWorkspace } from "@/lib/api";

export default function RecommendationPage() {
  const { bidderId: bidId } = useParams<{ bidderId: string }>();
  const { bid, assessment, loading, error } = useBidWorkspace(bidId);
  if (loading) return <p>Loading recommendation…</p>;
  if (error || !bid) return <div className="card card-body" role="alert">{error ?? "Bid not found."}</div>;

  return <>
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12 }}>
      <div><Link href={`/bidders/${encodeURIComponent(bidId)}`} className="card-link">← {bid.bidderName}</Link><h1>Recommendation</h1></div>
      <Link href={`/bidders/${encodeURIComponent(bidId)}/review`} className="btn btn-primary">Officer review</Link>
    </div>
    {!assessment ? <div className="card card-body">No recommendation is available until verification has been run.</div> : <>
      <section className="card card-body">
        <span className="badge badge-blue">{assessment.recommendation}</span>
        <h2>{assessment.riskLevel} risk · {assessment.complianceScore}% compliance</h2>
        <p>{assessment.recommendationSummary ?? "The API did not return a recommendation summary."}</p>
        <small>Evaluated {new Date(assessment.evaluatedAt).toLocaleString("en-IN")}. This is decision support; the officer records the final action.</small>
      </section>
      <section className="card mt-4"><div className="card-header"><span className="card-title">Evidence for review</span></div><div className="card-body">
        {assessment.findings.map(finding => <p key={finding.id}><strong>{finding.severity} · {finding.findingType}</strong>: {finding.message} {finding.evidenceReference && <span>({finding.evidenceReference})</span>}</p>)}
        {!assessment.findings.length && <p>No findings were returned by the backend.</p>}
      </div></section>
    </>}
  </>;
}
