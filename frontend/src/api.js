const API_BASE = "/api/auth";

async function request(path, { method = "GET", body, token } = {}) {
  const headers = {};
  if (body) headers["Content-Type"] = "application/json";
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || res.statusText);
  }
  return res.json();
}

export const api = {
  register: (data) => request("/register", { method: "POST", body: data }),
  login: (data) => request("/login", { method: "POST", body: data }),
  anonymous: (data) => request("/anonymous", { method: "POST", body: data }),
};