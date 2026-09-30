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
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  async function startVerification() {
    setRunning(true);
    setActionError(null);
    setActionSuccess(null);
    try {
      await runVerification(bidId);
      reload();
      setActionSuccess("Verification completed successfully.");
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
          <div style={{ marginTop: 18 }}>
            <button className="btn btn-primary" disabled={running} onClick={startVerification}>
              {running ? "Running verification…" : (assessment ? "Re-run Verification" : "Run verification")}
            </button>
          </div>
          {actionError && <p role="alert" style={{ color: "#b91c1c", marginTop: 8 }}>{actionError}</p>}
          {actionSuccess && <p role="alert" style={{ color: "#15803d", marginTop: 8 }}>{actionSuccess}</p>}
        </div>
      </section>

      <nav className="filter-bar" aria-label="Bid assessment sections">
        {tabs.map(([label, path]) => <Link key={path} className="btn btn-secondary btn-sm" href={`/bidders/${encodeURIComponent(bidId)}/${path}`}>{label}</Link>)}
      </nav>

      {assessment ? (() => {
        // Calculate Rule Summary
        const ruleCounts = assessment.ruleResults.reduce((acc, r) => {
          acc[r.status] = (acc[r.status] || 0) + 1;
          return acc;
        }, {} as Record<string, number>);
        const totalRules = assessment.ruleResults.length;

        // Calculate Verification Summary
        const verificationCounts = assessment.verificationResults.reduce((acc, v) => {
          acc[v.status] = (acc[v.status] || 0) + 1;
          return acc;
        }, {} as Record<string, number>);
        const totalSources = assessment.verificationResults.length;

        return (
          <div style={{ display: "flex", flexDirection: "column", gap: 16, marginTop: 16 }}>
            <div className="dash-grid dash-grid-3">
              {/* Rule Evaluation Summary */}
              <section className="card">
                <div className="card-header"><span className="card-title">Rule Evaluation</span></div>
                <div className="card-body">
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
                    <div className="donut-wrap" style={{ width: 80, height: 80 }}>
                      <svg viewBox="0 0 36 36" className="donut-svg">
                        <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#e2e8f0" strokeWidth="4"/>
                        <path strokeDasharray={`${((ruleCounts['PASS'] || 0) / (totalRules || 1)) * 100}, 100`} d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#10b981" strokeWidth="4"/>
                      </svg>
                      <div className="donut-label" style={{ marginTop: 2 }}>
                        <div className="donut-val" style={{ fontSize: 16 }}>{ruleCounts['PASS'] || 0}</div>
                        <div className="donut-sub">Passed</div>
                      </div>
                    </div>
                    <div style={{ flex: 1, paddingLeft: 16, fontSize: 13, display: 'flex', flexDirection: 'column', gap: 6, justifyContent: 'center' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: '#059669', fontWeight: 600 }}>Passed</span> <span>{ruleCounts['PASS'] || 0}</span></div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: '#dc2626', fontWeight: 600 }}>Failed</span> <span>{ruleCounts['FAIL'] || 0}</span></div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: '#d97706', fontWeight: 600 }}>Clarify</span> <span>{ruleCounts['NEEDS_CLARIFICATION'] || 0}</span></div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: '#64748b', fontWeight: 600 }}>Other</span> <span>{(ruleCounts['NOT_APPLICABLE'] || 0) + (ruleCounts['SOURCE_UNAVAILABLE'] || 0)}</span></div>
                    </div>
                  </div>
                </div>
              </section>

              {/* Verification Coverage */}
              <section className="card">
                <div className="card-header"><span className="card-title">Verification Coverage</span></div>
                <div className="card-body">
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
                    <div className="donut-wrap" style={{ width: 80, height: 80 }}>
                      <svg viewBox="0 0 36 36" className="donut-svg">
                        <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#e2e8f0" strokeWidth="4"/>
                        <path strokeDasharray={`${((verificationCounts['VERIFIED'] || 0) / (totalSources || 1)) * 100}, 100`} d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="#3b82f6" strokeWidth="4"/>
                      </svg>
                      <div className="donut-label" style={{ marginTop: 2 }}>
                        <div className="donut-val" style={{ fontSize: 16 }}>{verificationCounts['VERIFIED'] || 0}</div>
                        <div className="donut-sub">Verified</div>
                      </div>
                    </div>
                    <div style={{ flex: 1, paddingLeft: 16, fontSize: 13, display: 'flex', flexDirection: 'column', gap: 6, justifyContent: 'center' }}>
                      {Object.entries(verificationCounts).map(([status, count]) => (
                        <div key={status} style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <span style={{ fontWeight: 600, color: status === 'VERIFIED' ? '#2563eb' : (status === 'MISMATCH' || status === 'NOT_FOUND' ? '#dc2626' : '#64748b') }}>
                            {status}
                          </span> 
                          <span>{count as number}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </section>

              {/* Category Compliance Overview */}
              <section className="card">
                <div className="card-header"><span className="card-title">Category Breakdown</span></div>
                <div className="card-body" style={{ maxHeight: 120, overflowY: 'auto' }}>
                  {assessment.scoreBreakdown && assessment.scoreBreakdown.length > 0 ? assessment.scoreBreakdown.map(cat => (
                    <div key={cat.category || (cat as any).rule || Math.random()} style={{ marginBottom: 12 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, marginBottom: 4 }}>
                        <strong>{String(cat.category || (cat as any).rule || 'UNKNOWN').replace(/_/g, ' ').toUpperCase()}</strong>
                        <span>{cat.rulesPassed} / {cat.rulesTotal} Rules</span>
                      </div>
                      <div className="progress-bar">
                        <div 
                          className={`progress-bar-fill ${cat.fulfilled === 1 ? 'progress-green' : cat.fulfilled > 0 ? 'progress-yellow' : 'progress-red'}`} 
                          style={{ width: `${Math.max(0, Math.min(100, cat.fulfilled * 100))}%` }}
                        ></div>
                      </div>
                    </div>
                  )) : <p style={{ fontSize: 13 }}>No category breakdown available.</p>}
                </div>
              </section>
            </div>

            <div className="dash-grid dash-grid-2">
              <section className="card">
                <div className="card-header"><span className="card-title">Key findings</span></div>
                <div className="card-body">
                  {assessment.findings.length ? assessment.findings.map(finding => (
                    <div key={finding.id} className={`conflict-card ${finding.severity.toLowerCase()}`}>
                      <div className="conflict-header">
                        <span className="conflict-title">{finding.findingType.replace(/_/g, ' ')}</span>
                        <span className={`badge ${finding.severity === 'CRITICAL' || finding.severity === 'BLOCKER' ? 'badge-red' : finding.severity === 'HIGH' ? 'badge-orange' : finding.severity === 'MEDIUM' ? 'badge-yellow' : 'badge-gray'}`}>
                          {finding.severity}
                        </span>
                      </div>
                      <p style={{ fontSize: 13, marginTop: 8, marginBottom: 8 }}>{finding.message}</p>
                      {finding.evidenceReference && (
                        <div style={{ fontSize: 11, color: '#64748b' }}>Evidence Ref: {finding.evidenceReference}</div>
                      )}
                    </div>
                  )) : <p>No findings were returned.</p>}
                </div>
              </section>

              <section className="card">
                <div className="card-header"><span className="card-title">Source checks</span></div>
                <div className="card-body">
                  {assessment.verificationResults.map(result => (
                    <div key={result.id} className="quick-action" style={{ cursor: 'default' }}>
                      <div className="qa-left">
                        <div className="qa-text">
                          <div className="qa-label">{result.source} <span className="connector-mode">{result.mode}</span></div>
                          <div style={{ fontSize: 11, color: '#64748b', marginTop: 2 }}>{result.identifier}</div>
                        </div>
                      </div>
                      <span className={`badge ${result.status === 'VERIFIED' ? 'badge-green' : result.status === 'MISMATCH' || result.status === 'NOT_FOUND' ? 'badge-red' : 'badge-gray'}`}>
                        {result.status}
                      </span>
                    </div>
                  ))}
                  {!assessment.verificationResults.length && <p>No source checks were returned.</p>}
                </div>
              </section>
            </div>
          </div>
        );
      })() : <div className="card card-body">No assessment is stored for this bid yet. Run verification to populate rules, findings, evidence, and recommendation.</div>}
    </>
  );
}
