import { Component, type ReactNode } from "react";

interface Props { children: ReactNode; }
interface State { error: Error | null; }

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: { componentStack: string }) {
    console.error("[ErrorBoundary]", error, info.componentStack);
  }

  render() {
    if (this.state.error) {
      return (
        <div style={{
          display: "flex", flexDirection: "column", alignItems: "center",
          justifyContent: "center", height: "100%", gap: 16, padding: 32,
          background: "var(--bg)", color: "var(--text)",
        }}>
          <div style={{ fontSize: 32 }}>⚠️</div>
          <div style={{ fontSize: 18, fontWeight: 700 }}>Ошибка рендеринга</div>
          <pre style={{
            background: "var(--bg-card)", border: "1px solid var(--border)",
            borderRadius: 8, padding: "12px 16px", fontSize: 12,
            color: "#f87171", maxWidth: 600, whiteSpace: "pre-wrap", wordBreak: "break-all",
          }}>
            {this.state.error.message}
          </pre>
          <button
            onClick={() => { this.setState({ error: null }); window.location.href = "/dashboard"; }}
            style={{
              padding: "9px 20px", background: "var(--accent)", color: "#fff",
              borderRadius: 8, fontSize: 14, fontWeight: 600, cursor: "pointer",
            }}
          >
            На главную
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
