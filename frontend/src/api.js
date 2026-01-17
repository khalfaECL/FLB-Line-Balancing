const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

function getToken() {
  return localStorage.getItem("mte_token");
}

function setToken(token) {
  localStorage.setItem("mte_token", token);
}

function clearToken() {
  localStorage.removeItem("mte_token");
}

function authHeaders() {
  const token = getToken();
  if (!token) {
    return {};
  }
  return { Authorization: `Bearer ${token}` };
}

async function parseResponse(response) {
  const contentType = response.headers.get("content-type") || "";
  let data;

  if (contentType.includes("application/json")) {
    data = await response.json();
  } else {
    data = await response.text();
  }

  if (!response.ok) {
    const message = data?.detail || data || `Request failed (${response.status})`;
    throw new Error(message);
  }

  return data;
}

async function registerUser(email, password) {
  const response = await fetch(`${API_URL}/api/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  });
  return parseResponse(response);
}

async function verifyEmail(token) {
  const response = await fetch(
    `${API_URL}/api/auth/verify?token=${encodeURIComponent(token)}`
  );
  return parseResponse(response);
}

async function resendVerification(email) {
  const response = await fetch(`${API_URL}/api/auth/resend-verification`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email })
  });
  return parseResponse(response);
}

async function requestPasswordReset(email) {
  const response = await fetch(`${API_URL}/api/auth/forgot-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email })
  });
  return parseResponse(response);
}

async function resetPassword(token, password) {
  const response = await fetch(`${API_URL}/api/auth/reset-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token, password })
  });
  return parseResponse(response);
}

async function loginClient(email, password) {
  const response = await fetch(`${API_URL}/api/auth/login-client`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  });
  const data = await parseResponse(response);
  if (data?.access_token) {
    setToken(data.access_token);
  }
  return data;
}

async function loginAdmin(email, password) {
  const response = await fetch(`${API_URL}/api/auth/login-admin`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  });
  const data = await parseResponse(response);
  if (data?.access_token) {
    setToken(data.access_token);
  }
  return data;
}

async function getMe() {
  const response = await fetch(`${API_URL}/api/auth/me`, {
    headers: authHeaders()
  });
  return parseResponse(response);
}

async function listJobs() {
  const response = await fetch(`${API_URL}/api/jobs`, {
    headers: authHeaders()
  });
  return parseResponse(response);
}

async function deleteJob(jobId) {
  const response = await fetch(`${API_URL}/api/jobs/${jobId}`, {
    method: "DELETE",
    headers: authHeaders()
  });
  return parseResponse(response);
}

async function createJob(file, method) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("method", method);

  const response = await fetch(`${API_URL}/api/jobs`, {
    method: "POST",
    headers: authHeaders(),
    body: formData
  });
  return parseResponse(response);
}

async function listAdminUsers() {
  const response = await fetch(`${API_URL}/api/admin/users`, {
    headers: authHeaders()
  });
  return parseResponse(response);
}

async function listAdminJobs() {
  const response = await fetch(`${API_URL}/api/admin/jobs`, {
    headers: authHeaders()
  });
  return parseResponse(response);
}

async function adminRetryJob(jobId) {
  const response = await fetch(`${API_URL}/api/admin/jobs/${jobId}/retry`, {
    method: "POST",
    headers: authHeaders()
  });
  return parseResponse(response);
}

async function adminResendJob(jobId) {
  const response = await fetch(`${API_URL}/api/admin/jobs/${jobId}/resend`, {
    method: "POST",
    headers: authHeaders()
  });
  return parseResponse(response);
}

async function adminDeleteJob(jobId) {
  const response = await fetch(`${API_URL}/api/admin/jobs/${jobId}`, {
    method: "DELETE",
    headers: authHeaders()
  });
  return parseResponse(response);
}

async function adminDeleteUser(userId) {
  const response = await fetch(`${API_URL}/api/admin/users/${userId}`, {
    method: "DELETE",
    headers: authHeaders()
  });
  return parseResponse(response);
}

async function downloadReport(jobId) {
  const response = await fetch(`${API_URL}/api/jobs/${jobId}/report`, {
    headers: authHeaders()
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || "Unable to download report");
  }

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `report_${jobId}.pdf`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

export {
  API_URL,
  adminDeleteJob,
  adminDeleteUser,
  adminResendJob,
  adminRetryJob,
  authHeaders,
  clearToken,
  createJob,
  deleteJob,
  downloadReport,
  getMe,
  getToken,
  loginAdmin,
  loginClient,
  listAdminJobs,
  listAdminUsers,
  listJobs,
  registerUser,
  requestPasswordReset,
  resendVerification,
  resetPassword,
  setToken,
  verifyEmail
};
