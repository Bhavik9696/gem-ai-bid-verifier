"use client";
import { useState } from "react";

type Step = "tender" | "bidders" | "documents" | "processing" | "done";
const STEPS: Step[] = ["tender", "bidders", "documents", "processing", "done"];
const STEP_LABELS: Record<Step, string> = {
  tender: "Tender", bidders: "Bidders", documents: "Documents", processing: "Processing", done: "Ready",
};

export default function ImportPage() {
  const [step, setStep] = useState<Step>("tender");
  const [isProcessing, setIsProcessing] = useState(false);
  const [done, setDone] = useState(false);

  function advance() {
    const i = STEPS.indexOf(step);
    if (i === STEPS.length - 2) {
      setIsProcessing(true);
      setTimeout(() => { setIsProcessing(false); setDone(true); setStep("done"); }, 2000);
    } else if (i < STEPS.length - 1) {
      setStep(STEPS[i + 1]);
    }
  }

  const stepIdx = STEPS.indexOf(step);

  return (
    <>
      <div className="page-header">
        <h1>Import Tender & Bids</h1>
        <p>Import tender and bidder data from GeM into ComplianceOS for evaluation.</p>
      </div>

      {/* Step indicator */}
      <div style={{ display: "flex", alignItems: "center", marginBottom: 28, gap: 0 }}>
        {STEPS.map((s, i) => (
          <div key={s} style={{ display: "flex", alignItems: "center", flex: i < STEPS.length - 1 ? 1 : "unset" }}>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 4 }}>
              <div style={{
                width: 32, height: 32, borderRadius: "50%",
                background: i < stepIdx ? "#10b981" : i === stepIdx ? "#1a56db" : "#e2e8f0",
                color: i <= stepIdx ? "white" : "#94a3b8",
                display: "flex", alignItems: "center", justifyContent: "center",
                fontWeight: 700, fontSize: 13, transition: "background 0.3s",
              }}>
                {i < stepIdx ? "✓" : i + 1}
              </div>
              <span style={{ fontSize: 10, color: i === stepIdx ? "#1a56db" : "#64748b", fontWeight: i === stepIdx ? 700 : 400, whiteSpace: "nowrap" }}>
                {STEP_LABELS[s]}
              </span>
            </div>
            {i < STEPS.length - 1 && (
              <div style={{ flex: 1, height: 2, background: i < stepIdx ? "#10b981" : "#e2e8f0", margin: "0 4px", marginBottom: 20, transition: "background 0.3s" }} />
            )}
          </div>
        ))}
      </div>

      {done ? (
        <div className="card" style={{ textAlign: "center", padding: 48 }}>
          <div style={{ fontSize: 48, marginBottom: 12 }}>✅</div>
          <h2 style={{ fontSize: 22, fontWeight: 800, color: "#059669", margin: "0 0 8px" }}>Import Complete!</h2>
          <p style={{ color: "#64748b", margin: "0 0 24px" }}>Tender GEM/2025/B/47821 and 3 bidders have been imported successfully. OCR and extraction are running in the background.</p>
          <div style={{ display: "flex", gap: 12, justifyContent: "center" }}>
            <a href="/bidders" className="btn btn-primary">View Bidders →</a>
            <a href="/dashboard" className="btn btn-secondary">Back to Dashboard</a>
          </div>
        </div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 20 }}>
          <div className="card">
            <div className="card-header">
              <span className="card-title">
                {step === "tender" && "📋 Tender Import"}
                {step === "bidders" && "👥 Bidder Data Import"}
                {step === "documents" && "📄 Bid Documents"}
                {step === "processing" && "⚙️ Processing"}
              </span>
            </div>
            <div className="card-body">
              {step === "tender" && (
                <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                  <div className="form-group">
                    <label className="form-label">Import Method</label>
                    <div style={{ display: "flex", gap: 10 }}>
                      {["GeM API", "Upload JSON/CSV", "Manual Entry"].map(m => (
                        <button key={m} className={`btn btn-sm ${m === "Upload JSON/CSV" ? "btn-primary" : "btn-secondary"}`}>{m}</button>
                      ))}
                    </div>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Tender ID</label>
                    <input className="form-input" defaultValue="GEM/2025/B/47821" />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Tender Title</label>
                    <input className="form-input" defaultValue="Supply of IT Equipment" />
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                    <div className="form-group">
                      <label className="form-label">Department</label>
                      <input className="form-input" defaultValue="Ministry of Electronics & IT" />
                    </div>
                    <div className="form-group">
                      <label className="form-label">Bid Closing Date</label>
                      <input className="form-input" type="date" defaultValue="2026-09-30" />
                    </div>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Upload Tender JSON / PDF</label>
                    <div style={{ border: "2px dashed #e2e8f0", borderRadius: 8, padding: "24px", textAlign: "center", cursor: "pointer", background: "#f8fafc" }}>
                      <div style={{ fontSize: 24, marginBottom: 6 }}>📁</div>
                      <div style={{ fontSize: 13, color: "#64748b" }}>Drag & drop or click to upload tender file</div>
                      <div style={{ fontSize: 11, color: "#94a3b8", marginTop: 4 }}>Supports JSON, CSV, PDF</div>
                    </div>
                  </div>
                </div>
              )}

              {step === "bidders" && (
                <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                  <div style={{ background: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: 8, padding: "12px 16px", fontSize: 13, color: "#166534" }}>
                    ✅ Tender GEM/2025/B/47821 imported. Now import bidder data.
                  </div>
                  <div className="form-group">
                    <label className="form-label">Upload Bidder CSV / JSON</label>
                    <div style={{ border: "2px dashed #e2e8f0", borderRadius: 8, padding: "24px", textAlign: "center", background: "#f8fafc", cursor: "pointer" }}>
                      <div style={{ fontSize: 24, marginBottom: 6 }}>👥</div>
                      <div style={{ fontSize: 13, color: "#64748b" }}>Drop bidder data file or click to browse</div>
                    </div>
                  </div>
                  <div style={{ background: "#fffff0", borderRadius: 8, padding: 12, fontSize: 12, color: "#64748b" }}>
                    <strong>Demo dataset:</strong> 3 bidders will be loaded — Aster Tech Pvt Ltd, Bharat Supplies Pvt Ltd, Crest Systems Pvt Ltd.
                  </div>
                </div>
              )}

              {step === "documents" && (
                <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                  <div style={{ background: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: 8, padding: "12px 16px", fontSize: 13, color: "#166534" }}>
                    ✅ 3 bidders imported. Now upload bid documents.
                  </div>
                  {["BID-001 — Aster Tech", "BID-002 — Bharat Supplies", "BID-003 — Crest Systems"].map(b => (
                    <div key={b} style={{ border: "1px solid #e2e8f0", borderRadius: 8, padding: 14 }}>
                      <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 10 }}>{b}</div>
                      <div style={{ border: "2px dashed #e2e8f0", borderRadius: 6, padding: 14, textAlign: "center", background: "#f8fafc", cursor: "pointer" }}>
                        <div style={{ fontSize: 13, color: "#64748b" }}>📄 Drop documents or click to upload (GST, PAN, Udyam, OEM, etc.)</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {step === "processing" && isProcessing && (
                <div style={{ textAlign: "center", padding: 48 }}>
                  <div style={{ fontSize: 40, marginBottom: 12 }}>⚙️</div>
                  <h3 style={{ fontSize: 18, fontWeight: 700, color: "#0f172a", margin: "0 0 8px" }}>Processing Documents...</h3>
                  <p style={{ color: "#64748b", marginBottom: 20 }}>Running OCR, extracting fields, calling verification connectors...</p>
                  <div className="progress-bar" style={{ height: 8, borderRadius: 4 }}>
                    <div className="progress-bar-fill progress-blue" style={{ width: "65%", animation: "pulse 1.5s infinite" }} />
                  </div>
                </div>
              )}

              <div style={{ marginTop: 20, display: "flex", justifyContent: "space-between" }}>
                <button className="btn btn-secondary" onClick={() => { const i = STEPS.indexOf(step); if (i > 0) setStep(STEPS[i-1]); }} disabled={step === "tender"}>
                  ← Back
                </button>
                <button className="btn btn-primary" onClick={advance} disabled={isProcessing}>
                  {step === "documents" ? "Start Processing →" : "Next →"}
                </button>
              </div>
            </div>
          </div>

          {/* Sidebar preview */}
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <div className="card">
              <div className="card-header"><span className="card-title">📋 Import Summary</span></div>
              <div className="card-body">
                {[
                  { label: "Tender", value: stepIdx >= 1 ? "✅ GEM/2025/B/47821" : "Pending" },
                  { label: "Bidders", value: stepIdx >= 2 ? "✅ 3 bidders" : "Pending" },
                  { label: "Documents", value: stepIdx >= 3 ? "✅ 13 documents" : "Pending" },
                  { label: "Processing", value: done ? "✅ Complete" : "Pending" },
                ].map(r => (
                  <div key={r.label} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: "1px solid #f1f5f9", fontSize: 12 }}>
                    <span style={{ color: "#64748b" }}>{r.label}</span>
                    <span style={{ fontWeight: 600, color: r.value.startsWith("✅") ? "#059669" : "#94a3b8" }}>{r.value}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="card">
              <div className="card-header"><span className="card-title">ℹ️ Notes</span></div>
              <div className="card-body" style={{ fontSize: 12, color: "#64748b", lineHeight: 1.6 }}>
                <p style={{ margin: "0 0 8px" }}>All uploaded documents are hashed (SHA-256) before processing.</p>
                <p style={{ margin: "0 0 8px" }}>OCR runs on PDF/image documents. Extraction confidence scores are shown per field.</p>
                <p style={{ margin: 0 }}>Connectors run in DEMO mode. No live government data is accessed.</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
