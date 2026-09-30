"use client";

import { useEffect, useState } from "react";
import { apiRequest, useApiData, type AuditEvent, type Bid, type Tender } from "@/lib/api";
import React from "react";

function formatValue(key: string, value: any): React.ReactNode {
  if (value === null || value === undefined) return <span style={{ color: '#94a3b8', fontStyle: 'italic' }}>Not available</span>;
  if (typeof value === 'boolean') return value ? "Yes" : "No";
  if (typeof value === 'string') {
    if (value.match(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/)) {
      return new Date(value).toLocaleString("en-IN");
    }
    return value;
  }
  if (Array.isArray(value)) {
    return value.length > 0 ? (
      <ul style={{ margin: 0, paddingLeft: 16 }}>
        {value.map((v, i) => <li key={i}>{formatValue('', v)}</li>)}
      </ul>
    ) : "None";
  }
  if (typeof value === 'object') {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 4, marginTop: 4 }}>
        {Object.entries(value).map(([k, v]) => (
          <div key={k} style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: 8 }}>
            <div style={{ fontWeight: 600, color: '#64748b', fontSize: 11, textTransform: 'capitalize' }}>{k.replace(/_/g, ' ')}:</div>
            <div style={{ fontSize: 12 }}>{formatValue(k, v)}</div>
          </div>
        ))}
      </div>
    );
  }
  return String(value);
}

function AuditRow({ event }: { event: AuditEvent }) {
  const [expanded, setExpanded] = useState(false);
  
  let summary = "";
  if (typeof event.details === 'object' && event.details !== null) {
    const keys = Object.keys(event.details);
    if (keys.length === 0) summary = "Empty record";
    else if (keys.includes("message")) summary = String((event.details as any).message).slice(0, 50);
    else if (keys.includes("status")) summary = `Status: ${(event.details as any).status}`;
    else summary = `${keys.length} fields recorded`;
  } else {
    summary = String(event.details).slice(0, 50) + (String(event.details).length > 50 ? "..." : "");
  }

  return (
    <>
      <tr style={{ borderBottom: expanded ? "none" : "1px solid #f1f5f9" }}>
        <td style={{ whiteSpace: "nowrap" }}>{new Date(event.timestamp).toLocaleString("en-IN", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit", second: "2-digit" })}</td>
        <td style={{ fontWeight: 500 }}>{event.bidId}</td>
        <td>
          <span className={`badge ${event.eventType.includes('DECISION') ? 'badge-blue' : event.eventType.includes('ASSESSMENT') || event.eventType.includes('VERIFICATION') ? 'badge-green' : 'badge-gray'}`}>
            {event.eventType.replace(/_/g, ' ')}
          </span>
        </td>
        <td>{event.actor}</td>
        <td>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 16 }}>
            <span style={{ fontSize: 12, color: "#64748b", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", maxWidth: 200 }}>
              {summary}
            </span>
            <button 
              className="btn btn-secondary btn-sm" 
              onClick={() => setExpanded(!expanded)}
              style={{ whiteSpace: "nowrap" }}
            >
              {expanded ? "Hide Details" : "View Details"}
            </button>
          </div>
        </td>
      </tr>
      {expanded && (
        <tr style={{ background: "#f8fafc" }}>
          <td colSpan={5} style={{ padding: "16px 24px", borderTop: "none", borderBottom: "1px solid #e2e8f0" }}>
            <div style={{ background: "white", border: "1px solid #e2e8f0", borderRadius: 8, padding: 16 }}>
              {typeof event.details === 'object' && event.details !== null ? (
                <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                  {Object.entries(event.details).map(([k, v]) => (
                    <div key={k} style={{ display: "flex", gap: 16, borderBottom: "1px solid #f1f5f9", paddingBottom: 8, flexWrap: "wrap" }}>
                      <div style={{ width: 160, fontWeight: 700, color: "#0f172a", fontSize: 12, textTransform: "capitalize", flexShrink: 0 }}>
                        {k.replace(/_/g, ' ')}
                      </div>
                      <div style={{ fontSize: 13, color: "#374151", flex: 1, minWidth: 200, wordBreak: "break-word" }}>
                        {formatValue(k, v)}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ fontSize: 13, wordBreak: "break-word" }}>{formatValue('', event.details)}</div>
              )}
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

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

  if (tenders.loading) return <p style={{ padding: 20, color: "#64748b" }}>Loading tender list…</p>;
  if (tenders.error) return <div className="card card-body" role="alert" style={{ color: "#ef4444" }}>{tenders.error}</div>;

  return (
    <>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: 24, flexWrap: "wrap", gap: 16 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, color: '#0f172a', margin: 0 }}>Audit Trail</h1>
          <p style={{ color: '#64748b', fontSize: 13, marginTop: 4 }}>System and officer events recorded across the verification pipeline.</p>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          <label style={{ fontSize: 11, fontWeight: 700, color: '#64748b', textTransform: 'uppercase' }}>Select Tender Context</label>
          <select className="form-select" aria-label="Select tender" value={tenderId} onChange={event => setSelectedTenderId(event.target.value)} style={{ minWidth: 320 }}>
            {(tenders.data ?? []).map(tender => <option key={tender.tenderId} value={tender.tenderId}>{tender.referenceNumber} · {tender.title}</option>)}
          </select>
        </div>
      </div>

      <div className="stat-cards" style={{ gridTemplateColumns: 'repeat(4, 1fr)', marginBottom: 24 }}>
        <div className="stat-card">
          <div className="stat-card-label">Total Events</div>
          <div className="stat-card-value">{eventsLoading ? "…" : events.length}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Bids Tracked</div>
          <div className="stat-card-value">{bids.data?.length ?? 0}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">Officer Decisions</div>
          <div className="stat-card-value" style={{ color: '#3b82f6' }}>{eventsLoading ? "…" : events.filter(event => event.eventType === "OFFICER_DECISION_RECORDED").length}</div>
        </div>
        <div className="stat-card">
          <div className="stat-card-label">System Assessments</div>
          <div className="stat-card-value" style={{ color: '#10b981' }}>{eventsLoading ? "…" : events.filter(event => event.eventType.toLowerCase().includes("verification") || event.eventType.toLowerCase().includes("assessment")).length}</div>
        </div>
      </div>

      {(bids.error || eventsError) && <div className="card card-body" role="alert" style={{ color: "#ef4444", marginBottom: 16 }}>{bids.error ?? eventsError}</div>}
      {eventsLoading && <div style={{ padding: 20, color: "#64748b" }}>Loading audit events…</div>}
      
      {!eventsLoading && !eventsError && (
        <div className="card mt-4">
          <div style={{ overflowX: "auto" }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Bid ID</th>
                  <th>Event Type</th>
                  <th>Actor</th>
                  <th>Details</th>
                </tr>
              </thead>
              <tbody>
                {events.map(event => <AuditRow key={event.id} event={event} />)}
                {!events.length && (
                  <tr><td colSpan={5} style={{ textAlign: "center", padding: 24, color: "#64748b" }}>No audit events are recorded for this tender.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  );
}
