import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";
import { useClickToOrderDistribution } from "../../hooks/useAnalytics";
import styles from "../dashboard/Chart.module.css";

interface Props { campaignId: string; }

export default function ClickToOrderHistogram({ campaignId }: Props) {
  const { data = [], isLoading } = useClickToOrderDistribution(campaignId);

  if (isLoading) return <div className={styles.skeleton} />;

  return (
    <div className={styles.card}>
      <h3 className={styles.title}>Время от клика до заказа</h3>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
          <XAxis
            dataKey="bucket_label"
            tick={{ fill: "var(--text-muted)", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tickFormatter={(v: number) => `${v}%`}
            tick={{ fill: "var(--text-muted)", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 8 }}
            formatter={(v: number) => [`${v.toFixed(1)}%`, "Доля заказов"]}
          />
          <Bar dataKey="pct" fill="var(--accent)" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
