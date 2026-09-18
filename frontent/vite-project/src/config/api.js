/**
 * OmniLab AI - API Configuration & Auto-Refreshing JWT Client
 * 
 * Features:
 * - Dynamic Base URLs for REST (HTTP) and WebSockets (WS)
 * - Thread-safe concurrent Token Refreshing (single in-flight refresh promise)
 * - Preemptive expiration detection (< 30s remaining)
 * - Automatic retry on 401 Unauthorized
 * - Global auth event bus ('auth:unauthorized', 'auth:tokens_updated')
 */

// ─── BASE URLS ───────────────────────────────────────────────────────────────
export const API_BASE_URL =
  import.meta.env?.VITE_API_URL || "http://127.0.0.1:8000/api/v1";

export const WS_BASE_URL =
  import.meta.env?.VITE_WS_URL || "ws://127.0.0.1:8000/ws";

// ─── TOKEN STORAGE ───────────────────────────────────────────────────────────
const ACCESS_TOKEN_KEY = "omnilab_access_token";
const REFRESH_TOKEN_KEY = "omnilab_refresh_token";

export const getAccessToken = () => localStorage.getItem(ACCESS_TOKEN_KEY);
export const getRefreshToken = () => localStorage.getItem(REFRESH_TOKEN_KEY);

export const setTokens = ({ access, refresh }) => {
  if (access) localStorage.setItem(ACCESS_TOKEN_KEY, access);
  if (refresh) localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
  window.dispatchEvent(
    new CustomEvent("auth:tokens_updated", { detail: { access, refresh } })
  );
};

export const clearTokens = () => {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  window.dispatchEvent(new CustomEvent("auth:unauthorized"));
};

/**
 * Decode JWT without third-party libraries.
 */
export const decodeJwt = (token) => {
  if (!token) return null;
  try {
    const base64Url = token.split(".")[1];
    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split("")
        .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
        .join("")
    );
    return JSON.parse(jsonPayload);
  } catch {
    return null;
  }
};

/**
 * Checks if token is expired or expiring within bufferSeconds.
 */
export const isTokenExpired = (token, bufferSeconds = 30) => {
  const decoded = decodeJwt(token);
  if (!decoded || !decoded.exp) return true;
  const nowInSeconds = Math.floor(Date.now() / 1000);
  return decoded.exp - nowInSeconds <= bufferSeconds;
};

// ─── SINGLETON REFRESH PROMISE ───────────────────────────────────────────────
// Prevents duplicate refresh requests when multiple components make requests simultaneously
let refreshPromise = null;

/**
 * Automatically requests a new access token using the refresh token.
 * If multiple callers invoke this concurrently, they will all share the exact same promise.
 */
export const refreshAccessToken = async () => {
  const refreshToken = getRefreshToken();
  if (!refreshToken) {
    clearTokens();
    throw new Error("No refresh token available. Please log in.");
  }

  // If a refresh is already in-flight, return the existing promise
  if (refreshPromise) {
    return refreshPromise;
  }

  refreshPromise = (async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/token/refresh/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ refresh: refreshToken }),
      });

      if (!response.ok) {
        clearTokens();
        throw new Error("Refresh token expired or revoked. Please log in again.");
      }

      const data = await response.json();
      const newAccessToken = data.access;
      const newRefreshToken = data.refresh || refreshToken; // Some configs rotate refresh tokens

      setTokens({ access: newAccessToken, refresh: newRefreshToken });
      return newAccessToken;
    } catch (err) {
      clearTokens();
      throw err;
    } finally {
      refreshPromise = null;
    }
  })();

  return refreshPromise;
};

/**
 * Returns a valid access token.
 * If expired or expiring soon, refreshes automatically.
 */
export const getValidAccessToken = async () => {
  const token = getAccessToken();
  if (!token) return null;

  if (isTokenExpired(token)) {
    return await refreshAccessToken();
  }
  return token;
};

// ─── HTTP CLIENT WITH AUTO-RETRY ──────────────────────────────────────────────
/**
 * Wrapper around window.fetch with automatic JWT header injection and 401 token refreshing.
 *
 * @param {string} endpoint - e.g. "/simulations/cases/" or full URL
 * @param {RequestInit} options - fetch options
 */
export const apiFetch = async (endpoint, options = {}) => {
  const url = endpoint.startsWith("http") ? endpoint : `${API_BASE_URL}${endpoint.startsWith("/") ? "" : "/"}${endpoint}`;
  const headers = new Headers(options.headers || {});

  // Preemptive refresh if token exists and is expiring
  let token = getAccessToken();
  if (token && isTokenExpired(token)) {
    try {
      token = await refreshAccessToken();
    } catch {
      token = null;
    }
  }

  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  let response = await fetch(url, { ...options, headers });

  // If response is 401 Unauthorized, attempt refresh once and retry request
  if (response.status === 401 && getRefreshToken()) {
    try {
      const newToken = await refreshAccessToken();
      headers.set("Authorization", `Bearer ${newToken}`);
      response = await fetch(url, { ...options, headers });
    } catch {
      // Refresh failed, clear and let error propagate
      clearTokens();
    }
  }

  const contentType = response.headers.get("content-type");
  const isJson = contentType && contentType.includes("application/json");
  const data = isJson ? await response.json() : await response.text();

  if (!response.ok) {
    const error = new Error(
      (typeof data === "object" && data?.error?.message) ||
      (typeof data === "object" && data?.detail) ||
      `Request failed with status ${response.status}`
    );
    error.status = response.status;
    error.data = data;
    throw error;
  }

  return data;
};
