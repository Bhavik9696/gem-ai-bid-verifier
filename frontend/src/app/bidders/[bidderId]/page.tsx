"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { runVerification, useBidWorkspace } from "@/lib/api";

const tabs = [
  ["Documents", "documents"], ["Verification", "verification"], ["Findings", "conflicts"],
  ["Rules", "compliance"], ["Recommendation", "recommendation"], ["Officer review", "review"],
];

export default function BidProfilePage() {
  const { bidderId: bidId } = useParams<{ bidderId: string }>();
  const { bid, assessment, loading, error, reload } = useBidWorkspace(bidId);
  const [running, setRunning] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  async function startVerification() {
    setRunning(true);
    setActionError(null);
    try {
      await runVerification(bidId);
      reload();
    } catch (reason) {
      setActionError(reason instanceof Error ? reason.message : "Verification failed.");
    } finally {
      setRunning(false);
    }
  }

  if (loading) return <p>Loading bid…</p>;
  if (error || !bid) return <div className="card card-body" role="alert">{error ?? "Bid not found."}</div>;

  return (
    <>
      <div className="demo-banner">Bid ID: {bid.bidId} · Connector mode and evidence are shown in the assessment returned by the backend.</div>
      <section className="card">
        <div className="card-header"><div><h1 style={{ margin: 0 }}>{bid.bidderName}</h1><p>{bid.bidId} · Tender {bid.tenderId}</p></div><span className="badge badge-gray">{bid.status}</span></div>
        <div className="card-body">
          <div className="stat-cards">
            {[
              ["Bid amount", new Intl.NumberFormat("en-IN", { style: "currency", currency: bid.currency, maximumFractionDigits: 0 }).format(bid.bidAmount)],
              ["Compliance", assessment ? `${assessment.complianceScore}%` : "Not assessed"],
              ["Verification coverage", assessment ? `${assessment.verificationCoverage}%` : "—"],
              ["Risk", assessment?.riskLevel ?? "Pending"],
            ].map(([label, value]) => <div className="stat-card" key={label}><div className="stat-card-label">{label}</div><div className="stat-card-value">{value}</div></div>)}
          </div>
          {bid.submittedAt && <p>Submitted {new Date(bid.submittedAt).toLocaleString("en-IN")}</p>}
          {assessment?.recommendationSummary && <p>{assessment.recommendationSummary}</p>}
          {!assessment && <div style={{ marginTop: 18 }}><button className="btn btn-primary" disabled={running} onClick={startVerification}>{running ? "Running verification…" : "Run verification"}</button></div>}
          {actionError && <p role="alert" style={{ color: "#b91c1c" }}>{actionError}</p>}
        </div>
      </section>

      <nav className="filter-bar" aria-label="Bid assessment sections">
        {tabs.map(([label, path]) => <Link key={path} className="btn btn-secondary btn-sm" href={`/bidders/${encodeURIComponent(bidId)}/${path}`}>{label}</Link>)}
      </nav>

      {assessment ? (
        <div className="dash-grid dash-grid-2">
          <section className="card"><div className="card-header"><span className="card-title">Key findings</span></div><div className="card-body">
            {assessment.findings.length ? assessment.findings.map(finding => <p key={finding.id}><strong>{finding.severity} · {finding.findingType}</strong>: {finding.message}</p>) : <p>No findings were returned.</p>}
          </div></section>
          <section className="card"><div className="card-header"><span className="card-title">Source checks</span></div><div className="card-body">
            {assessment.verificationResults.map(result => <p key={result.id}><strong>{result.source}</strong> ({result.mode}): {result.status} · {result.identifier}</p>)}
            {!assessment.verificationResults.length && <p>No source checks were returned.</p>}
          </div></section>
        </div>
      ) : <div className="card card-body">No assessment is stored for this bid yet. Run verification to populate rules, findings, evidence, and recommendation.</div>}
    </>
  );
}
