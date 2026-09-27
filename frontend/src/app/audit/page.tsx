import { DEMO_AUDIT_EVENTS } from "@/lib/mockData";

const TYPE_COLOR: Record<string, string> = {
  import: "#1a56db",
  security: "#6366f1",
  ocr: "#8b5cf6",
  extraction: "#ec4899",
  verification: "#0891b2",
  rules: "#059669",
  conflict: "#ef4444",
  recommendation: "#f59e0b",
  officer: "#7c3aed",
};

const TYPE_ICON: Record<string, string> = {
  import: "⬆️", security: "🔒", ocr: "🔬", extraction: "🤖",
  verification: "🔍", rules: "⚖️", conflict: "⚠️",
  recommendation: "💡", officer: "👨‍⚖️",
};

export default function AuditPage() {
  return (
    <>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 12, marginBottom: 20 }}>
        {[
          { label: "Total Events", value: DEMO_AUDIT_EVENTS.length, color: "#1e40af", bg: "#eff6ff" },
          { label: "Imports", value: DEMO_AUDIT_EVENTS.filter(e => e.type === "import").length, color: "#1e40af", bg: "#eff6ff" },
          { label: "Conflicts Flagged", value: DEMO_AUDIT_EVENTS.filter(e => e.type === "conflict").length, color: "#dc2626", bg: "#fef2f2" },
          { label: "Officer Actions", value: DEMO_AUDIT_EVENTS.filter(e => e.type === "officer").length, color: "#7c3aed", bg: "#f5f3ff" },
        ].map(c => (
          <div key={c.label} style={{ background: c.bg, border: `1px solid ${c.color}22`, borderRadius: 10, padding: "14px 18px" }}>
            <div style={{ fontSize: 11, color: c.color, fontWeight: 700 }}>{c.label}</div>
            <div style={{ fontSize: 28, fontWeight: 900, color: c.color }}>{c.value}</div>
          </div>
        ))}
      </div>

      <div className="card">
        <div className="card-header">
          <span className="card-title">📅 Audit Event Timeline</span>
          <div style={{ display: "flex", gap: 8 }}>
            <span className="badge badge-gray">Tender: GEM/2025/B/47821</span>
            <span className="badge badge-blue">Session: 27 Sep 2026</span>
          </div>
        </div>
        <div className="card-body">
          <div className="timeline">
            {DEMO_AUDIT_EVENTS.map((ev, i) => (
              <div key={i} className="timeline-item">
                <div className="timeline-connector">
                  <div className="timeline-dot" style={{ background: TYPE_COLOR[ev.type] ?? "#1a56db", width: 12, height: 12 }} />
                  {i < DEMO_AUDIT_EVENTS.length - 1 && <div className="timeline-line" />}
                </div>
                <div className="timeline-content">
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 2 }}>
                    <span style={{ fontSize: 13 }}>{TYPE_ICON[ev.type]}</span>
                    <span className="timeline-event">{ev.event}</span>
                    <span className={`badge ${ev.type === "conflict" ? "badge-red" : ev.type === "officer" ? "badge-orange" : "badge-blue"}`}
                      style={{ fontSize: 9 }}>{ev.type.toUpperCase()}</span>
                  </div>
                  <div style={{ display: "flex", gap: 8 }}>
                    <span className="timeline-time">⏰ {ev.time}</span>
                    <span className="timeline-time">·</span>
                    <span className="timeline-time">Actor: {ev.actor}</span>
                  </div>
                  <div className="timeline-desc" style={{ marginTop: 2 }}>{ev.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}
