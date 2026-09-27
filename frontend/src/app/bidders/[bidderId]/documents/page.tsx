import Link from "next/link";
import { DEMO_BIDDERS, DEMO_DOCUMENTS, DEMO_EXTRACTED_FIELDS } from "@/lib/mockData";
import { notFound } from "next/navigation";

export default function DocumentsPage({ params }: { params: { bidderId: string } }) {
  const bidder = DEMO_BIDDERS.find(b => b.id === params.bidderId);
  if (!bidder) return notFound();
  const docs = DEMO_DOCUMENTS[params.bidderId as keyof typeof DEMO_DOCUMENTS] ?? [];
  const firstDoc = docs[0];
  const fields = firstDoc ? DEMO_EXTRACTED_FIELDS[firstDoc.id as keyof typeof DEMO_EXTRACTED_FIELDS] ?? [] : [];

  const DOC_ICONS: Record<string, string> = {
    GST_CERTIFICATE: "🧾", PAN_CERTIFICATE: "🆔", UDYAM_CERTIFICATE: "🏭",
    CIN_DOCUMENT: "🏢", OEM_LETTER: "✅", MII_DECLARATION: "🇮🇳",
  };

  return (
    <>
      <div className="demo-banner">⚠️ Demo Mode · Bidder: {bidder.legalName} · {bidder.id}</div>
      <div style={{ marginBottom: 16 }}>
        <Link href={`/bidders/${bidder.id}`} style={{ fontSize: 12, color: "#1a56db" }}>← Back to Profile</Link>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "280px 1fr", gap: 16 }}>
        {/* Document list */}
        <div>
          <div className="card">
            <div className="card-header"><span className="card-title">📄 Documents ({docs.length})</span></div>
            <div>
              {docs.map(doc => (
                <div key={doc.id} style={{
                  padding: "12px 16px", borderBottom: "1px solid #f1f5f9", cursor: "pointer",
                  background: doc === firstDoc ? "#eff6ff" : "white",
                  borderLeft: doc === firstDoc ? "3px solid #1a56db" : "3px solid transparent",
                }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                    <span style={{ fontSize: 16 }}>{DOC_ICONS[doc.type] ?? "📄"}</span>
                    <span style={{ fontWeight: 600, fontSize: 13, color: "#0f172a" }}>{doc.name}</span>
                  </div>
                  <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                    <span className={`badge ${doc.status === "Extracted" ? "badge-green" : doc.status === "Expired" ? "badge-red" : "badge-yellow"}`}
                      style={{ fontSize: 9 }}>{doc.status}</span>
                    <span className="badge badge-blue" style={{ fontSize: 9 }}>Conf: {doc.confidence}%</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Document viewer & extraction */}
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          {/* Viewer placeholder */}
          <div className="card">
            <div className="card-header">
              <span className="card-title">📋 {firstDoc?.name ?? "Select a document"}</span>
              <div style={{ display: "flex", gap: 8 }}>
                {firstDoc && (
                  <>
                    <span className="badge badge-cyan">OCR Complete</span>
                    <span className="badge badge-gray" style={{ fontSize: 10, fontFamily: "monospace" }}>{firstDoc.hash}</span>
                  </>
                )}
              </div>
            </div>
            <div style={{ background: "#f8fafc", minHeight: 220, display: "flex", alignItems: "center", justifyContent: "center", borderBottom: "1px solid #e2e8f0" }}>
              <div style={{ textAlign: "center", color: "#94a3b8" }}>
                <div style={{ fontSize: 48 }}>📄</div>
                <div style={{ fontSize: 13, marginTop: 8 }}>{firstDoc?.name}</div>
                <div style={{ fontSize: 11, marginTop: 4 }}>Page 1 — AI-extracted fields highlighted below</div>
              </div>
            </div>
            <div style={{ padding: "10px 16px", background: "#fff7ed", display: "flex", gap: 10, fontSize: 11, color: "#92400e" }}>
              <span>🤖 AI Extraction</span>
              <span>·</span>
              <span>Model: PaddleOCR + Field Schema</span>
              <span>·</span>
              <span>Uploaded: {new Date().toLocaleDateString()}</span>
            </div>
          </div>

          {/* Extracted fields */}
          <div className="card">
            <div className="card-header"><span className="card-title">🔬 Extracted Fields</span></div>
            <div style={{ overflowX: "auto" }}>
              <table className="data-table">
                <thead>
                  <tr><th>Field</th><th>Extracted Value</th><th>Confidence</th><th>Page</th></tr>
                </thead>
                <tbody>
                  {fields.map(f => (
                    <tr key={f.field}>
                      <td style={{ fontWeight: 600 }}>{f.field}</td>
                      <td><code style={{ background: "#f1f5f9", padding: "2px 6px", borderRadius: 4, fontSize: 12 }}>{f.value}</code></td>
                      <td>
                        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                          <div className="progress-bar" style={{ width: 50 }}>
                            <div className={`progress-bar-fill ${f.confidence >= 95 ? "progress-green" : f.confidence >= 80 ? "progress-yellow" : "progress-red"}`}
                              style={{ width: `${f.confidence}%` }} />
                          </div>
                          <span style={{ fontSize: 12, fontWeight: 700 }}>{f.confidence}%</span>
                        </div>
                      </td>
                      <td>Page {f.page}</td>
                    </tr>
                  ))}
                  {fields.length === 0 && (
                    <tr><td colSpan={4} style={{ textAlign: "center", color: "#94a3b8", padding: 24 }}>Select a document to see extracted fields.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* All docs summary */}
          <div className="card">
            <div className="card-header"><span className="card-title">📋 All Documents Summary</span></div>
            <div style={{ overflowX: "auto" }}>
              <table className="data-table">
                <thead>
                  <tr><th>Document</th><th>Type</th><th>Status</th><th>Confidence</th><th>Hash</th></tr>
                </thead>
                <tbody>
                  {docs.map(d => (
                    <tr key={d.id}>
                      <td style={{ fontWeight: 600 }}>{d.name}</td>
                      <td><span className="badge badge-gray" style={{ fontSize: 10 }}>{d.type}</span></td>
                      <td>
                        <span className={`badge ${d.status === "Extracted" ? "badge-green" : d.status === "Expired" ? "badge-red" : d.status === "Conflict Detected" ? "badge-yellow" : "badge-gray"}`}>
                          {d.status}
                        </span>
                      </td>
                      <td>{d.confidence}%</td>
                      <td style={{ fontFamily: "monospace", fontSize: 10, color: "#64748b" }}>{d.hash}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
