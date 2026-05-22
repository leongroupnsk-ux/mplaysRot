import React, { useState } from "react";
import type { CanvasWidget } from "../../../api/canvas";

interface Props {
  widget: CanvasWidget;
}

/** Generates placeholder data for the chart (in production, fetch from API). */
function generateData(metric: string, period: string): number[] {
  // Seeded random based on metric+period for consistency
  const seed = (metric + period).split("").reduce((acc, c) => acc + c.charCodeAt(0), 0);
  const days = period === "7d" ? 7 : period === "30d" ? 30 : 14;
  const base = metric === "romi" ? 120 : metric === "stock" ? 50 : 80;
  const pts: number[] = [];
  for (let i = 0; i < days; i++) {
    const pseudo = Math.sin(seed + i * 0.7) * 30 + Math.cos(seed * 0.3 + i) * 20;
    pts.push(Math.max(0, base + pseudo));
  }
  return pts;
}

function BarChart({ data, color }: { data: number[]; color: string }) {
  const max = Math.max(...data, 1);
  return (
    <div style={{ display: "flex", alignItems: "flex-end", gap: 3, height: 80, width: "100%" }}>
      {data.map((v, i) => (
        <div
          key={i}
          style={{
            flex: 1,
            height: `${(v / max) * 100}%`,
            background: color,
            borderRadius: "2px 2px 0 0",
            minWidth: 4,
            opacity: 0.7 + (i / data.length) * 0.3,
          }}
        />
      ))}
    </div>
  );
}

function LineChart({ data, color }: { data: number[]; color: string }) {
  const max = Math.max(...data, 1);
  const min = Math.min(...data);
  const h = 80;
  const w = 280;
  const scaleY = (v: number) => h - ((v - min) / (max - min + 1)) * h * 0.9 - h * 0.05;
  const pts = data
    .map((v, i) => `${i === 0 ? "M" : "L"} ${(i / (data.length - 1)) * w} ${scaleY(v)}`)
    .join(" ");

  const areaPath = pts + ` L ${w} ${h} L 0 ${h} Z`;

  return (
    <svg width="100%" height={h} viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none">
      <defs>
        <linearGradient id={`grad-${color.replace("#", "")}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.3" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={areaPath} fill={`url(#grad-${color.replace("#", "")})`} />
      <path d={pts} fill="none" stroke={color} strokeWidth="2.5" strokeLinejoin="round" />
    </svg>
  );
}

const METRICS: Record<string, { label: string; color: string; unit: string }> = {
  sales:   { label: "Продажи",       color: "#6366f1", unit: "шт." },
  romi:    { label: "ROMI",          color: "#22c55e", unit: "%" },
  stock:   { label: "Остатки",       color: "#f59e0b", unit: "шт." },
  returns: { label: "Возвраты",      color: "#ef4444", unit: "шт." },
  spend:   { label: "Расход",        color: "#8b5cf6", unit: "₽" },
};

const PERIODS = ["7d", "14d", "30d"];

export default function MiniChartWidget({ widget }: Props) {
  const { data } = widget;
  const [metric, setMetric] = useState<string>(data.metric || "sales");
  const [period, setPeriod] = useState<string>(data.period || "7d");
  const [chartType, setChartType] = useState<"bar" | "line">("bar");

  const meta = METRICS[metric] || METRICS.sales;
  const chartData = generateData(metric, period);
  const total = chartData.reduce((a, b) => a + b, 0);
  const avg = (total / chartData.length).toFixed(1);
  const lastValue = chartData[chartData.length - 1].toFixed(1);
  const prevValue = chartData[chartData.length - 2];
  const delta = ((chartData[chartData.length - 1] - prevValue) / (prevValue || 1)) * 100;

  return (
    <div style={{ height: "100%", display: "flex", flexDirection: "column", padding: "10px 12px", gap: 8 }}>
      {/* Controls */}
      <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
        <select
          value={metric}
          onChange={(e) => setMetric(e.target.value)}
          onMouseDown={(e) => e.stopPropagation()}
          style={selectStyle}
        >
          {Object.entries(METRICS).map(([k, v]) => (
            <option key={k} value={k}>{v.label}</option>
          ))}
        </select>
        <div style={{ display: "flex", gap: 2 }}>
          {PERIODS.map((p) => (
            <button
              key={p}
              onMouseDown={(e) => e.stopPropagation()}
              onClick={() => setPeriod(p)}
              style={{
                padding: "3px 7px",
                borderRadius: 5,
                fontSize: 10,
                border: "none",
                cursor: "pointer",
                fontWeight: 600,
                background: period === p ? meta.color : "#f1f5f9",
                color: period === p ? "#fff" : "#64748b",
              }}
            >
              {p}
            </button>
          ))}
        </div>
        <button
          onMouseDown={(e) => e.stopPropagation()}
          onClick={() => setChartType((t) => (t === "bar" ? "line" : "bar"))}
          style={{ marginLeft: "auto", background: "none", border: "none", cursor: "pointer", fontSize: 14, color: "#94a3b8" }}
          title="Переключить тип графика"
        >
          {chartType === "bar" ? "📉" : "📊"}
        </button>
      </div>

      {/* Summary */}
      <div style={{ display: "flex", alignItems: "baseline", gap: 6 }}>
        <span style={{ fontSize: 22, fontWeight: 800, color: meta.color }}>
          {lastValue}
        </span>
        <span style={{ fontSize: 12, color: "#94a3b8" }}>{meta.unit}</span>
        <span
          style={{
            fontSize: 11,
            fontWeight: 700,
            color: delta >= 0 ? "#22c55e" : "#ef4444",
            marginLeft: 4,
          }}
        >
          {delta >= 0 ? "▲" : "▼"} {Math.abs(delta).toFixed(1)}%
        </span>
      </div>

      {/* Chart */}
      <div style={{ flex: 1, minHeight: 0 }}>
        {chartType === "bar" ? (
          <BarChart data={chartData} color={meta.color} />
        ) : (
          <LineChart data={chartData} color={meta.color} />
        )}
      </div>

      {/* Footer stats */}
      <div style={{ display: "flex", gap: 12, fontSize: 11, color: "#94a3b8" }}>
        <span>Ср: {avg} {meta.unit}</span>
        <span>Всего: {total.toFixed(0)} {meta.unit}</span>
        <span style={{ marginLeft: "auto", fontStyle: "italic" }}>⚡ placeholder</span>
      </div>
    </div>
  );
}

const selectStyle: React.CSSProperties = {
  padding: "3px 6px",
  border: "1px solid #e2e8f0",
  borderRadius: 6,
  fontSize: 11,
  background: "#f8fafc",
  color: "#334155",
  flex: 1,
};
