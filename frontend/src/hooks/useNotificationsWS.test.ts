import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import { useAuthStore } from "../store/auth";

// ── QueryClient wrapper ───────────────────────────────────────────────────────

function makeWrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: qc }, children);
}

// ── WebSocket mock ────────────────────────────────────────────────────────────

class MockWebSocket {
  static instances: MockWebSocket[] = [];
  url: string;
  onopen: (() => void) | null = null;
  onmessage: ((e: { data: string }) => void) | null = null;
  onclose: ((e: { wasClean: boolean }) => void) | null = null;
  onerror: (() => void) | null = null;
  readyState = 0; // CONNECTING

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
  }

  close() { this.readyState = 3; } // CLOSED

  simulateOpen()  { this.readyState = 1; this.onopen?.(); }
  simulateClose(wasClean = false) { this.readyState = 3; this.onclose?.({ wasClean }); }
  simulateMessage(data: string) { this.onmessage?.({ data }); }
}

beforeEach(() => {
  MockWebSocket.instances = [];
  vi.stubGlobal("WebSocket", MockWebSocket);
  useAuthStore.setState({ accessToken: null, isAuthenticated: false, user: null, refreshToken: null });
});

afterEach(() => {
  vi.unstubAllGlobals();
});

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("useNotificationsWS", () => {
  it("does not open WebSocket when unauthenticated", async () => {
    const { useNotificationsWS } = await import("./useNotificationsWS");
    renderHook(() => useNotificationsWS(), { wrapper: makeWrapper() });
    expect(MockWebSocket.instances).toHaveLength(0);
  });

  it("opens WebSocket when token is set", async () => {
    const { useNotificationsWS } = await import("./useNotificationsWS");
    act(() => { useAuthStore.setState({ accessToken: "tok-abc", isAuthenticated: true }); });
    renderHook(() => useNotificationsWS(), { wrapper: makeWrapper() });
    expect(MockWebSocket.instances).toHaveLength(1);
    expect(MockWebSocket.instances[0].url).toContain("tok-abc");
  });

  it("closes connection on unmount", async () => {
    const { useNotificationsWS } = await import("./useNotificationsWS");
    act(() => { useAuthStore.setState({ accessToken: "tok-abc", isAuthenticated: true }); });
    const { unmount } = renderHook(() => useNotificationsWS(), { wrapper: makeWrapper() });
    const ws = MockWebSocket.instances[0];
    const closeSpy = vi.spyOn(ws, "close");
    unmount();
    expect(closeSpy).toHaveBeenCalled();
  });

  it("WebSocket URL contains the access token", async () => {
    const { useNotificationsWS } = await import("./useNotificationsWS");
    act(() => { useAuthStore.setState({ accessToken: "my-token-xyz", isAuthenticated: true }); });
    renderHook(() => useNotificationsWS(), { wrapper: makeWrapper() });
    expect(MockWebSocket.instances[0].url).toMatch(/token=my-token-xyz/);
  });
});
