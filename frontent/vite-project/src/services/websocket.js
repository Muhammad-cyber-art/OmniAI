/**
 * OmniLab AI - Resilient WebSocket Client
 * 
 * Features:
 * - Automatic valid JWT access token resolution (calls getValidAccessToken from api.js)
 * - Exponential backoff reconnection
 * - Heartbeat ping / pong keepalive
 * - Event-based subscription pattern (on, off, emit)
 * - Message queueing when connection is in CONNECTING state
 */

import { WS_BASE_URL, getValidAccessToken } from "../config/api";

export class OmniWebSocketClient {
  constructor(endpointPath, options = {}) {
    this.endpointPath = endpointPath.startsWith("/") ? endpointPath : `/${endpointPath}`;
    this.options = {
      autoReconnect: true,
      maxReconnectAttempts: 10,
      baseReconnectDelayMs: 1000,
      maxReconnectDelayMs: 15000,
      heartbeatIntervalMs: 25000,
      ...options,
    };

    this.ws = null;
    this.reconnectAttempts = 0;
    this.reconnectTimeout = null;
    this.heartbeatInterval = null;
    this.isExplicitlyClosed = false;
    this.messageQueue = [];
    this.listeners = new Map(); // type -> Set<callback>

    this.connectionState = "DISCONNECTED"; // DISCONNECTED, CONNECTING, CONNECTED, RECONNECTING
  }

  /**
   * Connect to WebSocket server with fresh JWT token.
   */
  async connect() {
    this.isExplicitlyClosed = false;
    this.setState("CONNECTING");

    try {
      const token = await getValidAccessToken();
      const wsUrl = new URL(`${WS_BASE_URL}${this.endpointPath}`);
      if (token) {
        wsUrl.searchParams.set("token", token);
      }

      this.ws = new WebSocket(wsUrl.toString());

      this.ws.onopen = (event) => {
        this.reconnectAttempts = 0;
        this.setState("CONNECTED");
        this.startHeartbeat();
        this.flushMessageQueue();
        this.emit("open", event);
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.emit("message", data);
          if (data.type) {
            this.emit(data.type, data);
          }
        } catch {
          this.emit("message", event.data);
        }
      };

      this.ws.onerror = (error) => {
        this.emit("error", error);
      };

      this.ws.onclose = (event) => {
        this.stopHeartbeat();
        this.emit("close", event);

        // 4001: Unauthorized, 4003: Forbidden - do not retry on auth/permission failures
        if (event.code === 4001 || event.code === 4003) {
          this.setState("DISCONNECTED");
          this.emit("auth_error", { code: event.code, reason: event.reason });
          return;
        }

        if (!this.isExplicitlyClosed && this.options.autoReconnect) {
          this.scheduleReconnect();
        } else {
          this.setState("DISCONNECTED");
        }
      };
    } catch (err) {
      this.emit("error", err);
      if (!this.isExplicitlyClosed && this.options.autoReconnect) {
        this.scheduleReconnect();
      } else {
        this.setState("DISCONNECTED");
      }
    }
  }

  scheduleReconnect() {
    if (this.reconnectAttempts >= this.options.maxReconnectAttempts) {
      this.setState("DISCONNECTED");
      this.emit("reconnect_failed");
      return;
    }

    this.setState("RECONNECTING");
    this.reconnectAttempts++;

    const delay = Math.min(
      this.options.baseReconnectDelayMs * Math.pow(1.5, this.reconnectAttempts - 1),
      this.options.maxReconnectDelayMs
    );

    this.reconnectTimeout = setTimeout(() => {
      this.connect();
    }, delay);
  }

  startHeartbeat() {
    this.stopHeartbeat();
    this.heartbeatInterval = setInterval(() => {
      if (this.isConnected()) {
        this.send({ type: "ping", timestamp: Date.now() });
      }
    }, this.options.heartbeatIntervalMs);
  }

  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  isConnected() {
    return this.ws && this.ws.readyState === WebSocket.OPEN;
  }

  send(data) {
    const payload = typeof data === "string" ? data : JSON.stringify(data);

    if (this.isConnected()) {
      this.ws.send(payload);
    } else {
      // Queue message until connection is established
      this.messageQueue.push(payload);
    }
  }

  flushMessageQueue() {
    while (this.messageQueue.length > 0 && this.isConnected()) {
      const payload = this.messageQueue.shift();
      this.ws.send(payload);
    }
  }

  disconnect() {
    this.isExplicitlyClosed = true;
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    this.stopHeartbeat();
    if (this.ws) {
      this.ws.close(1000, "Normal Closure");
      this.ws = null;
    }
    this.setState("DISCONNECTED");
  }

  on(eventType, callback) {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, new Set());
    }
    this.listeners.get(eventType).add(callback);
    return () => this.off(eventType, callback);
  }

  off(eventType, callback) {
    const set = this.listeners.get(eventType);
    if (set) {
      set.delete(callback);
      if (set.size === 0) {
        this.listeners.delete(eventType);
      }
    }
  }

  emit(eventType, data) {
    const set = this.listeners.get(eventType);
    if (set) {
      for (const cb of set) {
        try {
          cb(data);
        } catch (err) {
          console.error(`Error in WebSocket listener [${eventType}]:`, err);
        }
      }
    }
  }

  setState(newState) {
    this.connectionState = newState;
    this.emit("state_change", newState);
  }
}
