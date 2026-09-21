import React, { useState } from "react";
import { API_BASE } from "./apiBase";

export default function Login({ onAuthenticated }) {
  const [mode, setMode] = useState("login"); // "login" | "register"
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    const path = mode === "login" ? "/api/auth/login" : "/api/auth/register";
    const body =
      mode === "login"
        ? { username, password }
        : { username, email, password, role: "user" };

    try {
      const res = await fetch(`${API_BASE}${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      });

      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail.detail || `${mode} failed`);
      }

      const data = await res.json();
      onAuthenticated({ token: data.token, username: data.username, role: data.role });
    } catch (err) {
      setError(err.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.wrapper}>
      <div style={styles.panelPair}>
        <div style={styles.brandPanel}>
          <svg style={styles.brandMark} viewBox="0 0 48 48" fill="none" aria-hidden="true">
            <circle cx="24" cy="24" r="22" stroke="#E8672B" strokeWidth="2" />
            <path
              d="M24 6 L27 21 L42 24 L27 27 L24 42 L21 27 L6 24 L21 21 Z"
              fill="#E8672B"
            />
          </svg>
          <div style={styles.brandWordmark}>Unified Travel Agent</div>
          <p style={styles.brandTagline}>
            One assistant for flights, hotels, itineraries, and everywhere in between.
          </p>
          <div style={styles.brandDivider} />
          <ul style={styles.brandList}>
            <li>Real-time flight &amp; hotel search</li>
            <li>Day-by-day itinerary planning</li>
            <li>Remembers your last few trips</li>
          </ul>
        </div>

        <form onSubmit={submit} style={styles.formPanel}>
          <h2 style={styles.formTitle}>
            {mode === "login" ? "Welcome back" : "Create your account"}
          </h2>
          <p style={styles.formSubtitle}>
            {mode === "login" ? "Log in to continue planning." : "Start planning your next trip."}
          </p>

          <label style={styles.label} htmlFor="username">Username</label>
          <input
            id="username"
            type="text"
            placeholder="e.g. jane_traveler"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            style={styles.input}
            autoFocus
            required
          />

          {mode === "register" && (
            <>
              <label style={styles.label} htmlFor="email">Email</label>
              <input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                style={styles.input}
                required
              />
            </>
          )}

          <label style={styles.label} htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={styles.input}
            required
          />

          {error && <div style={styles.error}>{error}</div>}

          <button type="submit" disabled={loading} style={styles.button}>
            {loading ? "Please wait..." : mode === "login" ? "Log In" : "Create Account"}
          </button>

          <button
            type="button"
            onClick={() => {
              setError("");
              setMode(mode === "login" ? "register" : "login");
            }}
            style={styles.switchButton}
          >
            {mode === "login" ? "Need an account? Register" : "Already have an account? Log in"}
          </button>
        </form>
      </div>
    </div>
  );
}

const styles = {
  wrapper: {
    width: "100vw",
    height: "100vh",
    backgroundColor: "#12162a",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    padding: "24px",
    boxSizing: "border-box"
  },
  panelPair: {
    width: "100%",
    maxWidth: "880px",
    minHeight: "560px",
    backgroundColor: "#ffffff",
    borderRadius: "16px",
    boxShadow: "0 20px 60px rgba(0,0,0,0.35)",
    display: "flex",
    overflow: "hidden"
  },
  brandPanel: {
    flex: "0 0 42%",
    backgroundColor: "#1b2340",
    color: "#ffffff",
    padding: "48px 40px",
    display: "flex",
    flexDirection: "column",
    justifyContent: "center"
  },
  brandMark: {
    width: "40px",
    height: "40px",
    marginBottom: "20px"
  },
  brandWordmark: {
    fontFamily: "'Manrope', sans-serif",
    fontWeight: 800,
    fontSize: "26px",
    lineHeight: 1.2,
    marginBottom: "12px"
  },
  brandTagline: {
    fontFamily: "'Work Sans', sans-serif",
    fontSize: "14.5px",
    lineHeight: 1.6,
    color: "#c3c8dc",
    marginBottom: "24px",
    maxWidth: "26ch"
  },
  brandDivider: {
    width: "40px",
    height: "3px",
    backgroundColor: "#e8672b",
    borderRadius: "2px",
    marginBottom: "24px"
  },
  brandList: {
    listStyle: "none",
    display: "flex",
    flexDirection: "column",
    gap: "12px",
    fontFamily: "'Work Sans', sans-serif",
    fontSize: "13.5px",
    color: "#e4e6f2"
  },
  formPanel: {
    flex: "1 1 58%",
    padding: "48px 44px",
    display: "flex",
    flexDirection: "column",
    justifyContent: "center"
  },
  formTitle: {
    fontFamily: "'Manrope', sans-serif",
    fontWeight: 700,
    fontSize: "24px",
    color: "#171b2e",
    margin: 0
  },
  formSubtitle: {
    fontFamily: "'Work Sans', sans-serif",
    margin: "6px 0 24px",
    color: "#5c6478",
    fontSize: "14px"
  },
  label: {
    fontFamily: "'Work Sans', sans-serif",
    fontSize: "12.5px",
    fontWeight: 600,
    color: "#5c6478",
    marginBottom: "6px",
    display: "block"
  },
  input: {
    width: "100%",
    padding: "12px 14px",
    borderRadius: "10px",
    border: "1px solid #dee3ec",
    fontSize: "15px",
    fontFamily: "'Work Sans', sans-serif",
    outline: "none",
    marginBottom: "16px",
    backgroundColor: "#fbfbfc"
  },
  error: {
    color: "#c0362c",
    fontSize: "13px",
    fontFamily: "'Work Sans', sans-serif",
    marginBottom: "14px"
  },
  button: {
    padding: "13px 16px",
    borderRadius: "10px",
    border: "none",
    backgroundColor: "#e8672b",
    color: "#ffffff",
    cursor: "pointer",
    fontFamily: "'Manrope', sans-serif",
    fontSize: "15px",
    fontWeight: 700,
    marginBottom: "12px"
  },
  switchButton: {
    padding: "6px",
    borderRadius: "8px",
    border: "none",
    backgroundColor: "transparent",
    color: "#e8672b",
    cursor: "pointer",
    fontFamily: "'Work Sans', sans-serif",
    fontWeight: 600,
    fontSize: "13px"
  }
};
