import {
  ResponsiveContainer, ComposedChart, Bar, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
} from "recharts";
import { useTimeseries } from "../../hooks/useAnalytics";
import styles from "./Chart.module.css";

const fmt = (n: number) =>
  n >= 1_000_000 ? `${(n / 1_000_000).toFixed(1)}M` : n >= 1_000 ? `${(n / 1_000).toFixed(0)}k` : String(n);

export default function SpendRevenueChart() {
  const { data = [], isLoading } = useTimeseries();

  if (isLoading) return <div className={styles.skeleton} />;

  return (
    <div className={styles.card}>
      <h3 className={styles.title}>Расходы vs Доход</h3>
      <ResponsiveContainer width="100%" height={280}>
        <ComposedChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
          <XAxis
            dataKey="date"
            tickFormatter={(v: string) => v.slice(5)}
            tick={{ fill: "var(--text-muted)", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tickFormatter={fmt}
            tick={{ fill: "var(--text-muted)", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 8 }}
            labelStyle={{ color: "var(--text-muted)" }}
            formatter={(v: number, name: string) => [fmt(v), name === "spend" ? "Расходы" : "Доход"]}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} formatter={(v) => v === "spend" ? "Расходы" : "Доход"} />
          <Bar dataKey="spend" fill="rgba(108,99,255,0.4)" name="spend" radius={[3, 3, 0, 0]} />
          <Bar dataKey="revenue" fill="rgba(34,197,94,0.4)" name="revenue" radius={[3, 3, 0, 0]} />
          <Line dataKey="roas" stroke="var(--yellow)" dot={false} strokeWidth={2} name="ROAS" yAxisId={0} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
