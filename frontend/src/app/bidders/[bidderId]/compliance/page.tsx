"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useBidWorkspace } from "@/lib/api";

function resultClass(status: string) {
  if (status === "PASS") return "badge-green";
  if (status === "FAIL") return "badge-red";
  if (status === "NEEDS_CLARIFICATION") return "badge-yellow";
  return "badge-gray";
}

export default function CompliancePage() {
  const { bidderId: bidId } = useParams<{ bidderId: string }>();
  const { bid, assessment, loading, error } = useBidWorkspace(bidId);
  if (loading) return <p>Loading rule evaluation…</p>;
  if (error || !bid) return <div className="card card-body" role="alert">{error ?? "Bid not found."}</div>;
  const rules = assessment?.ruleResults ?? [];

  return <>
    <Link href={`/bidders/${encodeURIComponent(bidId)}`} className="card-link">← {bid.bidderName}</Link>
    <h1>Rule evaluation</h1>
    {!assessment ? <div className="card card-body">No rules have been evaluated yet.</div> : <>
      <div className="stat-cards">{[
        ["Total", rules.length], ["Passed", rules.filter(rule => rule.status === "PASS").length],
        ["Failed", rules.filter(rule => rule.status === "FAIL").length],
        ["Mandatory failure", assessment.hasMandatoryFailure ? "Yes" : "No"],
      ].map(([label, value]) => <div className="stat-card" key={label}><div className="stat-card-label">{label}</div><div className="stat-card-value">{value}</div></div>)}</div>
      <div className="card mt-4"><div style={{ overflowX: "auto" }}><table className="data-table">
        <thead><tr><th>Rule</th><th>Mandatory</th><th>Status</th><th>Tender clause</th><th>Details</th></tr></thead>
        <tbody>{rules.map(rule => <tr key={rule.id}><td><strong>{rule.ruleName}</strong><br /><small>{rule.ruleId}</small></td><td>{rule.isMandatory ? "Yes" : "No"}</td><td><span className={`badge ${resultClass(rule.status)}`}>{rule.status}</span></td><td>{rule.clause ?? "—"}</td><td>{rule.details ?? "—"}</td></tr>)}
          {!rules.length && <tr><td colSpan={5}>The assessment contains no rule results.</td></tr>}</tbody>
      </table></div></div>
    </>}
  </>;
}
