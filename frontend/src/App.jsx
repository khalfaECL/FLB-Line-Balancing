import React, { useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

import heroOne from "./assets/prod1.jpg";
import heroTwo from "./assets/prod2.jpg";
import {
  adminDeleteJob,
  adminDeleteUser,
  adminResendJob,
  adminRetryJob,
  clearToken,
  createJob,
  deleteJob,
  downloadReport,
  getMe,
  loginAdmin,
  loginClient,
  listAdminJobs,
  listAdminUsers,
  listJobs,
  registerUser,
  requestPasswordReset,
  resendVerification,
  resetPassword,
  verifyEmail
} from "./api";

const sampleStations = [
  { name: "S1", load: 42 },
  { name: "S2", load: 36 },
  { name: "S3", load: 44 },
  { name: "S4", load: 31 },
  { name: "S5", load: 39 }
];

const sampleTrend = [
  { name: "W1", efficiency: 68 },
  { name: "W2", efficiency: 74 },
  { name: "W3", efficiency: 79 },
  { name: "W4", efficiency: 86 },
  { name: "W5", efficiency: 92 }
];

const sampleMix = [
  { name: "MTE", value: 48 },
  { name: "SPT", value: 32 },
  { name: "RPW", value: 20 }
];

const sampleKpis = [
  { label: "Cycle time", value: "52s", meta: "Target 60s" },
  { label: "Line efficiency", value: "91%", meta: "+12% vs baseline" },
  { label: "Idle ratio", value: "6%", meta: "Stable output" },
  { label: "Stations", value: "5", meta: "Balanced workload" }
];

const pieColors = ["#e85d3f", "#1f7a8c", "#f2a40b"];

const METHODS = ["ALL", "MTE", "SPT", "RPW"];
const MAX_CLIENT_JOBS = 10;
const PASSWORD_RULES = [
  { key: "length", label: "8+ characters" },
  { key: "lower", label: "1 lowercase letter" },
  { key: "upper", label: "1 uppercase letter" },
  { key: "symbol", label: "1 symbol" }
];

function formatDate(value) {
  if (!value) {
    return "-";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return String(value);
  }
  return date.toLocaleString();
}

function getPasswordChecks(password) {
  const value = password || "";
  return {
    length: value.length >= 8,
    lower: /[a-z]/.test(value),
    upper: /[A-Z]/.test(value),
    symbol: /[^A-Za-z0-9]/.test(value)
  };
}

function isStrongPassword(password) {
  const checks = getPasswordChecks(password);
  return Object.values(checks).every(Boolean);
}

function PasswordMeter({ password }) {
  const checks = getPasswordChecks(password);
  const score = Object.values(checks).filter(Boolean).length;
  const percent = Math.round((score / PASSWORD_RULES.length) * 100);

  return (
    <div className="password-meter">
      <div className="meter-bar">
        <div className="meter-fill" style={{ width: `${percent}%` }} />
      </div>
      <div className="meter-label">Strength: {score}/4</div>
      <ul className="password-reqs">
        {PASSWORD_RULES.map((rule) => (
          <li key={rule.key} className={checks[rule.key] ? "met" : ""}>
            {rule.label}
          </li>
        ))}
      </ul>
    </div>
  );
}

function App() {
  const [activeView, setActiveView] = useState("home");
  const [pendingScroll, setPendingScroll] = useState("");
  const [status, setStatus] = useState("");
  const [user, setUser] = useState(null);
  const [clientMode, setClientMode] = useState("login");
  const [clientEmail, setClientEmail] = useState("");
  const [clientPassword, setClientPassword] = useState("");
  const [forgotEmail, setForgotEmail] = useState("");
  const [resetToken, setResetToken] = useState("");
  const [resetPasswordValue, setResetPasswordValue] = useState("");
  const [resetPasswordConfirm, setResetPasswordConfirm] = useState("");
  const [adminEmail, setAdminEmail] = useState("");
  const [adminPassword, setAdminPassword] = useState("");
  const [method, setMethod] = useState("ALL");
  const [file, setFile] = useState(null);
  const [fileKey, setFileKey] = useState(0);
  const [jobs, setJobs] = useState([]);
  const [adminUsers, setAdminUsers] = useState([]);
  const [adminJobs, setAdminJobs] = useState([]);
  const [authLoading, setAuthLoading] = useState(false);
  const [jobsLoading, setJobsLoading] = useState(false);
  const [adminLoading, setAdminLoading] = useState(false);

  const isClient = user?.role === "client";
  const isAdmin = user?.role === "admin";
  const isVerifiedClient = isClient && user?.email_verified;

  const userEmailById = useMemo(() => {
    return new Map((adminUsers || []).map((entry) => [entry.id, entry.email]));
  }, [adminUsers]);
  const hasJobCapacity = jobs.length < MAX_CLIENT_JOBS;

  const notify = (message) => {
    if (!message) {
      return;
    }
    setStatus(message);
  };

  const scrollToId = (id) => {
    const element = document.getElementById(id);
    if (!element) {
      return;
    }
    element.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const loadJobs = async () => {
    setJobsLoading(true);
    try {
      const data = await listJobs();
      setJobs(Array.isArray(data) ? data : []);
    } catch (error) {
      notify(error.message);
    } finally {
      setJobsLoading(false);
    }
  };

  const loadAdminData = async () => {
    setAdminLoading(true);
    try {
      const [users, jobsList] = await Promise.all([
        listAdminUsers(),
        listAdminJobs()
      ]);
      setAdminUsers(Array.isArray(users) ? users : []);
      setAdminJobs(Array.isArray(jobsList) ? jobsList : []);
    } catch (error) {
      notify(error.message);
    } finally {
      setAdminLoading(false);
    }
  };

  const handleLogout = () => {
    clearToken();
    setUser(null);
    setJobs([]);
    setAdminJobs([]);
    setAdminUsers([]);
    notify("Signed out");
  };

  const handleClientAuth = async (event) => {
    event.preventDefault();
    if (!clientEmail || !clientPassword) {
      notify("Enter email and password");
      return;
    }
    if (clientMode === "register" && !isStrongPassword(clientPassword)) {
      notify("Password must be 8+ with upper, lower, and symbol.");
      return;
    }

    setAuthLoading(true);
    try {
      if (clientMode === "register") {
        await registerUser(clientEmail, clientPassword);
        await loginClient(clientEmail, clientPassword);
        notify("Account created");
      } else {
        await loginClient(clientEmail, clientPassword);
        notify("Signed in");
      }

      const me = await getMe();
      setUser(me);
      if (me?.role === "client" && me?.email_verified) {
        await loadJobs();
      }
    } catch (error) {
      notify(error.message);
    } finally {
      setAuthLoading(false);
    }
  };

  const handleAdminAuth = async (event) => {
    event.preventDefault();
    if (!adminEmail || !adminPassword) {
      notify("Enter email and password");
      return;
    }

    setAuthLoading(true);
    try {
      await loginAdmin(adminEmail, adminPassword);
      const me = await getMe();
      setUser(me);
      if (me?.role === "admin") {
        await loadAdminData();
        notify("Admin session ready");
      }
    } catch (error) {
      notify(error.message);
    } finally {
      setAuthLoading(false);
    }
  };

  const handleResendVerification = async () => {
    if (!clientEmail) {
      notify("Enter your email first");
      return;
    }
    setAuthLoading(true);
    try {
      await resendVerification(clientEmail);
      notify("Verification email sent");
    } catch (error) {
      notify(error.message);
    } finally {
      setAuthLoading(false);
    }
  };

  const handleForgotPassword = async (event) => {
    event.preventDefault();
    const email = forgotEmail || clientEmail;
    if (!email) {
      notify("Enter your email");
      return;
    }
    setAuthLoading(true);
    try {
      await requestPasswordReset(email);
      notify("If the account exists, a reset link was sent.");
      setClientMode("login");
    } catch (error) {
      notify(error.message);
    } finally {
      setAuthLoading(false);
    }
  };

  const handleResetPassword = async (event) => {
    event.preventDefault();
    if (!resetToken) {
      notify("Missing reset token");
      return;
    }
    if (!resetPasswordValue || !resetPasswordConfirm) {
      notify("Enter your new password twice");
      return;
    }
    if (resetPasswordValue !== resetPasswordConfirm) {
      notify("Passwords do not match");
      return;
    }
    if (!isStrongPassword(resetPasswordValue)) {
      notify("Password must be 8+ with upper, lower, and symbol.");
      return;
    }
    setAuthLoading(true);
    try {
      await resetPassword(resetToken, resetPasswordValue);
      notify("Password updated. You can sign in now.");
      setClientMode("login");
      setResetToken("");
      setResetPasswordValue("");
      setResetPasswordConfirm("");
      window.history.replaceState({}, document.title, window.location.pathname);
    } catch (error) {
      notify(error.message);
    } finally {
      setAuthLoading(false);
    }
  };

  const handleUpload = async (event) => {
    event.preventDefault();
    if (!file) {
      notify("Select a file to upload");
      return;
    }
    if (!isClient) {
      notify("Client access required");
      return;
    }
    if (!user?.email_verified) {
      notify("Verify your email before running jobs");
      return;
    }

    setJobsLoading(true);
    try {
      await createJob(file, method);
      setFile(null);
      setFileKey((value) => value + 1);
      notify("Run queued");
      await loadJobs();
    } catch (error) {
      notify(error.message);
    } finally {
      setJobsLoading(false);
    }
  };

  const handleDownload = async (jobId) => {
    try {
      await downloadReport(jobId);
    } catch (error) {
      notify(error.message);
    }
  };

  const handleClientDelete = async (jobId) => {
    const confirmed = window.confirm("Delete this run and its files?");
    if (!confirmed) {
      return;
    }
    try {
      await deleteJob(jobId);
      notify("Run deleted");
      await loadJobs();
    } catch (error) {
      notify(error.message);
    }
  };

  const handleAdminRetry = async (jobId) => {
    try {
      await adminRetryJob(jobId);
      notify("Job queued for retry");
      await loadAdminData();
    } catch (error) {
      notify(error.message);
    }
  };

  const handleAdminResend = async (jobId) => {
    try {
      await adminResendJob(jobId);
      notify("Report sent");
      await loadAdminData();
    } catch (error) {
      notify(error.message);
    }
  };

  const handleAdminDelete = async (jobId) => {
    const confirmed = window.confirm("Delete this job?");
    if (!confirmed) {
      return;
    }
    try {
      await adminDeleteJob(jobId);
      notify("Job deleted");
      await loadAdminData();
    } catch (error) {
      notify(error.message);
    }
  };

  const handleAdminDeleteUser = async (userId) => {
    const confirmed = window.confirm("Delete this client and all their jobs?");
    if (!confirmed) {
      return;
    }
    try {
      await adminDeleteUser(userId);
      notify("Client deleted");
      await loadAdminData();
    } catch (error) {
      notify(error.message);
    }
  };

  const handleStartRun = () => {
    setActiveView("client");
    setPendingScroll("client-upload");
  };

  const handleViewSample = () => {
    setActiveView("home");
    setPendingScroll("home-sample");
  };

  useEffect(() => {
    let active = true;
    const init = async () => {
      try {
        const me = await getMe();
        if (!active) {
          return;
        }
        setUser(me);
        if (me?.role === "client" && me?.email_verified) {
          await loadJobs();
        }
        if (me?.role === "admin") {
          await loadAdminData();
        }
      } catch (error) {
        clearToken();
      }
    };
    init();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const verifyToken = params.get("verify");
    const resetTokenParam = params.get("reset");

    if (verifyToken) {
      setActiveView("client");
      verifyEmail(verifyToken)
        .then(() => notify("Email verified. You can sign in."))
        .catch((error) => notify(error.message));
    }

    if (resetTokenParam) {
      setActiveView("client");
      setClientMode("reset");
      setResetToken(resetTokenParam);
    }

    if (verifyToken) {
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, []);

  useEffect(() => {
    if (!status) {
      return;
    }
    const timer = setTimeout(() => setStatus(""), 4200);
    return () => clearTimeout(timer);
  }, [status]);

  useEffect(() => {
    if (!pendingScroll) {
      return;
    }
    const handle = window.requestAnimationFrame(() => {
      scrollToId(pendingScroll);
      setPendingScroll("");
    });
    return () => window.cancelAnimationFrame(handle);
  }, [pendingScroll, activeView]);

  useEffect(() => {
    if (activeView !== "home") {
      return;
    }
    const elements = document.querySelectorAll(".reveal");
    if (!elements.length) {
      return;
    }
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
          }
        });
      },
      { threshold: 0.2 }
    );
    elements.forEach((element) => observer.observe(element));
    return () => observer.disconnect();
  }, [activeView]);

  useEffect(() => {
    if (activeView === "client" && isVerifiedClient) {
      loadJobs();
    }
    if (activeView === "admin" && isAdmin) {
      loadAdminData();
    }
  }, [activeView, isClient, isAdmin]);

  return (
    <div className="app">
      <nav className="nav">
        <div className="brand">
          <div className="brand-mark">MTE</div>
          <div>
            <div className="brand-title">Line Balancing Studio</div>
            <div className="brand-sub">Production intelligence workspace</div>
          </div>
        </div>
        <div className="segmented">
          <button
            type="button"
            className={activeView === "home" ? "active" : ""}
            onClick={() => setActiveView("home")}
          >
            Home
          </button>
          <button
            type="button"
            className={activeView === "client" ? "active" : ""}
            onClick={() => setActiveView("client")}
          >
            Client
          </button>
          <button
            type="button"
            className={activeView === "admin" ? "active" : ""}
            onClick={() => setActiveView("admin")}
          >
            Admin
          </button>
        </div>
        <div className="auth-chip">
          <span>{user ? `${user.email} (${user.role})` : "Guest"}</span>
          {user ? (
            <button type="button" onClick={handleLogout}>
              Sign out
            </button>
          ) : null}
        </div>
      </nav>

      {activeView === "home" && (
        <div className="home">
          <section className="hero home-section reveal" id="home-hero">
            <div className="hero-text">
              <div className="home-eyebrow">Production intelligence</div>
              <h1>Balance every line with data you can defend in a meeting.</h1>
              <p>
                Compare MTE, SPT, and RPW in a single run, then deliver clear
                KPIs to operations, finance, and engineering with a polished
                report and audit-ready traceability.
              </p>
              <ul className="hero-list">
                <li>Automated PDF reports with station assignments.</li>
                <li>Real-time queue tracking across teams.</li>
                <li>Client-ready dashboards for each scenario.</li>
              </ul>
              <div className="hero-actions">
                <button className="primary" type="button" onClick={handleStartRun}>
                  Start a balancing run
                </button>
                <button className="ghost" type="button" onClick={handleViewSample}>
                  View sample dashboard
                </button>
              </div>
              <div className="home-stats">
                <div className="stat-card">
                  <div className="stat-label">Avg efficiency</div>
                  <div className="stat-value">+18%</div>
                  <div className="stat-meta">Pilot factory results</div>
                </div>
                <div className="stat-card">
                  <div className="stat-label">Decision speed</div>
                  <div className="stat-value">2.3x</div>
                  <div className="stat-meta">From upload to report</div>
                </div>
                <div className="stat-card">
                  <div className="stat-label">Scenarios</div>
                  <div className="stat-value">12</div>
                  <div className="stat-meta">Saved per client</div>
                </div>
              </div>
            </div>
            <div className="image-stack">
              <img className="stack-image primary" src={heroOne} alt="Factory floor" />
              <img className="stack-image secondary" src={heroTwo} alt="Analytics desk" />
              <div className="image-badge">
                <strong>Live operations view</strong>
                <span>Queue + dashboard timeline</span>
              </div>
            </div>
          </section>

          <section className="home-section reveal" id="home-features">
            <div className="section-head">
              <div>
                <h2>Built for production leaders.</h2>
                <p>
                  Replace spreadsheets with a guided workflow that turns raw
                  routing files into action-ready insights in minutes.
                </p>
              </div>
            </div>
            <div className="feature-grid">
              <div className="feature-card">
                <span className="feature-tag">Decision engine</span>
                <h3>Compare methods instantly</h3>
                <p>
                  Run MTE, SPT, or RPW side-by-side to justify the best line
                  configuration with data.
                </p>
              </div>
              <div className="feature-card">
                <span className="feature-tag">Client experience</span>
                <h3>Dedicated client workspaces</h3>
                <p>
                  Give each client a secure space with their own runs, reports,
                  and KPIs.
                </p>
              </div>
              <div className="feature-card">
                <span className="feature-tag">Operational clarity</span>
                <h3>Dashboard ready summaries</h3>
                <p>
                  Export polished reports and keep stakeholders aligned on the
                  same metrics.
                </p>
              </div>
              <div className="feature-card">
                <span className="feature-tag">Secure delivery</span>
                <h3>Email results in one click</h3>
                <p>
                  Trigger SMTP reports from the admin space with status tracking
                  for every job.
                </p>
              </div>
            </div>
          </section>

          <section className="home-section reveal" id="home-sample">
            <div className="section-head">
              <div>
                <h2>Sample dashboard</h2>
                <p>Preview the KPIs and charts clients see after each run.</p>
              </div>
              <button className="ghost" type="button" onClick={handleStartRun}>
                Run your data
              </button>
            </div>
            <div className="kpi-grid">
              {sampleKpis.map((kpi) => (
                <div className="kpi-card" key={kpi.label}>
                  <div className="kpi-label">{kpi.label}</div>
                  <div className="kpi-value">{kpi.value}</div>
                  <div className="kpi-meta">{kpi.meta}</div>
                </div>
              ))}
            </div>
            <div className="chart-grid">
              <div className="chart-card">
                <div className="chart-title">Station workload</div>
                <div className="chart-box">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={sampleStations}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="load" fill="#1f7a8c" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
              <div className="chart-card">
                <div className="chart-title">Efficiency trend</div>
                <div className="chart-box">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={sampleTrend}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <Tooltip />
                      <Line type="monotone" dataKey="efficiency" stroke="#e85d3f" strokeWidth={3} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
              <div className="chart-card">
                <div className="chart-title">Method mix</div>
                <div className="chart-box">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={sampleMix}
                        dataKey="value"
                        nameKey="name"
                        outerRadius={80}
                        innerRadius={40}
                      >
                        {sampleMix.map((entry, index) => (
                          <Cell key={entry.name} fill={pieColors[index % pieColors.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          </section>

          <section className="home-section reveal" id="home-flow">
            <div className="section-head">
              <div>
                <h2>Three-step workflow</h2>
                <p>From spreadsheet to stakeholder-ready results in minutes.</p>
              </div>
            </div>
            <div className="timeline">
              <div className="timeline-step">
                <div className="timeline-index">1</div>
                <div className="timeline-body">
                  <h4>Upload routing file</h4>
                  <p>Select your Excel file and choose the balancing method.</p>
                </div>
              </div>
              <div className="timeline-step">
                <div className="timeline-index">2</div>
                <div className="timeline-body">
                  <h4>Run the optimizer</h4>
                  <p>Let the engine compute station assignments and KPIs.</p>
                </div>
              </div>
              <div className="timeline-step">
                <div className="timeline-index">3</div>
                <div className="timeline-body">
                  <h4>Share the report</h4>
                  <p>Download PDF outputs or send them to clients by email.</p>
                </div>
              </div>
            </div>
          </section>

          <section className="home-section reveal" id="home-cta">
            <div className="cta-card">
              <h2>Ready to balance with confidence?</h2>
              <p>
                Use the client space for live runs or showcase the dashboard to
                new stakeholders right now.
              </p>
              <div className="hero-actions">
                <button className="primary" type="button" onClick={handleStartRun}>
                  Start a balancing run
                </button>
                <button className="ghost" type="button" onClick={handleViewSample}>
                  View sample dashboard
                </button>
              </div>
            </div>
          </section>
        </div>
      )}
      {activeView === "client" && (
        <div className="panel">
          <div className="panel-grid">
            <div className="panel-card">
              <div className="panel-title">Client access</div>
              <p className="panel-text">
                Sign in with a client account or register a new one. Only
                registered clients can launch balancing runs.
              </p>
              {isClient ? (
                <>
                  <p className="panel-text">Signed in as {user?.email}.</p>
                  {user?.email_verified ? (
                    <p className="panel-text">Email verified. Client tools unlocked.</p>
                  ) : (
                    <div className="notice">
                      <span>Verify your email to run balancing jobs.</span>
                      <button
                        className="link"
                        type="button"
                        onClick={handleResendVerification}
                        disabled={authLoading}
                      >
                        Resend verification email
                      </button>
                    </div>
                  )}
                </>
              ) : (
                <>
                  {user && !isClient ? (
                    <p className="panel-text">
                      You are signed in as an admin. Sign out to use client
                      space.
                    </p>
                  ) : null}
                  {(clientMode === "login" || clientMode === "register") && (
                    <form className="auth-form" onSubmit={handleClientAuth}>
                      <div className="auth-toggle">
                        <button
                          type="button"
                          className={clientMode === "login" ? "active" : ""}
                          onClick={() => setClientMode("login")}
                        >
                          Sign in
                        </button>
                        <button
                          type="button"
                          className={clientMode === "register" ? "active" : ""}
                          onClick={() => setClientMode("register")}
                        >
                          Register
                        </button>
                      </div>
                      <label>
                        Email
                        <input
                          type="email"
                          value={clientEmail}
                          onChange={(event) => setClientEmail(event.target.value)}
                          placeholder="client@example.com"
                          required
                        />
                      </label>
                      <label>
                        Password
                        <input
                          type="password"
                          value={clientPassword}
                          onChange={(event) => setClientPassword(event.target.value)}
                          placeholder="********"
                          required
                        />
                      </label>
                      {clientMode === "register" ? (
                        <PasswordMeter password={clientPassword} />
                      ) : null}
                      <button className="primary" type="submit" disabled={authLoading}>
                        {clientMode === "register" ? "Create account" : "Sign in"}
                      </button>
                      <div className="auth-links">
                        {clientMode === "login" ? (
                          <>
                            <button
                              className="link"
                              type="button"
                              onClick={() => {
                                setForgotEmail(clientEmail);
                                setClientMode("forgot");
                              }}
                            >
                              Forgot password?
                            </button>
                            <button
                              className="link"
                              type="button"
                              onClick={handleResendVerification}
                              disabled={!clientEmail || authLoading}
                            >
                              Resend verification
                            </button>
                          </>
                        ) : (
                          <button
                            className="link"
                            type="button"
                            onClick={() => setClientMode("login")}
                          >
                            Back to sign in
                          </button>
                        )}
                      </div>
                    </form>
                  )}
                  {clientMode === "forgot" && (
                    <form className="auth-form" onSubmit={handleForgotPassword}>
                      <label>
                        Email
                        <input
                          type="email"
                          value={forgotEmail}
                          onChange={(event) => setForgotEmail(event.target.value)}
                          placeholder="client@example.com"
                          required
                        />
                      </label>
                      <button className="primary" type="submit" disabled={authLoading}>
                        Send reset link
                      </button>
                      <div className="auth-links">
                        <button
                          className="link"
                          type="button"
                          onClick={() => setClientMode("login")}
                        >
                          Back to sign in
                        </button>
                      </div>
                    </form>
                  )}
                  {clientMode === "reset" && (
                    <form className="auth-form" onSubmit={handleResetPassword}>
                      <label>
                        New password
                        <input
                          type="password"
                          value={resetPasswordValue}
                          onChange={(event) => setResetPasswordValue(event.target.value)}
                          placeholder="********"
                          required
                        />
                      </label>
                      <label>
                        Confirm password
                        <input
                          type="password"
                          value={resetPasswordConfirm}
                          onChange={(event) => setResetPasswordConfirm(event.target.value)}
                          placeholder="********"
                          required
                        />
                      </label>
                      <PasswordMeter password={resetPasswordValue} />
                      <button className="primary" type="submit" disabled={authLoading}>
                        Update password
                      </button>
                    </form>
                  )}
                </>
              )}
            </div>

            <div className="panel-card" id="client-upload">
              <div className="panel-title">Start a balancing run</div>
              <p className="panel-text">
                Upload a routing spreadsheet to generate KPIs and reports.
              </p>
              {!isClient ? (
                <p className="panel-text">Client access required to submit jobs.</p>
              ) : !isVerifiedClient ? (
                <p className="panel-text">Verify your email to unlock submissions.</p>
              ) : !hasJobCapacity ? (
                <p className="panel-text">
                  Storage limit reached ({MAX_CLIENT_JOBS}). Delete an old run to
                  upload more.
                </p>
              ) : null}
              <form className="upload-form" onSubmit={handleUpload}>
                <label>
                  Method
                  <select
                    value={method}
                    onChange={(event) => setMethod(event.target.value)}
                    disabled={!isClient || !isVerifiedClient || !hasJobCapacity}
                  >
                    {METHODS.map((item) => (
                      <option key={item} value={item}>
                        {item}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Excel file
                  <input
                    key={fileKey}
                    type="file"
                    accept=".xlsx,.xls"
                    onChange={(event) => setFile(event.target.files?.[0] || null)}
                    disabled={!isClient || !isVerifiedClient || !hasJobCapacity}
                  />
                </label>
                <button
                  className="primary"
                  type="submit"
                  disabled={!isVerifiedClient || !hasJobCapacity || jobsLoading || !file}
                >
                  Run balancing
                </button>
              </form>
            </div>

            <div className="panel-card wide">
              <div className="panel-title">Recent runs</div>
              <p className="panel-text">
                Track progress, download PDF reports, and review KPI history.
              </p>
              <div className="panel-actions">
                <span className="panel-meta">
                  Storage: {jobs.length}/{MAX_CLIENT_JOBS}
                </span>
                <button
                  className="ghost"
                  type="button"
                  onClick={loadJobs}
                  disabled={!isVerifiedClient || jobsLoading}
                >
                  Refresh
                </button>
              </div>
              <div className="table">
                <div className="table-row table-head cols-6">
                  <span>File</span>
                  <span>Method</span>
                  <span>Status</span>
                  <span>Updated</span>
                  <span>Report</span>
                  <span>Actions</span>
                </div>
                {jobsLoading ? (
                  <div className="table-row empty">Loading jobs...</div>
                ) : jobs.length ? (
                  jobs.map((job) => {
                    const statusLabel = job.status || "unknown";
                    const statusClass = statusLabel.toLowerCase();
                    return (
                      <div className="table-row cols-6" key={job.job_id}>
                        <span>{job.filename || "-"}</span>
                        <span>{job.method || "-"}</span>
                        <span>
                          <span className={`pill ${statusClass}`}>{statusLabel}</span>
                        </span>
                        <span>{formatDate(job.updated_at)}</span>
                        <span>
                          <button
                            className="link"
                            type="button"
                            onClick={() => handleDownload(job.job_id)}
                            disabled={job.status !== "completed"}
                          >
                            Download
                          </button>
                        </span>
                        <span className="table-actions">
                          <button
                            className="link danger"
                            type="button"
                            onClick={() => handleClientDelete(job.job_id)}
                            disabled={jobsLoading}
                          >
                            Delete
                          </button>
                        </span>
                      </div>
                    );
                  })
                ) : (
                  <div className="table-row empty">No runs yet.</div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
      {activeView === "admin" && (
        <div className="panel">
          <div className="panel-grid">
            <div className="panel-card">
              <div className="panel-title">Admin access</div>
              <p className="panel-text">
                Sign in with an admin account to review every client run and
                resend reports.
              </p>
              {isAdmin ? (
                <p className="panel-text">Signed in as {user?.email}.</p>
              ) : (
                <>
                  {user && !isAdmin ? (
                    <p className="panel-text">
                      You are signed in as a client. Sign out to use admin space.
                    </p>
                  ) : null}
                  <form className="auth-form" onSubmit={handleAdminAuth}>
                    <label>
                      Admin email
                      <input
                        type="email"
                        value={adminEmail}
                        onChange={(event) => setAdminEmail(event.target.value)}
                        placeholder="admin@example.com"
                        required
                      />
                    </label>
                    <label>
                      Password
                      <input
                        type="password"
                        value={adminPassword}
                        onChange={(event) => setAdminPassword(event.target.value)}
                        placeholder="********"
                        required
                      />
                    </label>
                    <button className="primary" type="submit" disabled={authLoading}>
                      Sign in as admin
                    </button>
                  </form>
                </>
              )}
            </div>

            <div className="panel-card">
              <div className="panel-title">Registered users</div>
              <p className="panel-text">All active accounts in the platform.</p>
              <div className="panel-actions">
                <button
                  className="ghost"
                  type="button"
                  onClick={loadAdminData}
                  disabled={!isAdmin || adminLoading}
                >
                  Refresh
                </button>
              </div>
              <div className="table">
                <div className="table-row table-head cols-4">
                  <span>Email</span>
                  <span>Role</span>
                  <span>Verified</span>
                  <span>Actions</span>
                </div>
                {!isAdmin ? (
                  <div className="table-row empty">Admin access required.</div>
                ) : adminLoading ? (
                  <div className="table-row empty">Loading users...</div>
                ) : adminUsers.length ? (
                  adminUsers.map((entry) => (
                    <div className="table-row cols-4" key={entry.id}>
                      <span>{entry.email}</span>
                      <span>{entry.role}</span>
                      <span>{entry.email_verified ? "Yes" : "No"}</span>
                      <span className="table-actions">
                        <button
                          className="link danger"
                          type="button"
                          onClick={() => handleAdminDeleteUser(entry.id)}
                          disabled={entry.role === "admin" || adminLoading}
                        >
                          Delete
                        </button>
                      </span>
                    </div>
                  ))
                ) : (
                  <div className="table-row empty">No users found.</div>
                )}
              </div>
            </div>

            <div className="panel-card wide">
              <div className="panel-title">Jobs monitor</div>
              <p className="panel-text">
                Manage processing status, resend emails, or retry a run.
              </p>
              <div className="panel-actions">
                <button
                  className="ghost"
                  type="button"
                  onClick={loadAdminData}
                  disabled={!isAdmin || adminLoading}
                >
                  Refresh
                </button>
              </div>
              <div className="table">
                <div className="table-row table-head cols-6">
                  <span>Client</span>
                  <span>File</span>
                  <span>Method</span>
                  <span>Status</span>
                  <span>Email</span>
                  <span>Actions</span>
                </div>
                {!isAdmin ? (
                  <div className="table-row empty">Admin access required.</div>
                ) : adminLoading ? (
                  <div className="table-row empty">Loading jobs...</div>
                ) : adminJobs.length ? (
                  adminJobs.map((job) => {
                    const statusLabel = job.status || "unknown";
                    const statusClass = statusLabel.toLowerCase();
                    const emailClass = (job.email_status || "skipped").toLowerCase();
                    const emailLabel =
                      job.email_status ||
                      (job.status === "completed" ? "pending" : "n/a");
                    return (
                      <div className="table-row cols-6" key={job.job_id}>
                        <span>{userEmailById.get(job.user_id) || job.user_id || "-"}</span>
                        <span>{job.filename || "-"}</span>
                        <span>{job.method || "-"}</span>
                        <span>
                          <span
                            className={`pill ${statusClass}`}
                            title={job.error || ""}
                          >
                            {statusLabel}
                          </span>
                        </span>
                        <span>
                          <span
                            className={`pill email ${emailClass}`}
                            title={job.email_error || ""}
                          >
                            {emailLabel}
                          </span>
                        </span>
                        <span className="table-actions">
                          <button
                            className="link"
                            type="button"
                            onClick={() => handleAdminRetry(job.job_id)}
                            disabled={job.status === "processing" || adminLoading}
                          >
                            Retry
                          </button>
                          <button
                            className="link"
                            type="button"
                            onClick={() => handleAdminResend(job.job_id)}
                            disabled={job.status !== "completed" || adminLoading}
                          >
                            Send
                          </button>
                          <button
                            className="link"
                            type="button"
                            onClick={() => handleDownload(job.job_id)}
                            disabled={job.status !== "completed"}
                          >
                            PDF
                          </button>
                          <button
                            className="link danger"
                            type="button"
                            onClick={() => handleAdminDelete(job.job_id)}
                            disabled={adminLoading}
                          >
                            Delete
                          </button>
                        </span>
                      </div>
                    );
                  })
                ) : (
                  <div className="table-row empty">No jobs found.</div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {status ? <div className="status">{status}</div> : null}
    </div>
  );
}

export default App;
