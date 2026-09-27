import React, { useState, useRef, useEffect, useCallback } from "react";
import "./App.css";
import { LogoMark } from "./Logo";

// true = show Web/General labels on answers too (handy while testing)
// false = only show the label on PDF answers
const SHOW_ALL_BADGES = false;

/* ---------------- storage helpers ---------------- */
const LS_BASEURL = "paperpilot.baseUrl";
const LS_SESSIONS = (m) => `paperpilot.sessions.${m}`;

function getStoredBaseUrl() {
 return (
   localStorage.getItem(LS_BASEURL) ||
   import.meta.env.VITE_API_URL ||
   "http://localhost:8000"
 );
}

const LS_THEME = "paperpilot.theme";

function getStoredTheme() {
  const saved = localStorage.getItem(LS_THEME);
  if (saved === "light" || saved === "dark") return saved;
  // first visit: follow the computer's setting
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

function loadSessions(mode) {
  try {
    const raw = localStorage.getItem(LS_SESSIONS(mode));
    const sessions = raw ? JSON.parse(raw) : [];
    // drop "Thinking…" bubbles left over from interrupted requests,
    // and drop chats that are completely empty
    return sessions
      .map((s) => ({
        ...s,
        messages: s.messages.filter((m) => !m.pending),
      }))
      .filter((s) => s.messages.length > 0 || s.documentId);
  } catch {
    return [];
  }
}

function saveSessions(mode, sessions) {
  localStorage.setItem(LS_SESSIONS(mode), JSON.stringify(sessions));
}

function uuid() {
  if (crypto.randomUUID) return crypto.randomUUID();
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

function createSession() {
  return {
    id: uuid(),
    title: "New chat",
    messages: [],
    documentId: null,
    filename: null,
    pages: null,
    chunks: null,
  };
}

/** Ensures a mode's state has a valid activeId, creating a first session if empty. */
function ensureActive(modeState) {
  if (!modeState.sessions.length) {
    const s = createSession();
    return { sessions: [s], activeId: s.id };
  }
  if (!modeState.sessions.find((s) => s.id === modeState.activeId)) {
    return { ...modeState, activeId: modeState.sessions[0].id };
  }
  return modeState;
}

/** Opens a fresh chat, reusing the newest chat only if it is still empty. */
function startFreshChat(modeState) {
  const first = modeState.sessions[0];
  if (first && first.messages.length === 0 && !first.documentId) {
    return { ...modeState, activeId: first.id };
  }
  const s = createSession();
  return { sessions: [s, ...modeState.sessions], activeId: s.id };
}

function sourceMeta(route) {
  if (route === "web") return { label: "🌐 Web", cls: "web" };
  if (route === "pdf") return { label: "📄 PDF", cls: "pdf" };
  return { label: "🧠 General", cls: "general" };
}

async function safeErr(res) {
  try {
    const j = await res.json();
    return j.detail || JSON.stringify(j);
  } catch {
    return res.statusText || `HTTP ${res.status}`;
  }
}

/* ---------------- component ---------------- */
export default function App() {
  const [screen, setScreen] = useState("landing"); // 'landing' | 'workspace'
  const [mode, setMode] = useState("smart"); // 'smart' | 'pdf_only'
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [modes, setModes] = useState(() => ({
    smart: { sessions: loadSessions("smart"), activeId: null },
    pdf_only: { sessions: loadSessions("pdf_only"), activeId: null },
  }));
  const [input, setInput] = useState("");
  const [baseUrl, setBaseUrl] = useState(getStoredBaseUrl());
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [baseUrlDraft, setBaseUrlDraft] = useState("");
  const [uploading, setUploading] = useState(false);
  const [theme, setTheme] = useState(getStoredTheme);

  const fileInputRef = useRef(null);
  const textareaRef = useRef(null);
  const messagesEndRef = useRef(null);

  // Persist both mode buckets whenever they change.
  useEffect(() => {
    saveSessions("smart", modes.smart.sessions);
    saveSessions("pdf_only", modes.pdf_only.sessions);
  }, [modes]);

  // Apply the theme to the whole page and remember it.
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem(LS_THEME, theme);
  }, [theme]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ block: "end" });
  }, [modes, mode]);

  const modeState = modes[mode];
  const sessions = modeState.sessions;
  const activeSession =
    sessions.find((s) => s.id === modeState.activeId) || null;

  /** Updates a specific session (by mode + id), safe to call after an async gap. */
  const updateSessionById = useCallback((modeKey, sessionId, updater) => {
    setModes((prev) => {
      const cur = prev[modeKey];
      const newSessions = cur.sessions.map((s) =>
        s.id === sessionId ? { ...s, ...updater(s) } : s,
      );
      return { ...prev, [modeKey]: { ...cur, sessions: newSessions } };
    });
  }, []);

  function enterMode(m) {
    setModes((prev) => ({ ...prev, [m]: startFreshChat(prev[m]) }));
    setMode(m);
    setScreen("workspace");
  }

  function switchMode(m) {
    if (m === mode) return;
    setModes((prev) => ({ ...prev, [m]: ensureActive(prev[m]) }));
    setMode(m);
  }

  function goHome() {
    setScreen("landing");
  }

  function toggleTheme() {
    setTheme((t) => (t === "dark" ? "light" : "dark"));
  }

  function handleNewChat() {
    setModes((prev) => {
      const cur = prev[mode];
      const s = createSession();
      return {
        ...prev,
        [mode]: { sessions: [s, ...cur.sessions], activeId: s.id },
      };
    });
  }

  function handleSelectSession(id) {
    setModes((prev) => ({ ...prev, [mode]: { ...prev[mode], activeId: id } }));
  }

  function handleDeleteSession(id) {
    setModes((prev) => {
      const cur = prev[mode];
      const remaining = cur.sessions.filter((s) => s.id !== id);
      let next = {
        sessions: remaining,
        activeId:
          cur.activeId === id ? (remaining[0]?.id ?? null) : cur.activeId,
      };
      next = ensureActive(next);
      return { ...prev, [mode]: next };
    });
  }

  function handleAttachClick() {
    fileInputRef.current?.click();
  }

  async function handleFileChange(e) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file || !activeSession) return;
    const modeKey = mode;
    const sessionId = activeSession.id;
    setUploading(true);
    try {
      const url = `${baseUrl}/upload?session_id=${encodeURIComponent(sessionId)}`;
      const fd = new FormData();
      fd.append("file", file);
      const res = await fetch(url, { method: "POST", body: fd });
      if (!res.ok) throw new Error(await safeErr(res));
      const data = await res.json();
      updateSessionById(modeKey, sessionId, (s) => ({
        documentId: data.document_id,
        filename: data.filename,
        pages: data.pages,
        chunks: data.chunks,
        title: s.title === "New chat" ? data.filename || "PDF chat" : s.title,
        // show the upload inside the chat so you can see when it happened
        messages: [
          ...s.messages,
          {
            id: uuid(),
            role: "assistant",
            text: `📄 ${data.filename} uploaded · ${data.pages} pages`,
          },
        ],
      }));
    } catch (err) {
      alert(
        `Upload failed: ${err.message}\n\nCheck the API base URL (⚙ API) and that your FastAPI server is running.`,
      );
    } finally {
      setUploading(false);
    }
  }

  function autoResize() {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 140) + "px";
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendQuestion();
    }
  }

  async function sendQuestion() {
    const text = input.trim();
    if (!text || !activeSession) return;
    if (mode === "pdf_only" && !activeSession.documentId) return;

    const modeKey = mode;
    const sessionId = activeSession.id;
    const userMsg = { id: uuid(), role: "user", text };
    const pendingId = uuid();
    const pendingMsg = {
      id: pendingId,
      role: "assistant",
      text: "Thinking…",
      pending: true,
    };

    updateSessionById(modeKey, sessionId, (s) => ({
      title:
        s.title === "New chat"
          ? text.slice(0, 42) + (text.length > 42 ? "…" : "")
          : s.title,
      messages: [...s.messages, userMsg, pendingMsg],
    }));
    setInput("");
    requestAnimationFrame(autoResize);

    try {
      const params = new URLSearchParams({
        question: text,
        session_id: sessionId,
        mode: modeKey,
      });
      if (activeSession.documentId)
        params.append("document_id", activeSession.documentId);
      const res = await fetch(`${baseUrl}/ask?${params.toString()}`, {
        method: "POST",
      });
      if (!res.ok) throw new Error(await safeErr(res));
      const data = await res.json();

      updateSessionById(modeKey, sessionId, (s) => ({
        messages: s.messages.map((m) =>
          m.id === pendingId
            ? {
                id: pendingId,
                role: "assistant",
                text: data.answer || "(No answer returned.)",
                meta: {
                  answered_using: data.answered_using,
                  sources: data.sources,
                  verified: data.verified,
                },
              }
            : m,
        ),
        documentId: s.documentId || data.document_id || null,
      }));
    } catch (err) {
      updateSessionById(modeKey, sessionId, (s) => ({
        messages: s.messages.map((m) =>
          m.id === pendingId
            ? {
                id: pendingId,
                role: "assistant",
                text: `Could not reach PaperPilot: ${err.message}`,
                error: true,
              }
            : m,
        ),
      }));
    }
  }

  function openSettings() {
    setBaseUrlDraft(baseUrl);
    setSettingsOpen(true);
  }

  function saveSettings() {
    const v = baseUrlDraft.trim().replace(/\/+$/, "");
    if (v) {
      localStorage.setItem(LS_BASEURL, v);
      setBaseUrl(v);
    }
    setSettingsOpen(false);
  }

  const needsDoc =
    mode === "pdf_only" && !(activeSession && activeSession.documentId);

  /* ---------------- render ---------------- */
  return (
    <div className="pp-app">
      {screen === "landing" && (
        <Landing onPick={enterMode} theme={theme} onToggleTheme={toggleTheme} />
      )}

      {screen === "workspace" && (
        <div className="pp-workspace">
          <Sidebar
            mode={mode}
            open={sidebarOpen}
            onSwitchMode={switchMode}
            onGoHome={goHome}
            sessions={sessions}
            activeId={modeState.activeId}
            onSelect={handleSelectSession}
            onDelete={handleDeleteSession}
            onNewChat={handleNewChat}
            baseUrl={baseUrl}
            onOpenSettings={openSettings}
          />

          <main className="main-col">
            <div className="main-header">
              <div className="header-left">
                <button
                  className="sidebar-toggle"
                  onClick={() => setSidebarOpen((v) => !v)}
                  title={sidebarOpen ? "Hide sidebar" : "Show sidebar"}
                  aria-label={sidebarOpen ? "Hide sidebar" : "Show sidebar"}
                >
                  {sidebarOpen ? "◧" : "☰"}
                </button>
                <div className="thread-title">
                  {activeSession ? activeSession.title : "New chat"}
                </div>
              </div>
              <div className="header-right">
                <ThemeToggle theme={theme} onToggle={toggleTheme} />
                <span
                  className={`mode-pill ${mode === "smart" ? "smart" : "pdfonly"}`}
                >
                  {mode === "smart" ? "Smart Study" : "PDF Study"}
                </span>
              </div>
            </div>

            {activeSession?.documentId && (
              <div className="doc-strip">
                <span>
                  📄{" "}
                  <span className="name">
                    {activeSession.filename || "document.pdf"}
                  </span>
                </span>
                <span>
                  {activeSession.pages ? `${activeSession.pages} pages` : ""}
                </span>
                <button onClick={handleAttachClick}>Replace PDF</button>
              </div>
            )}

            <div className="messages">
              {!activeSession || activeSession.messages.length === 0 ? (
                <div className="empty-state">
                  {mode === "pdf_only" ? (
                    <>
                      <div className="icon">▤</div>
                      <h3>Attach a PDF to begin</h3>
                      <p>
                        PDF Study only answers from the document you upload. Use
                        the 📎 button to add one.
                      </p>
                    </>
                  ) : (
                    <>
                      <div className="icon">
                        <LogoMark size={52} />
                      </div>
                      <h3>Ask anything</h3>
                      <p>
                        Attach a PDF if you like, or just start asking —
                        PaperPilot will pull from the web, general knowledge, or
                        your document as needed.
                      </p>
                    </>
                  )}
                </div>
              ) : (
                activeSession.messages.map((m) => (
                  <Message key={m.id} msg={m} />
                ))
              )}
              <div ref={messagesEndRef} />
            </div>

            <div className="composer">
              <div className="composer-inner">
                <button
                  className="attach-btn"
                  onClick={handleAttachClick}
                  title="Attach a PDF"
                  disabled={uploading}
                >
                  {uploading ? "⏳" : "📎"}
                </button>
                <textarea
                  ref={textareaRef}
                  rows={1}
                  placeholder="Ask a question…"
                  value={input}
                  disabled={needsDoc}
                  onChange={(e) => {
                    setInput(e.target.value);
                    autoResize();
                  }}
                  onKeyDown={handleKeyDown}
                />
                <button
                  className="go-btn"
                  onClick={sendQuestion}
                  disabled={needsDoc || !input.trim()}
                >
                  Go
                </button>
              </div>
              <div className="composer-hint">
                {needsDoc
                  ? "Attach a PDF with 📎 before asking in PDF Study."
                  : ""}
              </div>
            </div>
          </main>
        </div>
      )}

      <input
        type="file"
        ref={fileInputRef}
        accept="application/pdf"
        style={{ display: "none" }}
        onChange={handleFileChange}
      />

      {settingsOpen && (
        <div
          className="modal-backdrop"
          onClick={(e) =>
            e.target === e.currentTarget && setSettingsOpen(false)
          }
        >
          <div className="modal">
            <h3>API connection</h3>
            <p>
              Base URL of your FastAPI backend (e.g. where you ran{" "}
              <code>uvicorn</code>).
            </p>
            <input
              type="text"
              value={baseUrlDraft}
              placeholder="http://localhost:8000"
              onChange={(e) => setBaseUrlDraft(e.target.value)}
            />
            <div className="modal-actions">
              <button onClick={() => setSettingsOpen(false)}>Cancel</button>
              <button className="primary" onClick={saveSettings}>
                Save
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/* ---------------- subcomponents ---------------- */

function ThemeToggle({ theme, onToggle, className = "" }) {
  const next = theme === "dark" ? "light" : "dark";
  return (
    <button
      className={`theme-toggle ${className}`}
      onClick={onToggle}
      title={`Switch to ${next} mode`}
      aria-label={`Switch to ${next} mode`}
    >
      {theme === "dark" ? "☀" : "☾"}
    </button>
  );
}

function Landing({ onPick, theme, onToggleTheme }) {
  return (
    <section className="pp-landing">
      <ThemeToggle
        theme={theme}
        onToggle={onToggleTheme}
        className="floating"
      />
      <div className="landing-mark">
        <LogoMark size={38} />
        <div className="wordmark">
          Paper<em>Pilot</em> AI
        </div>
      </div>
      <h1>Study your documents, smarter.</h1>
      <p className="sub">
        Pick how you want to work. Each one keeps its own chats, so switching
        never loses your place.
      </p>
      <div className="mode-picker">
        <button className="mode-card smart" onClick={() => onPick("smart")}>
          <div className="icon">
            <LogoMark size={26} />
          </div>
          <h2>Smart Study</h2>
          <p>
            Ask anything. PaperPilot pulls from your PDF, the web, or general
            knowledge — and tells you which one answered.
          </p>
          <span className="enter">Enter Smart Study →</span>
        </button>
        <button
          className="mode-card pdfonly"
          onClick={() => onPick("pdf_only")}
        >
          <div className="icon">▤</div>
          <h2>PDF Study</h2>
          <p>
            Strictly your document. Upload a PDF and get answers grounded only
            in what's on the page.
          </p>
          <span className="enter">Enter PDF Study →</span>
        </button>
      </div>
    </section>
  );
}

function Sidebar({
  mode,
  open,
  onSwitchMode,
  onGoHome,
  sessions,
  activeId,
  onSelect,
  onDelete,
  onNewChat,
  baseUrl,
  onOpenSettings,
}) {
  return (
    <aside className={`sidebar ${open ? "" : "collapsed"}`}>
      <div className="sidebar-inner">
        <div className="sidebar-top">
          <button className="brand-row" onClick={onGoHome} title="Back to home">
            <LogoMark size={24} />
            <div className="wordmark">PaperPilot</div>
          </button>
          <div className="mode-toggle">
            <button
              className={mode === "smart" ? "active" : ""}
              onClick={() => onSwitchMode("smart")}
            >
              Smart Study
            </button>
            <button
              className={mode === "pdf_only" ? "active" : ""}
              onClick={() => onSwitchMode("pdf_only")}
            >
              PDF Study
            </button>
          </div>
        </div>

        <button className="new-chat-btn" onClick={onNewChat}>
          + New chat
        </button>

        <div className="chat-list">
          {sessions.length === 0 ? (
            <div className="chat-list-empty">
              No chats yet. Start one above.
            </div>
          ) : (
            sessions.map((s) => (
              <div
                key={s.id}
                className={`chat-item ${s.id === activeId ? "active" : ""}`}
                onClick={() => onSelect(s.id)}
              >
                {s.documentId && (
                  <span className="doc-dot" title="PDF attached" />
                )}
                <span className="title">{s.title || "New chat"}</span>
                <button
                  className="del"
                  title="Delete chat"
                  aria-label="Delete chat"
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete(s.id);
                  }}
                >
                  ×
                </button>
              </div>
            ))
          )}
        </div>

        <div className="sidebar-bottom">
          <button className="ghost-btn" onClick={onOpenSettings}>
            ⚙ API
          </button>
          <span style={{ fontSize: 11, color: "var(--ink-faint)" }}>
            {baseUrl.replace(/^https?:\/\//, "")}
          </span>
        </div>
      </div>
    </aside>
  );
}

function Message({ msg }) {
  const cls = `msg ${msg.role}${msg.pending ? " pending" : ""}${msg.error ? " error" : ""}`;
  return (
    <div className={cls}>
      <div className="bubble">{msg.text}</div>
      {msg.role === "assistant" &&
        msg.meta &&
        !msg.pending &&
        !msg.error &&
        (SHOW_ALL_BADGES || msg.meta.answered_using === "pdf") && (
          <div className="badge-row">
            <span
              className={`src-badge ${sourceMeta(msg.meta.answered_using).cls}`}
            >
              {sourceMeta(msg.meta.answered_using).label}
            </span>
            {msg.meta.answered_using === "pdf" &&
              msg.meta.verified !== null &&
              msg.meta.verified !== undefined && (
                <span
                  className={`verified-tag ${msg.meta.verified ? "" : "no"}`}
                >
                  {msg.meta.verified
                    ? "✓ Verified against PDF"
                    : "– Unverified"}
                </span>
              )}
          </div>
        )}
    </div>
  );
}
