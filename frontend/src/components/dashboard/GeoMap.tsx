import { useState } from "react";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, Cell,
} from "recharts";
import { useGeo } from "../../hooks/useAnalytics";
import styles from "./Chart.module.css";
import geoStyles from "./GeoMap.module.css";

type Metric = "revenue" | "clicks" | "orders" | "conversion_rate";

const METRICS: { key: Metric; label: string; fmt: (v: number) => string }[] = [
  { key: "revenue",         label: "Доход",      fmt: (v) => `${v.toLocaleString("ru")} ₽` },
  { key: "clicks",          label: "Клики",      fmt: (v) => v.toLocaleString("ru") },
  { key: "orders",          label: "Заказы",     fmt: (v) => v.toLocaleString("ru") },
  { key: "conversion_rate", label: "CR",          fmt: (v) => `${(v * 100).toFixed(2)}%` },
];

const COLORS = [
  "rgba(108,99,255,0.85)",
  "rgba(108,99,255,0.70)",
  "rgba(108,99,255,0.56)",
  "rgba(108,99,255,0.44)",
  "rgba(108,99,255,0.34)",
  "rgba(108,99,255,0.26)",
  "rgba(108,99,255,0.20)",
  "rgba(108,99,255,0.16)",
  "rgba(108,99,255,0.13)",
  "rgba(108,99,255,0.10)",
];

function CustomTooltip({ active, payload, metric }: {
  active?: boolean; payload?: { value: number }[]; metric: typeof METRICS[0]
}) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: "var(--bg-card)", border: "1px solid var(--border)",
      borderRadius: 8, padding: "8px 12px", fontSize: 12,
    }}>
      <span style={{ color: "var(--accent)" }}>{metric.fmt(payload[0].value)}</span>
    </div>
  );
}

export default function GeoMap() {
  const { data = [], isLoading } = useGeo();
  const [activeMetric, setActiveMetric] = useState<Metric>("revenue");

  if (isLoading) return <div className={styles.skeleton} style={{ height: 320 }} />;

  const metric = METRICS.find((m) => m.key === activeMetric)!;

  const sorted = [...data]
    .sort((a, b) => (b[activeMetric] as number) - (a[activeMetric] as number))
    .slice(0, 10);

  const max = sorted[0]?.[activeMetric] as number ?? 1;

  return (
    <div className={styles.card}>
      <div className={geoStyles.header}>
        <h3 className={styles.title} style={{ margin: 0 }}>География</h3>
        <div className={geoStyles.tabs}>
          {METRICS.map((m) => (
            <button
              key={m.key}
              className={`${geoStyles.tab} ${activeMetric === m.key ? geoStyles.tabActive : ""}`}
              onClick={() => setActiveMetric(m.key)}
              type="button"
            >
              {m.label}
            </button>
          ))}
        </div>
      </div>

      {data.length === 0 ? (
        <div className={geoStyles.empty}>Нет данных за выбранный период</div>
      ) : (
        <div className={geoStyles.body}>
          {/* Bar chart */}
          <ResponsiveContainer width="100%" height={sorted.length * 36 + 16}>
            <BarChart
              data={sorted}
              layout="vertical"
              margin={{ top: 0, right: 60, left: 0, bottom: 0 }}
              barSize={16}
            >
              <CartesianGrid horizontal={false} strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis
                type="number"
                domain={[0, max]}
                tickFormatter={(v: number) =>
                  activeMetric === "conversion_rate"
                    ? `${(v * 100).toFixed(1)}%`
                    : activeMetric === "revenue"
                    ? v >= 1_000_000
                      ? `${(v / 1_000_000).toFixed(1)}M`
                      : `${(v / 1_000).toFixed(0)}k`
                    : String(v)
                }
                tick={{ fill: "var(--text-muted)", fontSize: 10 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                type="category"
                dataKey="region"
                width={130}
                tick={{ fill: "var(--text)", fontSize: 12 }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip
                content={<CustomTooltip metric={metric} />}
                cursor={{ fill: "rgba(255,255,255,0.03)" }}
              />
              <Bar dataKey={activeMetric} radius={[0, 4, 4, 0]}>
                {sorted.map((_, i) => (
                  <Cell key={i} fill={COLORS[i] ?? COLORS[COLORS.length - 1]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>

          {/* Table summary */}
          <div className={geoStyles.table}>
            {sorted.map((row, i) => (
              <div key={row.region} className={geoStyles.tableRow}>
                <span className={geoStyles.rank}>{i + 1}</span>
                <span className={geoStyles.region}>{row.region}</span>
                <span className={geoStyles.value}>{metric.fmt(row[activeMetric] as number)}</span>
                <div className={geoStyles.bar}>
                  <div
                    className={geoStyles.barFill}
                    style={{ width: `${((row[activeMetric] as number) / max) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
