/**
 * OmniLab AI - React Hook for Live Simulation WebSockets
 * 
 * Provides real-time connection state, message history, live AI feedback,
 * score updates, and actions (sendTurn, requestHint, abandonSession).
 * 
 * Usage in component:
 * const { isConnected, isEvaluating, sessionState, latestFeedback, sendTurn } = useSimulationSocket(sessionId);
 */

import { useState, useEffect, useRef, useCallback } from "react";
import { OmniWebSocketClient } from "../services/websocket";

export function useSimulationSocket(sessionId) {
  const [connectionState, setConnectionState] = useState("DISCONNECTED");
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [sessionState, setSessionState] = useState(null);
  const [messages, setMessages] = useState([]);
  const [latestFeedback, setLatestFeedback] = useState(null);
  const [error, setError] = useState(null);

  const clientRef = useRef(null);

  useEffect(() => {
    if (!sessionId) return;

    const client = new OmniWebSocketClient(`/simulations/${sessionId}/`);
    clientRef.current = client;

    // Track connection state
    const unbindState = client.on("state_change", (state) => {
      setConnectionState(state);
      if (state === "CONNECTED") setError(null);
    });

    // Connection established initial metadata
    const unbindEstablished = client.on("connection_established", (data) => {
      setSessionState(data);
      setMessages((prev) => [...prev, { type: "system", text: "Connected to simulation room." }]);
    });

    // AI is evaluating (typing indicator)
    const unbindEvaluating = client.on("evaluating", (data) => {
      setIsEvaluating(true);
      setMessages((prev) => [...prev, { type: "evaluating", text: data.message }]);
    });

    // Turn completed with evaluation
    const unbindTurnResult = client.on("turn_result", (payload) => {
      setIsEvaluating(false);
      setLatestFeedback(payload.data);
      setSessionState((prev) => ({
        ...prev,
        current_step: payload.data.current_step,
        total_score: payload.data.total_score,
        steps_taken: payload.data.steps_taken,
        status: payload.data.is_final_step ? "COMPLETED" : prev?.status,
      }));
      setMessages((prev) => [...prev, { type: "turn_result", data: payload.data }]);
    });

    // Hint received
    const unbindHint = client.on("hint_result", (payload) => {
      setMessages((prev) => [...prev, { type: "hint", data: payload.data }]);
    });

    // Session abandoned
    const unbindAbandoned = client.on("session_abandoned", (data) => {
      setSessionState((prev) => ({ ...prev, status: "ABANDONED" }));
      setMessages((prev) => [...prev, { type: "system", text: data.message }]);
    });

    // Error messages from server
    const unbindError = client.on("error", (err) => {
      setIsEvaluating(false);
      setError(err?.message || "WebSocket communication error.");
    });

    // Auth error (unauthorized or session mismatch)
    const unbindAuthError = client.on("auth_error", (err) => {
      setError(`Authentication failed (Code ${err.code}). Please log in.`);
    });

    // Initiate connection
    client.connect();

    return () => {
      unbindState();
      unbindEstablished();
      unbindEvaluating();
      unbindTurnResult();
      unbindHint();
      unbindAbandoned();
      unbindError();
      unbindAuthError();
      client.disconnect();
      clientRef.current = null;
    };
  }, [sessionId]);

  const sendTurn = useCallback((studentInput) => {
    if (!clientRef.current) return;
    setError(null);
    clientRef.current.send({
      type: "student_turn",
      input: studentInput,
    });
  }, []);

  const requestHint = useCallback(() => {
    if (!clientRef.current) return;
    clientRef.current.send({
      type: "request_hint",
    });
  }, []);

  const abandonSession = useCallback(() => {
    if (!clientRef.current) return;
    clientRef.current.send({
      type: "abandon",
    });
  }, []);

  return {
    connectionState,
    isConnected: connectionState === "CONNECTED",
    isEvaluating,
    sessionState,
    messages,
    latestFeedback,
    error,
    sendTurn,
    requestHint,
    abandonSession,
  };
}
