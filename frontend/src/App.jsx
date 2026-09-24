import React, { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import Login from "./Login";
import { API_BASE } from "./apiBase";

const WELCOME_MESSAGE = {
  sender: "agent",
  text: "Hello! I am your Unified Travel Agent. Where would you like to go?",
  agentName: "Travel Agent",
  time: Date.now()
};
const AUTH_STORAGE_KEY = "unified_travel_agent_auth";

function formatTime(ms) {
  return new Date(ms).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function formatDate(value) {
  const d = new Date(value);
  const today = new Date();
  const sameDay = d.toDateString() === today.toDateString();
  if (sameDay) return formatTime(d.getTime());
  return d.toLocaleDateString([], { month: "short", day: "numeric" });
}

function BrandMark({ style }) {
  return (
    <svg style={style} viewBox="0 0 48 48" fill="none" aria-hidden="true">
      <circle cx="24" cy="24" r="22" stroke="#E8672B" strokeWidth="2.5" />
      <path d="M24 6 L27 21 L42 24 L27 27 L24 42 L21 27 L6 24 L21 21 Z" fill="#E8672B" />
    </svg>
  );
}

export default function App() {
  const [auth, setAuth] = useState(() => {
    try {
      const stored = localStorage.getItem(AUTH_STORAGE_KEY);
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });

  const [messages, setMessages] = useState([WELCOME_MESSAGE]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  // A new session ID means a new conversation for tracing/fact-extraction purposes.
  const [sessionId, setSessionId] = useState(() => crypto.randomUUID());
  // Which past session (if any) is currently loaded in the chat pane, so the
  // sidebar can highlight it - null means "this is a fresh, not-yet-saved conversation".
  const [activeSessionId, setActiveSessionId] = useState(null);

  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [sidebarTab, setSidebarTab] = useState("history");
  const [conversations, setConversations] = useState([]);
  const [memories, setMemories] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  // What real PII (email/phone/etc.) this session's redaction tokens stand
  // for - fetched on demand from /api/pii/token-map, not kept refreshed
  // automatically, so it's always re-fetched when opened.
  const [tokenMap, setTokenMap] = useState(null);
  const [tokenMapOpen, setTokenMapOpen] = useState(false);

  const chatEndRef = useRef(null);
  const inputRef = useRef(null);

  const authedFetch = (path) =>
    fetch(`${API_BASE}${path}`, { headers: { Authorization: `Bearer ${auth.token}` } });

  const loadSidebarData = async () => {
    setHistoryLoading(true);
    try {
      const [convRes, memRes] = await Promise.all([
        authedFetch("/api/conversations"),
        authedFetch("/api/memory")
      ]);
      if (convRes.status === 401 || memRes.status === 401) {
        logout();
        return;
      }
      setConversations(convRes.ok ? await convRes.json() : []);
      setMemories(memRes.ok ? await memRes.json() : []);
    } catch {
      // sidebar data is a nice-to-have - a failed fetch just leaves it empty
    } finally {
      setHistoryLoading(false);
    }
  };

  // Keep the latest message in view without the user having to scroll down
  // themselves - it's easy to lose a reply below the fold once a
  // conversation grows past the first couple of turns.
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, loading]);

  useEffect(() => {
    if (auth) {
      inputRef.current?.focus();
      loadSidebarData();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [auth]);

  // A different session's token map shouldn't linger on screen once the
  // conversation switches - close the panel and drop the stale data.
  useEffect(() => {
    setTokenMap(null);
    setTokenMapOpen(false);
  }, [sessionId]);

  const toggleTokenMap = async () => {
    if (tokenMapOpen) {
      setTokenMapOpen(false);
      return;
    }
    try {
      const res = await authedFetch(`/api/pii/token-map/${sessionId}`);
      if (res.status === 401) {
        logout();
        return;
      }
      setTokenMap(res.ok ? await res.json() : {});
    } catch {
      setTokenMap({});
    }
    setTokenMapOpen(true);
  };

  const handleAuthenticated = (nextAuth) => {
    setAuth(nextAuth);
    try {
      localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(nextAuth));
    } catch {
      // localStorage unavailable - session still works, just won't persist a reload
    }
  };

  const logout = () => {
    setAuth(null);
    try {
      localStorage.removeItem(AUTH_STORAGE_KEY);
    } catch {
      // ignore
    }
    setMessages([WELCOME_MESSAGE]);
    setConversations([]);
    setMemories([]);
    setActiveSessionId(null);
  };

  const startNewConversation = () => {
    setMessages([WELCOME_MESSAGE]);
    setInput("");
    setSessionId(crypto.randomUUID());
    setActiveSessionId(null);
    inputRef.current?.focus();
  };

  const openConversation = async (targetSessionId) => {
    setHistoryLoading(true);
    try {
      const res = await authedFetch(`/api/conversations/${targetSessionId}`);
      if (res.status === 401) {
        logout();
        return;
      }
      if (!res.ok) return;

      const rows = await res.json();
      const loaded = rows.map((row) => ({
        sender: row.role === "user" ? "user" : "agent",
        text: row.content,
        agentName: row.role === "agent" ? "Travel Agent" : undefined,
        time: new Date(row.created_at).getTime()
      }));

      setMessages(loaded.length ? loaded : [WELCOME_MESSAGE]);
      setSessionId(targetSessionId);
      setActiveSessionId(targetSessionId);
      inputRef.current?.focus();
    } finally {
      setHistoryLoading(false);
    }
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMsg = input;
    setInput("");
    setMessages((prev) => [...prev, { sender: "user", text: userMsg, time: Date.now() }]);
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${auth.token}`
        },
        body: JSON.stringify({
          user_id: auth.username,
          session_id: sessionId,
          message: userMsg
        })
      });

      if (res.status === 401) {
        logout();
        return;
      }

      const data = await res.json();
      setMessages((prev) => [
        ...prev,
        {
          sender: "agent",
          text: data.response || "No response received.",
          agentName: data.agent_name || "Travel Agent",
          time: Date.now()
        }
      ]);
      setActiveSessionId(sessionId);
      loadSidebarData();
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { sender: "agent", text: "Error connecting to backend server.", agentName: "Travel Agent", time: Date.now() }
      ]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  if (!auth) {
    return <Login onAuthenticated={handleAuthenticated} />;
  }

  return (
    <div style={styles.wrapper}>
      <div style={styles.card}>
        {sidebarOpen && (
          <aside style={styles.sidebar}>
            <div style={styles.sidebarBrandRow}>
              <BrandMark style={styles.sidebarBrandMark} />
              <span style={styles.sidebarWordmark}>Unified Travel Agent</span>
            </div>

            <button type="button" onClick={startNewConversation} style={styles.newConvoButton}>
              + New Conversation
            </button>

            <div style={styles.tabRow}>
              <button
                type="button"
                onClick={() => setSidebarTab("history")}
                style={sidebarTab === "history" ? styles.tabButtonActive : styles.tabButton}
              >
                History
              </button>
              <button
                type="button"
                onClick={() => setSidebarTab("memory")}
                style={sidebarTab === "memory" ? styles.tabButtonActive : styles.tabButton}
              >
                Memory
              </button>
            </div>

            <div style={styles.listScroll}>
              {sidebarTab === "history" && (
                <>
                  {historyLoading && conversations.length === 0 && (
                    <div style={styles.sidebarHint}>Loading...</div>
                  )}
                  {!historyLoading && conversations.length === 0 && (
                    <div style={styles.sidebarHint}>No past conversations yet.</div>
                  )}
                  {conversations.map((c) => (
                    <button
                      key={c.session_id}
                      type="button"
                      onClick={() => openConversation(c.session_id)}
                      style={
                        c.session_id === activeSessionId
                          ? { ...styles.historyItem, ...styles.historyItemActive }
                          : styles.historyItem
                      }
                    >
                      <div style={styles.historyPreview}>{c.preview || "(empty conversation)"}</div>
                      <div style={styles.historyMeta}>
                        {formatDate(c.last_activity)} · {c.message_count} messages
                      </div>
                    </button>
                  ))}
                </>
              )}

              {sidebarTab === "memory" && (
                <>
                  {memories.length === 0 && (
                    <div style={styles.sidebarHint}>
                      Nothing remembered yet - it builds up as you chat.
                    </div>
                  )}
                  {memories.map((m, i) => (
                    <div key={i} style={styles.memoryItem}>
                      <div style={styles.memoryText}>{m.summary}</div>
                      <div style={styles.historyMeta}>{formatDate(m.updated_at)}</div>
                    </div>
                  ))}
                </>
              )}
            </div>

            <div style={styles.sidebarFooter}>
              <div style={{ minWidth: 0 }}>
                <div style={styles.accountLine}>
                  {auth.username} · {auth.role}
                </div>
                <div
                  style={styles.sessionIdLine}
                  title={`Session ID: ${sessionId} (click to copy)`}
                  onClick={() => navigator.clipboard?.writeText(sessionId)}
                >
                  Session: {sessionId.slice(0, 8)}…
                </div>
              </div>
              <button type="button" onClick={logout} style={styles.pillButtonQuiet}>
                Log Out
              </button>
            </div>

            <button type="button" onClick={toggleTokenMap} style={styles.tokenMapToggle}>
              {tokenMapOpen ? "Hide redacted PII ▲" : "View redacted PII ▼"}
            </button>
            {tokenMapOpen && (
              <div style={styles.tokenMapPanel}>
                {tokenMap && Object.keys(tokenMap).length ? (
                  Object.entries(tokenMap).map(([token, value]) => (
                    <div key={token} style={styles.tokenMapRow}>
                      <span style={styles.tokenMapToken}>{token}</span>
                      <span>→</span>
                      <span style={styles.tokenMapValue}>{value}</span>
                    </div>
                  ))
                ) : (
                  <div style={styles.tokenMapEmpty}>No PII redacted in this session yet.</div>
                )}
              </div>
            )}
          </aside>
        )}

        <div style={styles.mainColumn}>
          <header style={styles.header}>
            <div style={styles.brandRow}>
              <button
                type="button"
                onClick={() => setSidebarOpen((v) => !v)}
                style={styles.collapseToggle}
                aria-label="Toggle sidebar"
              >
                ☰
              </button>
              <h2 style={styles.title}>
                {activeSessionId ? "Conversation" : "New Conversation"}
              </h2>
            </div>
          </header>

          <div style={styles.chatBox}>
            {messages.map((msg, i) => (
              <div key={i} style={{ display: "flex", flexDirection: "column", alignItems: msg.sender === "user" ? "flex-end" : "flex-start" }}>
                {msg.sender === "agent" && (
                  <span style={styles.agentTag}>{msg.agentName || "Travel Agent"}</span>
                )}
                <div
                  style={{
                    ...styles.message,
                    backgroundColor: msg.sender === "user" ? "#1b2340" : "#ffffff",
                    color: msg.sender === "user" ? "#ffffff" : "#171b2e",
                    border: msg.sender === "user" ? "none" : "1px solid #dee3ec"
                  }}
                >
                  {msg.sender === "user" ? (
                    <span>{msg.text}</span>
                  ) : (
                    <div style={styles.markdownWrapper}>
                      <ReactMarkdown>{msg.text}</ReactMarkdown>
                    </div>
                  )}
                </div>
                <span style={styles.timestamp}>{formatTime(msg.time)}</span>
              </div>
            ))}
            {loading && (
              <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-start" }}>
                <div style={{ ...styles.message, backgroundColor: "#ffffff", border: "1px solid #dee3ec", color: "#5c6478" }}>
                  Thinking…
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          <form onSubmit={sendMessage} style={styles.form}>
            <input
              ref={inputRef}
              type="text"
              autoComplete="off"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about flights, itineraries, or sights..."
              style={styles.input}
            />
            <button type="submit" disabled={loading} style={styles.button}>
              Send
            </button>
          </form>
        </div>
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
    padding: "20px",
    boxSizing: "border-box"
  },
  card: {
    width: "100%",
    maxWidth: "1200px",
    height: "100%",
    backgroundColor: "#eef1f6",
    borderRadius: "16px",
    boxShadow: "0 20px 60px rgba(0,0,0,0.35)",
    display: "flex",
    overflow: "hidden"
  },
  sidebar: {
    flex: "0 0 280px",
    backgroundColor: "#1b2340",
    color: "#ffffff",
    display: "flex",
    flexDirection: "column",
    padding: "22px 16px",
    boxSizing: "border-box",
    overflow: "hidden"
  },
  sidebarBrandRow: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    padding: "0 6px",
    marginBottom: "20px"
  },
  sidebarBrandMark: {
    width: "24px",
    height: "24px",
    flexShrink: 0
  },
  sidebarWordmark: {
    fontFamily: "'Manrope', sans-serif",
    fontWeight: 700,
    fontSize: "14.5px",
    color: "#ffffff"
  },
  newConvoButton: {
    padding: "11px 14px",
    borderRadius: "10px",
    border: "1px solid #e8672b",
    backgroundColor: "#e8672b",
    color: "#ffffff",
    cursor: "pointer",
    fontFamily: "'Manrope', sans-serif",
    fontSize: "13.5px",
    fontWeight: 700,
    marginBottom: "18px"
  },
  tabRow: {
    display: "flex",
    gap: "4px",
    marginBottom: "10px",
    padding: "3px",
    backgroundColor: "#151b34",
    borderRadius: "10px"
  },
  tabButton: {
    flex: 1,
    padding: "8px 10px",
    borderRadius: "8px",
    border: "none",
    backgroundColor: "transparent",
    color: "#9aa1bd",
    cursor: "pointer",
    fontFamily: "'Work Sans', sans-serif",
    fontSize: "12.5px",
    fontWeight: 600
  },
  tabButtonActive: {
    flex: 1,
    padding: "8px 10px",
    borderRadius: "8px",
    border: "none",
    backgroundColor: "#2a325a",
    color: "#ffffff",
    cursor: "pointer",
    fontFamily: "'Work Sans', sans-serif",
    fontSize: "12.5px",
    fontWeight: 600
  },
  listScroll: {
    flex: 1,
    overflowY: "auto",
    display: "flex",
    flexDirection: "column",
    gap: "8px",
    paddingRight: "2px"
  },
  sidebarHint: {
    fontFamily: "'Work Sans', sans-serif",
    fontSize: "12.5px",
    color: "#8991b8",
    padding: "10px 6px",
    lineHeight: 1.5
  },
  historyItem: {
    textAlign: "left",
    width: "100%",
    padding: "10px 12px",
    borderRadius: "10px",
    border: "1px solid transparent",
    backgroundColor: "transparent",
    color: "#e4e6f2",
    cursor: "pointer"
  },
  historyItemActive: {
    backgroundColor: "#2a325a",
    border: "1px solid #3a4272"
  },
  historyPreview: {
    fontFamily: "'Work Sans', sans-serif",
    fontSize: "13px",
    fontWeight: 500,
    marginBottom: "4px",
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap"
  },
  historyMeta: {
    fontFamily: "'IBM Plex Mono', monospace",
    fontSize: "10.5px",
    color: "#8991b8"
  },
  memoryItem: {
    padding: "10px 12px",
    borderRadius: "10px",
    backgroundColor: "#232a4d"
  },
  memoryText: {
    fontFamily: "'Work Sans', sans-serif",
    fontSize: "12.5px",
    lineHeight: 1.5,
    color: "#e4e6f2",
    marginBottom: "6px"
  },
  sidebarFooter: {
    marginTop: "14px",
    paddingTop: "14px",
    borderTop: "1px solid #2a325a",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: "8px"
  },
  accountLine: {
    fontFamily: "'Work Sans', sans-serif",
    fontSize: "12px",
    color: "#c3c8dc",
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap"
  },
  sessionIdLine: {
    fontFamily: "monospace",
    fontSize: "11px",
    color: "#7a82a6",
    overflow: "hidden",
    textOverflow: "ellipsis",
    whiteSpace: "nowrap",
    cursor: "pointer",
    marginTop: "2px"
  },
  tokenMapToggle: {
    marginTop: "10px",
    width: "100%",
    background: "none",
    border: "1px solid #2a325a",
    borderRadius: "6px",
    color: "#c3c8dc",
    fontFamily: "'Work Sans', sans-serif",
    fontSize: "11px",
    padding: "6px 8px",
    cursor: "pointer",
    textAlign: "left"
  },
  tokenMapPanel: {
    marginTop: "8px",
    maxHeight: "160px",
    overflowY: "auto",
    display: "flex",
    flexDirection: "column",
    gap: "4px"
  },
  tokenMapRow: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    fontFamily: "monospace",
    fontSize: "10px",
    color: "#c3c8dc",
    overflowWrap: "anywhere"
  },
  tokenMapToken: {
    color: "#e4986b"
  },
  tokenMapValue: {
    color: "#8fd19e"
  },
  tokenMapEmpty: {
    fontFamily: "'Work Sans', sans-serif",
    fontSize: "11px",
    color: "#7a82a6"
  },
  mainColumn: {
    flex: 1,
    minWidth: 0,
    display: "flex",
    flexDirection: "column"
  },
  header: {
    padding: "16px 24px",
    borderBottom: "1px solid #dee3ec",
    backgroundColor: "#ffffff",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between"
  },
  brandRow: {
    display: "flex",
    alignItems: "center",
    gap: "14px"
  },
  collapseToggle: {
    width: "32px",
    height: "32px",
    borderRadius: "8px",
    border: "1px solid #dee3ec",
    backgroundColor: "#ffffff",
    color: "#5c6478",
    cursor: "pointer",
    fontSize: "14px"
  },
  title: {
    margin: 0,
    fontFamily: "'Manrope', sans-serif",
    fontWeight: 800,
    fontSize: "17px",
    color: "#171b2e"
  },
  pillButtonQuiet: {
    padding: "8px 14px",
    borderRadius: "999px",
    border: "1px solid #3a4272",
    backgroundColor: "transparent",
    color: "#e4e6f2",
    cursor: "pointer",
    fontFamily: "'Manrope', sans-serif",
    fontSize: "12.5px",
    fontWeight: 700,
    flexShrink: 0
  },
  chatBox: {
    flex: 1,
    overflowY: "auto",
    padding: "20px 24px",
    display: "flex",
    flexDirection: "column",
    gap: "14px"
  },
  agentTag: {
    fontFamily: "'IBM Plex Mono', monospace",
    fontSize: "10.5px",
    fontWeight: 600,
    letterSpacing: "0.04em",
    textTransform: "uppercase",
    color: "#b8501f",
    backgroundColor: "#fde9dd",
    padding: "3px 9px",
    borderRadius: "999px",
    marginBottom: "6px"
  },
  message: {
    maxWidth: "85%",
    padding: "14px 18px",
    borderRadius: "14px",
    fontSize: "15px",
    lineHeight: "1.6",
    fontFamily: "'Work Sans', sans-serif"
  },
  markdownWrapper: {
    wordBreak: "break-word"
  },
  timestamp: {
    fontFamily: "'IBM Plex Mono', monospace",
    fontSize: "10.5px",
    color: "#8991a6",
    marginTop: "4px",
    padding: "0 4px"
  },
  form: {
    display: "flex",
    gap: "12px",
    padding: "16px 24px",
    backgroundColor: "#ffffff",
    borderTop: "1px solid #dee3ec"
  },
  input: {
    flex: 1,
    padding: "13px 18px",
    borderRadius: "999px",
    border: "1px solid #dee3ec",
    fontSize: "15px",
    fontFamily: "'Work Sans', sans-serif",
    outline: "none",
    backgroundColor: "#fbfbfc",
    color: "#171b2e"
  },
  button: {
    padding: "13px 26px",
    borderRadius: "999px",
    border: "none",
    backgroundColor: "#e8672b",
    color: "#ffffff",
    cursor: "pointer",
    fontFamily: "'Manrope', sans-serif",
    fontSize: "15px",
    fontWeight: 700
  }
};
