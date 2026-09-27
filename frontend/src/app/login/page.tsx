"use client";
import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

const ROLES = [
  { id: "officer", label: "Procurement Officer", icon: "👨‍💼" },
  { id: "reviewer", label: "Reviewer", icon: "🔍" },
  { id: "admin", label: "Admin", icon: "⚙️" },
  { id: "auditor", label: "Auditor", icon: "🛡️" },
];

const FEATURES = [
  { icon: "📄", title: "Document Intelligence", desc: "Extract & verify documents with AI" },
  { icon: "🏛️", title: "Government Verification", desc: "Cross-check with official sources" },
  { icon: "✅", title: "Compliance & Conflict Detection", desc: "Check rules, risks & conflicts" },
  { icon: "🤖", title: "Explainable AI Recommendations", desc: "Transparent reasoning with evidence" },
  { icon: "👨‍⚖️", title: "Officer Review", desc: "You make the final decision" },
  { icon: "📅", title: "Audit Trail & Reports", desc: "Complete traceability and downloadable reports" },
];

export default function LoginPage() {
  const [role, setRole] = useState("officer");
  const [showPw, setShowPw] = useState(false);
  const router = useRouter();

  function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    router.push("/dashboard");
  }

  return (
    <div className="login-shell">
      {/* Left panel */}
      <div className="login-left">
        {/* Header */}
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 24 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "6px 12px", background: "rgba(255,255,255,0.08)", borderRadius: 8, border: "1px solid rgba(255,255,255,0.12)" }}>
              <span style={{ fontSize: 20 }}>🇮🇳</span>
              <div>
                <div style={{ fontSize: 10, color: "rgba(255,255,255,0.6)" }}>Government of India</div>
                <div style={{ fontSize: 12, fontWeight: 700, color: "white" }}>GeM · Government e-Marketplace</div>
              </div>
            </div>
            <div style={{ width: 1, height: 36, background: "rgba(255,255,255,0.15)" }} />
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <div style={{ width: 32, height: 32, background: "linear-gradient(135deg,#1a56db,#06b6d4)", borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 16 }}>🛡️</div>
              <div>
                <div style={{ fontSize: 13, fontWeight: 800, color: "white" }}>GeM AI Bid Verifier</div>
                <div style={{ fontSize: 10, color: "rgba(255,255,255,0.5)" }}>AI-Powered Bid Verification for Government Procurement</div>
              </div>
            </div>
          </div>

          {/* Demo badge */}
          <div style={{ display: "inline-flex", alignItems: "center", gap: 6, background: "rgba(16,185,129,0.15)", border: "1px solid rgba(16,185,129,0.3)", borderRadius: 6, padding: "4px 10px", marginBottom: 32 }}>
            <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#10b981", display: "inline-block" }} />
            <span style={{ fontSize: 10, fontWeight: 700, color: "#34d399", letterSpacing: 1 }}>DEMO MODE</span>
            <span style={{ fontSize: 9, color: "rgba(255,255,255,0.4)" }}>· This is a demo environment with sample data only.</span>
          </div>

          {/* Tagline */}
          <div style={{ display: "flex", gap: 16, marginBottom: 16 }}>
            {["FAIR", "TRANSPARENT", "EFFICIENT"].map(t => (
              <span key={t} style={{ fontSize: 10, fontWeight: 700, color: "rgba(255,255,255,0.4)", letterSpacing: 2 }}>{t}</span>
            ))}
          </div>
          <h1 style={{ fontSize: 40, fontWeight: 900, color: "white", lineHeight: 1.1, margin: "0 0 8px" }}>
            Smarter Procurement.
          </h1>
          <h2 style={{ fontSize: 40, fontWeight: 900, color: "#06b6d4", lineHeight: 1.1, margin: "0 0 20px" }}>
            Stronger India.
          </h2>
          <p style={{ fontSize: 14, color: "rgba(255,255,255,0.65)", lineHeight: 1.7, maxWidth: 380 }}>
            GeM AI Bid Verifier helps procurement officers verify bids with AI-powered document intelligence, government source checks and compliance rules — while you make the final decision.
          </p>

          {/* Feature grid */}
          <div className="feature-grid" style={{ marginTop: 28 }}>
            {FEATURES.map(f => (
              <div key={f.title} className="feature-item">
                <div className="feature-icon">{f.icon}</div>
                <div className="feature-title">{f.title}</div>
                <div className="feature-desc">{f.desc}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer tagline */}
        <div style={{ fontFamily: "Georgia, serif", fontStyle: "italic", fontSize: 18, color: "rgba(255,255,255,0.35)", marginTop: 24 }}>
          Better Decisions.<br />
          <span style={{ color: "#06b6d4", fontWeight: 600 }}>Greater Impact.</span>
        </div>
      </div>

      {/* Right panel – login form */}
      <div className="login-right">
        <div className="login-form-wrap">
          <h2 style={{ fontSize: 26, fontWeight: 800, color: "#0f172a", margin: "0 0 6px" }}>Welcome Back</h2>
          <p style={{ fontSize: 13, color: "#64748b", margin: "0 0 28px" }}>Sign in to your GeM AI Bid Verifier account</p>

          <form onSubmit={handleLogin}>
            <div className="form-group" style={{ marginBottom: 16 }}>
              <label className="form-label">Email / Username</label>
              <div className="input-icon-wrap">
                <span className="input-icon">✉️</span>
                <input className="form-input with-icon" type="email" placeholder="officer@nic.in" defaultValue="officer@nic.in" />
              </div>
            </div>

            <div className="form-group" style={{ marginBottom: 16 }}>
              <label className="form-label">Password</label>
              <div className="input-icon-wrap">
                <span className="input-icon">🔒</span>
                <input
                  className="form-input with-icon with-icon-right"
                  type={showPw ? "text" : "password"}
                  placeholder="Enter your password"
                  defaultValue="demo1234"
                />
                <span className="input-icon-right" onClick={() => setShowPw(!showPw)}>
                  {showPw ? "🙈" : "👁️"}
                </span>
              </div>
            </div>

            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
              <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13, color: "#374151", cursor: "pointer" }}>
                <input type="checkbox" defaultChecked style={{ accentColor: "#1a56db" }} />
                Remember me
              </label>
              <a href="#" style={{ fontSize: 13, color: "#1a56db", fontWeight: 600 }}>Forgot password?</a>
            </div>

            <button type="submit" className="btn btn-primary btn-lg w-full" style={{ marginBottom: 20, fontSize: 15, letterSpacing: 0.3 }}>
              Login →
            </button>

            <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 20 }}>
              <div style={{ flex: 1, height: 1, background: "#e2e8f0" }} />
              <span style={{ fontSize: 12, color: "#94a3b8" }}>OR</span>
              <div style={{ flex: 1, height: 1, background: "#e2e8f0" }} />
            </div>

            <div style={{ marginBottom: 8 }}>
              <p style={{ fontSize: 13, fontWeight: 600, color: "#374151", marginBottom: 10 }}>Select Your Role</p>
              {ROLES.map(r => (
                <div
                  key={r.id}
                  className={`role-option${role === r.id ? " selected" : ""}`}
                  onClick={() => setRole(r.id)}
                >
                  <div className="role-left">
                    <span className="role-icon">{r.icon}</span>
                    <span className="role-name">{r.label}</span>
                  </div>
                  <span style={{ color: "#94a3b8", fontSize: 14 }}>›</span>
                </div>
              ))}
            </div>
          </form>

          <div style={{ marginTop: 20, textAlign: "center", borderTop: "1px solid #f1f5f9", paddingTop: 16 }}>
            <span style={{ fontSize: 11, color: "#94a3b8" }}>Version 1.0.0</span>
            <span style={{ fontSize: 11, color: "#cbd5e1", margin: "0 8px" }}>|</span>
            <span style={{ fontSize: 11, color: "#64748b" }}>GeM Integration</span>
            <span style={{ fontSize: 11, color: "#cbd5e1", margin: "0 8px" }}>|</span>
            <span style={{ fontSize: 11, color: "#64748b" }}>🔒 Secure Access</span>
          </div>
        </div>
      </div>
    </div>
  );
}
