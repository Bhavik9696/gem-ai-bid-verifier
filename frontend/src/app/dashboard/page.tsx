import { DEMO_TENDERS, DEMO_BIDDERS, DEMO_AUDIT_EVENTS } from "@/lib/mockData";
import Link from "next/link";

function StatCard({ label, value, change, sub, icon, color }: {
  label: string; value: string; change?: string; sub?: string; icon: string; color?: string;
}) {
  const isUp = change?.includes("+");
  return (
    <div className="stat-card">
      <div className="stat-card-label" style={{ color }}>
        <span>{icon}</span> {label}
      </div>
      <div className="stat-card-value">{value}</div>
      {change && (
        <div className={`stat-card-change ${isUp ? "change-up" : "change-down"}`}>
          <span>{isUp ? "▲" : "▼"}</span> {change}
        </div>
      )}
      {sub && <div className="stat-card-sub">{sub}</div>}
    </div>
  );
}

function DonutChart({ data }: { data: { label: string; value: number; color: string }[] }) {
  const total = data.reduce((s, d) => s + d.value, 0);
  let cumulative = 0;
  const cx = 70; const cy = 70; const r = 54; const stroke = 20;
  const circ = 2 * Math.PI * r;

  return (
    <div style={{ display: "flex", gap: 20, alignItems: "center" }}>
      <div className="donut-wrap">
        <svg width="140" height="140" className="donut-svg">
          {data.map((d, i) => {
            const pct = d.value / total;
            const offset = circ * (1 - cumulative);
            const dash = circ * pct;
            cumulative += pct;
            return (
              <circle key={i} cx={cx} cy={cy} r={r}
                fill="none" stroke={d.color} strokeWidth={stroke}
                strokeDasharray={`${dash} ${circ - dash}`}
                strokeDashoffset={offset}
                style={{ transition: "stroke-dasharray 0.4s" }}
              />
            );
          })}
        </svg>
        <div className="donut-label">
          <div className="donut-val">{total}</div>
          <div className="donut-sub">Total</div>
        </div>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {data.map(d => (
          <div key={d.label} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 24 }}>
            <div className="legend-item">
              <div className="legend-dot" style={{ background: d.color }} />
              <span style={{ fontSize: 12, color: "#374151" }}>{d.label}</span>
            </div>
            <div style={{ display: "flex", gap: 8 }}>
              <span style={{ fontSize: 12, fontWeight: 700, color: "#0f172a" }}>{d.value}</span>
              <span style={{ fontSize: 11, color: "#94a3b8" }}>{Math.round(d.value / total * 100)}%</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function MiniLineChart() {
  const points = [400, 520, 680, 580, 720, 900, 1050, 1200, 1100, 1350, 1500, 1420, 1600, 1580];
  const verified = [200, 280, 380, 320, 450, 600, 720, 900, 850, 1050, 1200, 1100, 1250, 1200];
  const w = 320; const h = 80;
  const max = Math.max(...points);
  const xs = points.map((_, i) => (i / (points.length - 1)) * w);
  const ys = (arr: number[]) => arr.map(v => h - (v / max) * h * 0.9 - 5);

  const path = (arr: number[]) =>
    xs.map((x, i) => `${i === 0 ? "M" : "L"} ${x} ${ys(arr)[i]}`).join(" ");

  return (
    <svg width={w} height={h + 10} className="line-chart" viewBox={`0 0 ${w} ${h + 10}`}>
      <defs>
        <linearGradient id="lg1" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.3" />
          <stop offset="100%" stopColor="#3b82f6" stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={path(points) + ` L ${w} ${h} L 0 ${h} Z`} fill="url(#lg1)" />
      <path d={path(points)} fill="none" stroke="#3b82f6" strokeWidth="2" strokeLinejoin="round" />
      <path d={path(verified)} fill="none" stroke="#10b981" strokeWidth="2" strokeLinejoin="round" strokeDasharray="4 2" />
    </svg>
  );
}

const STATUS_COLORS: Record<string, string> = {
  "Published": "badge-blue",
  "Under Evaluation": "badge-yellow",
  "Awarded": "badge-green",
  "Cancelled": "badge-red",
};

const RISK_CONF: Record<string, { cls: string; dot: string }> = {
  Low: { cls: "risk-low", dot: "#10b981" },
  High: { cls: "risk-high", dot: "#ef4444" },
  Critical: { cls: "risk-critical", dot: "#7c3aed" },
  Medium: { cls: "risk-medium", dot: "#f59e0b" },
};

function BidderRow({ b }: { b: typeof DEMO_BIDDERS[0] }) {
  const risk = RISK_CONF[b.riskLevel] ?? { cls: "", dot: "#94a3b8" };
  return (
    <tr>
      <td>
        <div style={{ fontWeight: 600, color: "#0f172a", fontSize: 13 }}>{b.legalName}</div>
        <div style={{ fontSize: 11, color: "#94a3b8" }}>{b.id}</div>
      </td>
      <td>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <div className="progress-bar" style={{ width: 60 }}>
            <div className={`progress-bar-fill ${b.complianceScore >= 90 ? "progress-green" : b.complianceScore >= 75 ? "progress-yellow" : "progress-red"}`}
              style={{ width: `${b.complianceScore}%` }} />
          </div>
          <span style={{ fontSize: 12, fontWeight: 700 }}>{b.complianceScore}%</span>
        </div>
      </td>
      <td>
        <div style={{ fontSize: 12, fontWeight: 600 }}>{b.verificationScore}%</div>
      </td>
      <td>
        <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
          <span style={{ width: 8, height: 8, borderRadius: "50%", background: risk.dot, display: "inline-block" }} />
          <span className={risk.cls} style={{ fontSize: 12 }}>{b.riskLevel}</span>
        </div>
      </td>
      <td>
        <span className={`badge ${b.status === "Compliant" ? "badge-green" : b.status === "High-Risk" ? "badge-red" : "badge-yellow"}`}>
          {b.statusLabel}
        </span>
      </td>
      <td>
        <Link href={`/bidders/${b.id}`} className="btn btn-secondary btn-sm">View →</Link>
      </td>
    </tr>
  );
}

export default function DashboardPage() {
  const donutData = [
    { label: "Published", value: 412, color: "#3b82f6" },
    { label: "Under Evaluation", value: 231, color: "#f59e0b" },
    { label: "Awarded", value: 128, color: "#10b981" },
    { label: "Cancelled", value: 42, color: "#ef4444" },
    { label: "Others", value: 29, color: "#cbd5e1" },
  ];

  return (
    <>
      <div className="demo-banner">
        ⚠️ <strong>DEMO MODE:</strong> This is a demo environment with sample data only. Connector results are from the DEMO dataset, not live government sources.
      </div>

      {/* Stat Cards */}
      <div className="stat-cards">
        <StatCard icon="📋" label="Total Tenders" value="842" change="+12%" sub="vs. last 7 days" />
        <StatCard icon="📥" label="Bids Received" value="3,467" change="+18%" sub="vs. last 7 days" />
        <StatCard icon="✅" label="Verified Bidders" value="2,913" change="+16%" sub="vs. last 7 days" />
        <StatCard icon="🚩" label="Flagged for Review" value="142" change="+23%" sub="vs. last 7 days" color="#ef4444" />
        <StatCard icon="⏱️" label="Avg. Processing Time" value="4.2 hrs" change="-36%" sub="vs. last 7 days" />
      </div>

      {/* Row 1: Donut + Line Chart + Risk */}
      <div className="dash-grid dash-grid-3 mb-4">
        <div className="card">
          <div className="card-header">
            <span className="card-title">📊 Tender Status</span>
            <Link href="/tenders" className="card-link">View All →</Link>
          </div>
          <div className="card-body">
            <DonutChart data={donutData} />
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <span className="card-title">📈 Bid Verification Trend</span>
            <select className="form-select" style={{ fontSize: 11, padding: "3px 8px" }}>
              <option>Last 7 Days</option>
              <option>Last 30 Days</option>
            </select>
          </div>
          <div className="card-body">
            <div style={{ display: "flex", gap: 16, marginBottom: 10 }}>
              <div className="legend-item"><div className="legend-dot" style={{ background: "#3b82f6" }} /><span style={{ fontSize: 11 }}>Total Bids</span></div>
              <div className="legend-item"><div className="legend-dot" style={{ background: "#10b981" }} /><span style={{ fontSize: 11 }}>Verified Bids</span></div>
            </div>
            <MiniLineChart />
            <div style={{ display: "flex", justifyContent: "space-between", marginTop: 4 }}>
              {["22 Apr", "23 Apr", "24 Apr", "25 Apr", "26 Apr", "27 Apr", "28 Apr"].map(d => (
                <span key={d} style={{ fontSize: 9, color: "#94a3b8" }}>{d}</span>
              ))}
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <span className="card-title">⚠️ Top Risk Indicators</span>
            <Link href="/conflicts" className="card-link">View All →</Link>
          </div>
          <div className="card-body">
            {[
              { label: "High Risk", val: 42, pct: "17%", cls: "badge-red" },
              { label: "Medium Risk", val: 67, pct: "27%", cls: "badge-yellow" },
              { label: "Low Risk", val: 98, pct: "40%", cls: "badge-green" },
              { label: "No Risk", val: 41, pct: "16%", cls: "badge-blue" },
            ].map(r => (
              <div key={r.label} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "8px 0", borderBottom: "1px solid #f1f5f9" }}>
                <span className={`badge ${r.cls}`}>{r.label}</span>
                <span style={{ fontWeight: 700, fontSize: 13 }}>{r.val}</span>
                <span style={{ fontSize: 11, color: "#94a3b8" }}>{r.pct}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Row 2: Recent Tenders + Quick Actions + System Health */}
      <div className="dash-grid dash-grid-3">
        <div className="card" style={{ gridColumn: "1/2" }}>
          <div className="card-header">
            <span className="card-title">📋 Recent Tenders</span>
            <Link href="/tenders" className="card-link">View All →</Link>
          </div>
          <div style={{ overflowX: "auto" }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Tender ID</th>
                  <th>Title</th>
                  <th>Department</th>
                  <th>Status</th>
                  <th>Bids</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {DEMO_TENDERS.map(t => (
                  <tr key={t.id}>
                    <td className="link-cell" style={{ fontSize: 11, fontFamily: "monospace" }}>{t.id}</td>
                    <td style={{ fontWeight: 500, maxWidth: 160, fontSize: 12 }}>{t.title}</td>
                    <td style={{ fontSize: 11, color: "#64748b" }}>{t.department}</td>
                    <td><span className={`badge ${STATUS_COLORS[t.status] ?? "badge-gray"}`} style={{ fontSize: 10 }}>{t.status}</span></td>
                    <td style={{ fontWeight: 700, textAlign: "center" }}>{t.bidderCount}</td>
                    <td><Link href={`/tenders`} className="btn btn-secondary btn-sm">View →</Link></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 16, gridColumn: "2/3" }}>
          <div className="card">
            <div className="card-header">
              <span className="card-title">⚡ Quick Actions</span>
            </div>
            <div className="card-body">
              {[
                { icon: "⬆️", label: "Import Tender / Bid", sub: "From GeM or external source", href: "/tenders/import" },
                { icon: "👥", label: "Verify Bidder", sub: "Check profile, KYC & history", href: "/bidders" },
                { icon: "✅", label: "Run Compliance Check", sub: "Screen for rules & conflicts", href: "/compliance" },
                { icon: "📊", label: "Generate Report", sub: "Download audit & compliance", href: "/reports" },
              ].map(a => (
                <Link href={a.href} key={a.label} style={{ textDecoration: "none" }}>
                  <div className="quick-action">
                    <div className="qa-left">
                      <span className="qa-icon">{a.icon}</span>
                      <div>
                        <div className="qa-label">{a.label}</div>
                        <div className="qa-sub">{a.sub}</div>
                      </div>
                    </div>
                    <span className="qa-arrow">›</span>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </div>

        <div className="card" style={{ gridColumn: "3/4" }}>
          <div className="card-header">
            <span className="card-title">🛡️ System Health</span>
          </div>
          <div className="card-body">
            {[
              "AI Model Service", "Document Processing", "Bidder Verification",
              "Compliance Engine", "Audit Logging", "Database",
            ].map(s => (
              <div key={s} className="health-item">
                <span className="health-name">{s}</span>
                <span className="health-status">
                  <span className="status-dot" /> Healthy
                </span>
              </div>
            ))}
            <div style={{ marginTop: 12, padding: "8px 10px", background: "#f0fdf4", borderRadius: 6, fontSize: 11, color: "#166534" }}>
              ℹ️ No active alerts. All systems are running normally.
            </div>
          </div>
        </div>
      </div>

      {/* Bidders table */}
      <div className="card mt-4">
        <div className="card-header">
          <span className="card-title">👥 Bidders – Current Tender (GEM/2025/B/47821)</span>
          <Link href="/bidders" className="card-link">View All →</Link>
        </div>
        <div style={{ padding: "4px 0 0" }}>
          <div style={{ display: "flex", gap: 8, padding: "0 20px 12px" }}>
            <span className="badge badge-gray">Total: 3</span>
            <span className="badge badge-green">Ready: 1</span>
            <span className="badge badge-yellow">Review: 1</span>
            <span className="badge badge-red">Critical: 1</span>
          </div>
          <table className="data-table">
            <thead>
              <tr>
                <th>Bidder</th><th>Compliance</th><th>Verification</th><th>Risk</th><th>Status</th><th>Action</th>
              </tr>
            </thead>
            <tbody>{DEMO_BIDDERS.map(b => <BidderRow key={b.id} b={b} />)}</tbody>
          </table>
        </div>
      </div>

      {/* Recent audit events */}
      <div className="card mt-4">
        <div className="card-header">
          <span className="card-title">📅 Recent Audit Events</span>
          <Link href="/audit" className="card-link">Full Timeline →</Link>
        </div>
        <div className="card-body">
          <div className="timeline">
            {DEMO_AUDIT_EVENTS.slice(0, 6).map((ev, i) => (
              <div key={i} className="timeline-item">
                <div className="timeline-connector">
                  <div className="timeline-dot" style={{ background: ev.type === "conflict" ? "#ef4444" : ev.type === "officer" ? "#8b5cf6" : "#1a56db" }} />
                  {i < 5 && <div className="timeline-line" />}
                </div>
                <div className="timeline-content">
                  <div className="timeline-time">{ev.time} · {ev.actor}</div>
                  <div className="timeline-event">{ev.event}</div>
                  <div className="timeline-desc">{ev.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}
