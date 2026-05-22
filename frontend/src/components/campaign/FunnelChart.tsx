import { useFunnel } from "../../hooks/useAnalytics";
import styles from "./FunnelChart.module.css";

const STEP_LABELS: Record<string, string> = {
  clicks: "Клики",
  favorites: "Избранное",
  cart_adds: "Корзина",
  orders: "Заказы",
};

const STEP_COLORS = ["#6c63ff", "#8b84ff", "#22c55e", "#f59e0b"];

interface Props { campaignId: string; }

export default function FunnelChart({ campaignId }: Props) {
  const { data, isLoading } = useFunnel(campaignId);

  if (isLoading) return <div className={styles.skeleton} />;
  if (!data) return null;

  const maxCount = Math.max(...data.steps.map((s) => s.count), 1);

  return (
    <div className={styles.card}>
      <h3 className={styles.title}>Воронка конверсии</h3>
      <div className={styles.funnel}>
        {data.steps.map((step, i) => {
          const widthPct = (step.count / maxCount) * 100;
          return (
            <div key={step.name} className={styles.stepRow}>
              <span className={styles.stepLabel}>{STEP_LABELS[step.name] ?? step.name}</span>
              <div className={styles.barWrap}>
                <div
                  className={styles.bar}
                  style={{ width: `${widthPct}%`, background: STEP_COLORS[i] }}
                />
              </div>
              <span className={styles.count}>{step.count.toLocaleString("ru")}</span>
              {i > 0 && (
                <span className={styles.cr}>
                  {(step.conversion_rate * 100).toFixed(1)}%
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
