import styles from "./MetricCard.module.css";
import { clsx } from "clsx";

interface Props {
  label: string;
  value: string | number;
  delta?: number;
  suffix?: string;
  highlight?: boolean;
}

export default function MetricCard({ label, value, delta, suffix, highlight }: Props) {
  return (
    <div className={clsx(styles.card, highlight && styles.highlight)}>
      <span className={styles.label}>{label}</span>
      <span className={styles.value}>
        {value}
        {suffix && <span className={styles.suffix}>{suffix}</span>}
      </span>
      {delta !== undefined && (
        <span className={clsx(styles.delta, delta >= 0 ? styles.positive : styles.negative)}>
          {delta >= 0 ? "+" : ""}{delta.toFixed(1)}%
        </span>
      )}
    </div>
  );
}
