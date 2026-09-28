"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { recordDecision, useBidWorkspace, type OfficerDecision } from "@/lib/api";

type Action = "CONFIRM" | "REQUEST_CLARIFICATION" | "OVERRIDE";

export default function ReviewPage() {
  const { bidderId: bidId } = useParams<{ bidderId: string }>();
  const { bid, assessment, loading, error, reload } = useBidWorkspace(bidId);
  const [action, setAction] = useState<Action | "">("");
  const [reason, setReason] = useState("");
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);
  const [requestError, setRequestError] = useState<string | null>(null);
  const [decision, setDecision] = useState<OfficerDecision | null>(null);

  async function submit() {
    if (!action || ((action === "OVERRIDE" || action === "REQUEST_CLARIFICATION") && !reason.trim())) return;
    setSaving(true);
    setRequestError(null);
    try {
      const result = await recordDecision(bidId, { decision: action, reason: reason.trim() || undefined, notes: notes.trim() || undefined });
      setDecision(result);
      reload();
    } catch (problem) {
      setRequestError(problem instanceof Error ? problem.message : "Could not record decision.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <p>Loading bid for review…</p>;
  if (error || !bid) return <div className="card card-body" role="alert">{error ?? "Bid not found."}</div>;
  if (decision) return <section className="card card-body"><h1>Decision recorded</h1><p>{decision.decision} · {decision.bidStatus}</p><p>Officer {decision.officerId} · {new Date(decision.decidedAt).toLocaleString("en-IN")}</p>{decision.reason && <p>Reason: {decision.reason}</p>}<Link href={`/bidders/${encodeURIComponent(bidId)}`} className="btn btn-primary">Return to bid</Link></section>;

  return <>
    <Link href={`/bidders/${encodeURIComponent(bidId)}`} className="card-link">← {bid.bidderName}</Link>
    <h1>Officer decision</h1>
    <div className="demo-banner">Decisions are written to the backend audit trail. Override and clarification require a reason.</div>
    <div className="card card-body">
      <p><strong>{bid.bidderName}</strong> · {bid.bidId} · {bid.tenderId}</p>
      <p>Recommendation: {assessment?.recommendation ?? "No assessment yet"} · Risk: {assessment?.riskLevel ?? "Pending"}</p>
      <div className="filter-bar" role="group" aria-label="Officer decision">
        {([
          ["CONFIRM", "Confirm"], ["REQUEST_CLARIFICATION", "Request clarification"], ["OVERRIDE", "Override"],
        ] as const).map(([value, label]) => <button type="button" key={value} className={`filter-btn${action === value ? " active" : ""}`} onClick={() => setAction(value)}>{label}</button>)}
      </div>
      {(action === "REQUEST_CLARIFICATION" || action === "OVERRIDE") && <label className="form-group"><span className="form-label">Reason (required)</span><textarea className="form-input" rows={4} value={reason} onChange={event => setReason(event.target.value)} /></label>}
      {action && <label className="form-group"><span className="form-label">Notes (optional)</span><textarea className="form-input" rows={3} value={notes} onChange={event => setNotes(event.target.value)} /></label>}
      {requestError && <p role="alert" style={{ color: "#b91c1c" }}>{requestError}</p>}
      <button className="btn btn-primary" disabled={!action || saving || ((action === "OVERRIDE" || action === "REQUEST_CLARIFICATION") && !reason.trim())} onClick={submit}>{saving ? "Recording…" : "Record decision"}</button>
    </div>
  </>;
}
