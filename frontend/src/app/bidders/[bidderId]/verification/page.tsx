import Link from "next/link";
import { DEMO_BIDDERS, DEMO_GST_VERIFICATION, DEMO_PAN_VERIFICATION, DEMO_UDYAM_VERIFICATION, DEMO_OEM_VERIFICATION, DEMO_BLACKLIST_VERIFICATION, CONNECTORS } from "@/lib/mockData";
import { notFound } from "next/navigation";

export default function VerificationPage({ params }: { params: { bidderId: string } }) {
  const bidder = DEMO_BIDDERS.find(b => b.id === params.bidderId);
  if (!bidder) return notFound();

  const gst = DEMO_GST_VERIFICATION[params.bidderId as keyof typeof DEMO_GST_VERIFICATION];
  const pan = DEMO_PAN_VERIFICATION[params.bidderId as keyof typeof DEMO_PAN_VERIFICATION];
  const udyam = DEMO_UDYAM_VERIFICATION[params.bidderId as keyof typeof DEMO_UDYAM_VERIFICATION];
  const oem = DEMO_OEM_VERIFICATION[params.bidderId as keyof typeof DEMO_OEM_VERIFICATION];
  const bl = DEMO_BLACKLIST_VERIFICATION[params.bidderId as keyof typeof DEMO_BLACKLIST_VERIFICATION];

  function StatusTag({ match, status }: { match: boolean; status: string }) {
    if (status === "NOT_FOUND" || status === "UNAVAILABLE") return <span className="badge badge-red">⚠️ NOT FOUND</span>;
    if (match === false) return <span className="badge badge-yellow">⚠️ CONFLICT</span>;
    return <span className="badge badge-green">✓ VERIFIED</span>;
  }

  function ConnCard({ title, icon, data, fields, match, status }: {
    title: string; icon: string;
    data: Record<string, string | boolean>;
    fields: [string, string][];
    match: boolean; status: string;
  }) {
    return (
      <div className="connector-card" style={{ borderLeft: match ? "3px solid #10b981" : "3px solid #ef4444" }}>
        <div className="connector-header">
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontSize: 20 }}>{icon}</span>
            <span className="connector-name">{title}</span>
          </div>
          <span className="connector-mode">DEMO</span>
        </div>
        <StatusTag match={match} status={status} />
        <div className="connector-fields">
          {fields.map(([k, v]) => (
            <div key={k} className="connector-field">
              <span className="connector-field-key">{k}</span>
              <span className="connector-field-val" style={{ color: k.toLowerCase().includes("status") ? (v === "ACTIVE" || v === "VALID" || v === "CURRENT" || v === "CLEAR" ? "#059669" : "#dc2626") : "#0f172a" }}>
                {v}
              </span>
            </div>
          ))}
        </div>
        {!match && (
          <div style={{ marginTop: 8, background: "#fef2f2", padding: "6px 8px", borderRadius: 6, fontSize: 11, color: "#991b1b" }}>
            ⚠️ {(data as any).conflict}
          </div>
        )}
      </div>
    );
  }

  return (
    <>
      <div className="demo-banner">
        ⚠️ Demo Mode — All connectors operating in DEMO mode. Results are from controlled prototype dataset, NOT live government sources.
      </div>
      <div style={{ marginBottom: 16 }}>
        <Link href={`/bidders/${bidder.id}`} style={{ fontSize: 12, color: "#1a56db" }}>← Back to Profile</Link>
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <div>
          <h2 style={{ fontSize: 18, fontWeight: 800, color: "#0f172a", margin: 0 }}>{bidder.legalName}</h2>
          <p style={{ fontSize: 12, color: "#64748b", margin: "2px 0 0" }}>Verification Center — {bidder.id}</p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <span className="badge badge-yellow">🔒 MODE: DEMO</span>
          <span className="badge badge-blue">Connectors: 5 active</span>
        </div>
      </div>

      {/* Summary bar */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 12, marginBottom: 20 }}>
        {[
          { label: "Verified", value: bidder.conflicts === 0 ? "5 / 5" : "3 / 5", color: bidder.conflicts === 0 ? "#059669" : "#d97706", bg: bidder.conflicts === 0 ? "#f0fdf4" : "#fffbeb" },
          { label: "Conflicts", value: String(bidder.conflicts), color: "#dc2626", bg: "#fef2f2" },
          { label: "Missing", value: String(bidder.missingDocs), color: "#92400e", bg: "#fff7ed" },
          { label: "Verification %", value: `${bidder.verificationScore}%`, color: "#1e40af", bg: "#eff6ff" },
        ].map(c => (
          <div key={c.label} style={{ background: c.bg, border: `1px solid ${c.color}22`, borderRadius: 10, padding: "12px 16px" }}>
            <div style={{ fontSize: 11, color: c.color, fontWeight: 700 }}>{c.label}</div>
            <div style={{ fontSize: 24, fontWeight: 900, color: c.color }}>{c.value}</div>
          </div>
        ))}
      </div>

      <div className="connector-grid">
        <ConnCard title="GST / GSTIN" icon="🧾" data={gst as any} match={gst.match} status={gst.verificationStatus} fields={[
          ["GSTIN", gst.gstin], ["Legal Name", gst.legalName], ["Status", gst.status],
          ["Returns", gst.returnFilingStatus], ["Last Period", gst.lastReturnPeriod],
        ]} />
        <ConnCard title="PAN / Income Tax" icon="🆔" data={pan as any} match={pan.match} status={pan.verificationStatus} fields={[
          ["PAN", pan.pan], ["Name", pan.name], ["Status", pan.status],
        ]} />
        <ConnCard title="Udyam / MSME" icon="🏭" data={udyam as any} match={udyam.match} status={udyam.verificationStatus} fields={[
          ["Udyam No.", udyam.udyamNumber ?? "Not found"], ["Legal Name", udyam.legalName ?? "N/A"], ["Status", udyam.status],
        ]} />
        <ConnCard title="OEM Authorisation" icon="✅" data={oem as any} match={oem.match} status={oem.verificationStatus} fields={[
          ["Auth No.", oem.authNumber], ["Manufacturer", oem.manufacturer], ["Valid To", oem.validTo], ["Status", oem.status],
        ]} />
        <ConnCard title="Blacklist / Debarment" icon="🚫" data={bl} match={bl.status === "CLEAR"} status={bl.verificationStatus} fields={[
          ["Registry Status", bl.status], ["Source", bl.source],
        ]} />
        {CONNECTORS.slice(5).map(c => (
          <div key={c.id} className="connector-card" style={{ opacity: 0.6, borderLeft: "3px solid #e2e8f0" }}>
            <div className="connector-header">
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ fontSize: 20 }}>{c.icon}</span>
                <span className="connector-name">{c.name}</span>
              </div>
              <span className="connector-mode">DEMO</span>
            </div>
            <span className="badge badge-gray" style={{ fontSize: 10 }}>NOT APPLICABLE</span>
            <div style={{ fontSize: 11, color: "#94a3b8", marginTop: 8 }}>{c.desc}</div>
          </div>
        ))}
      </div>
    </>
  );
}
