"use client";

import { useEffect, useState } from "react";
import { apiRequest, useApiData, type AuditEvent, type Bid, type Tender } from "@/lib/api";

export default function AuditPage() {
  const tenders = useApiData<Tender[]>("/api/tenders");
  const [selectedTenderId, setSelectedTenderId] = useState<string | null>(null);
  const tenderId = selectedTenderId ?? tenders.data?.[0]?.tenderId ?? "";
  const bids = useApiData<Bid[]>(tenderId ? `/api/tenders/${encodeURIComponent(tenderId)}/bids` : null);
  const [eventResult, setEventResult] = useState<{ key: string; events: AuditEvent[]; error: string | null } | null>(null);
  const eventKey = (bids.data ?? []).map(bid => bid.bidId).join("|");

  useEffect(() => {
    if (!bids.data) return;
    let active = true;
    Promise.all(bids.data.map(bid => apiRequest<AuditEvent[]>(`/api/bids/${encodeURIComponent(bid.bidId)}/audit-events`)))
      .then(results => { if (active) setEventResult({ key: eventKey, events: results.flat().sort((a, b) => b.timestamp.localeCompare(a.timestamp)), error: null }); })
      .catch(error => { if (active) setEventResult({ key: eventKey, events: [], error: error instanceof Error ? error.message : "Could not load audit events." }); });
    return () => { active = false; };
  }, [bids.data, eventKey]);

  const currentEvents = eventResult?.key === eventKey ? eventResult : null;
  const events = currentEvents?.events ?? [];
  const eventsError = currentEvents?.error ?? null;
  const eventsLoading = Boolean(bids.data) && !currentEvents;

  if (tenders.loading) return <p>Loading tender list…</p>;
  if (tenders.error) return <div className="card card-body" role="alert">{tenders.error}</div>;

  return <>
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 16, marginBottom: 18 }}>
      <div><h1>Audit trail</h1><p>Events recorded by the backend for bids in the selected tender.</p></div>
      <select className="form-select" aria-label="Select tender" value={tenderId} onChange={event => setSelectedTenderId(event.target.value)}>
        {(tenders.data ?? []).map(tender => <option key={tender.tenderId} value={tender.tenderId}>{tender.referenceNumber}</option>)}
      </select>
    </div>
    <div className="stat-cards">{[
      ["Events", events.length], ["Bids", bids.data?.length ?? 0], ["Officer decisions", events.filter(event => event.eventType === "OFFICER_DECISION_RECORDED").length], ["Assessment events", events.filter(event => event.eventType.toLowerCase().includes("verification") || event.eventType.toLowerCase().includes("assessment")).length],
    ].map(([label, value]) => <div className="stat-card" key={label}><div className="stat-card-label">{label}</div><div className="stat-card-value">{eventsLoading ? "…" : value}</div></div>)}</div>
    {(bids.error || eventsError) && <div className="card card-body" role="alert">{bids.error ?? eventsError}</div>}
    {eventsLoading && <p>Loading audit events…</p>}
    {!eventsLoading && !eventsError && <div className="card mt-4"><div style={{ overflowX: "auto" }}><table className="data-table">
      <thead><tr><th>Timestamp</th><th>Bid</th><th>Event</th><th>Actor</th><th>Details</th></tr></thead>
      <tbody>{events.map(event => <tr key={event.id}><td>{new Date(event.timestamp).toLocaleString("en-IN")}</td><td>{event.bidId}</td><td>{event.eventType}</td><td>{event.actor}</td><td><pre style={{ whiteSpace: "pre-wrap", margin: 0 }}>{JSON.stringify(event.details)}</pre></td></tr>)}
        {!events.length && <tr><td colSpan={5}>No audit events are recorded for this tender.</td></tr>}</tbody>
    </table></div></div>}
  </>;
}
