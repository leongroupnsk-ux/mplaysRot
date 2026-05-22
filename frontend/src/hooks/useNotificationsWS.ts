import { useEffect, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useAuthStore } from "../store/auth";

const WS_BASE = import.meta.env.VITE_API_URL
  ? import.meta.env.VITE_API_URL.replace(/^http/, "ws").replace(/\/$/, "")
  : `ws://${window.location.host}`;

const RECONNECT_DELAY_MS = 3_000;
const MAX_RECONNECT_ATTEMPTS = 10;

/**
 * Connects to the notifications WebSocket service and invalidates
 * the React Query "notifications" cache whenever a new notification
 * arrives for the current user.
 *
 * Connection lifecycle:
 *  - Opens when the user is authenticated
 *  - Closes and re-opens if the token changes (re-login)
 *  - Reconnects automatically on unexpected close, up to MAX_RECONNECT_ATTEMPTS
 *  - Cleans up on unmount
 */
export function useNotificationsWS() {
  const queryClient = useQueryClient();
  const token = useAuthStore((s) => s.accessToken);
  const wsRef = useRef<WebSocket | null>(null);
  const attemptRef = useRef(0);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!token) {
      _close();
      return;
    }

    attemptRef.current = 0;
    _connect();

    return () => {
      _close();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  function _connect() {
    if (wsRef.current) {
      wsRef.current.onclose = null;
      wsRef.current.close();
    }

    const ws = new WebSocket(`${WS_BASE}/ws?token=${token}`);
    wsRef.current = ws;

    ws.onopen = () => {
      attemptRef.current = 0;
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data as string);
        // Any incoming message means a new notification — refresh the list
        if (msg?.type !== undefined || msg?.id !== undefined) {
          queryClient.invalidateQueries({ queryKey: ["notifications"] });
        }
      } catch {
        // Non-JSON frames (ping frames from server) — ignore
      }
    };

    ws.onclose = (event) => {
      if (event.wasClean) return;
      _scheduleReconnect();
    };

    ws.onerror = () => {
      // onerror always fires before onclose — let onclose handle reconnect
    };
  }

  function _scheduleReconnect() {
    if (attemptRef.current >= MAX_RECONNECT_ATTEMPTS) return;
    attemptRef.current += 1;
    const delay = Math.min(RECONNECT_DELAY_MS * attemptRef.current, 30_000);
    timerRef.current = setTimeout(_connect, delay);
  }

  function _close() {
    if (timerRef.current) clearTimeout(timerRef.current);
    if (wsRef.current) {
      wsRef.current.onclose = null;
      wsRef.current.close();
      wsRef.current = null;
    }
  }
}
