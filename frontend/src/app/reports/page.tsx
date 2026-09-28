"use client";

import { useEffect, useState } from "react";
import { apiRequest, useApiData, type Assessment, type Bid, type Tender } from "@/lib/api";

function downloadFile(filename: string, content: string, type: string) {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

function csvValue(value: unknown) {
  return `"${String(value ?? "").replaceAll('"', '""')}"`;
}

async function optionalAssessment(bidId: string) {
  try {
    return await apiRequest<Assessment>(`/api/bids/${encodeURIComponent(bidId)}/assessment`);
  } catch (error) {
    if (error instanceof Error && error.message.includes("No verification assessment")) return null;
    throw error;
  }
}

export default function ReportsPage() {
  const tenders = useApiData<Tender[]>("/api/tenders");
  const [selectedTenderId, setSelectedTenderId] = useState<string | null>(null);
  const tenderId = selectedTenderId ?? tenders.data?.[0]?.tenderId ?? "";
  const bids = useApiData<Bid[]>(tenderId ? `/api/tenders/${encodeURIComponent(tenderId)}/bids` : null);
  const [assessmentResult, setAssessmentResult] = useState<{ key: string; assessments: Record<string, Assessment | null>; error: string | null } | null>(null);
  const assessmentKey = (bids.data ?? []).map(bid => bid.bidId).join("|");
  const tender = tenders.data?.find(item => item.tenderId === tenderId);

  useEffect(() => {
    if (!bids.data) return;
    let active = true;
    Promise.all(bids.data.map(async bid => [bid.bidId, await optionalAssessment(bid.bidId)] as const))
      .then(results => { if (active) setAssessmentResult({ key: assessmentKey, assessments: Object.fromEntries(results), error: null }); })
      .catch(problem => { if (active) setAssessmentResult({ key: assessmentKey, assessments: {}, error: problem instanceof Error ? problem.message : "Could not load assessments." }); });
    return () => { active = false; };
  }, [bids.data, assessmentKey]);

  const currentAssessments = assessmentResult?.key === assessmentKey ? assessmentResult : null;
  const assessments = currentAssessments?.assessments ?? {};
  const loadingAssessments = Boolean(bids.data) && !currentAssessments;
  const error = currentAssessments?.error ?? null;
  const assessedCount = Object.values(assessments).filter(Boolean).length;
  const csvRows = (bids.data ?? []).map(bid => {
    const assessment = assessments[bid.bidId];
    return [bid.bidId, bid.bidderName, bid.status, bid.bidAmount, bid.currency, assessment?.complianceScore ?? "", assessment?.verificationCoverage ?? "", assessment?.riskLevel ?? "", assessment?.recommendation ?? ""];
  });

  if (tenders.loading) return <p>Loading reports…</p>;
  if (tenders.error) return <div className="card card-body" role="alert">{tenders.error}</div>;

  return <>
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 16, marginBottom: 18 }}>
      <div><h1>Evaluation reports</h1><p>Export backend bid summaries and available assessments.</p></div>
      <select className="form-select" aria-label="Select tender" value={tenderId} onChange={event => setSelectedTenderId(event.target.value)}>
        {(tenders.data ?? []).map(item => <option key={item.tenderId} value={item.tenderId}>{item.referenceNumber}</option>)}
      </select>
    </div>
    <div className="stat-cards">{[
      ["Tender", tender?.referenceNumber ?? "—"], ["Bids", bids.data?.length ?? 0], ["Assessed", loadingAssessments ? "…" : assessedCount],
    ].map(([label, value]) => <div className="stat-card" key={label}><div className="stat-card-label">{label}</div><div className="stat-card-value">{value}</div></div>)}</div>
    {(bids.error || error) && <div className="card card-body mt-4" role="alert">{bids.error ?? error}</div>}
    <div className="card card-body mt-4">
      <strong>Export current tender data</strong><p>CSV contains bid summaries and assessment scores. JSON contains the full returned assessment payloads.</p>
      <div style={{ display: "flex", gap: 8 }}>
        <button className="btn btn-primary" disabled={!bids.data?.length || loadingAssessments} onClick={() => downloadFile(`${tenderId}-evaluation.csv`, [["Bid ID", "Bidder", "Status", "Amount", "Currency", "Compliance", "Verification coverage", "Risk", "Recommendation"], ...csvRows].map(row => row.map(csvValue).join(",")).join("\n"), "text/csv")}>Export CSV</button>
        <button className="btn btn-secondary" disabled={!bids.data?.length || loadingAssessments} onClick={() => downloadFile(`${tenderId}-assessments.json`, JSON.stringify({ tender, bids: bids.data, assessments }, null, 2), "application/json")}>Export JSON</button>
      </div>
    </div>
    <div className="card mt-4"><div style={{ overflowX: "auto" }}><table className="data-table">
      <thead><tr><th>Bidder</th><th>Bid ID</th><th>Compliance</th><th>Risk</th><th>Recommendation</th><th>Status</th></tr></thead>
      <tbody>{(bids.data ?? []).map(bid => { const assessment = assessments[bid.bidId]; return <tr key={bid.bidId}><td>{bid.bidderName}</td><td>{bid.bidId}</td><td>{assessment ? `${assessment.complianceScore}%` : "Not assessed"}</td><td>{assessment?.riskLevel ?? "—"}</td><td>{assessment?.recommendation ?? "—"}</td><td>{bid.status}</td></tr>; })}
        {!bids.data?.length && <tr><td colSpan={6}>No bids are available for this tender.</td></tr>}</tbody>
    </table></div></div>
  </>;
}
