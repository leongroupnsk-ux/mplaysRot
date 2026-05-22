import { useFilters } from "../../store/filters";
import styles from "./DateRangePicker.module.css";

const PRESETS = [
  { label: "7д", days: 7 },
  { label: "30д", days: 30 },
  { label: "90д", days: 90 },
];

function shift(days: number): string {
  const d = new Date();
  d.setDate(d.getDate() - days);
  return d.toISOString().slice(0, 10);
}

export default function DateRangePicker() {
  const { dateFrom, dateTo, setDateRange } = useFilters();

  const applyPreset = (days: number) => {
    setDateRange(shift(days), new Date().toISOString().slice(0, 10));
  };

  return (
    <div className={styles.root}>
      {PRESETS.map(({ label, days }) => (
        <button
          key={days}
          className={styles.preset}
          onClick={() => applyPreset(days)}
        >
          {label}
        </button>
      ))}
      <input type="date" value={dateFrom} onChange={(e) => setDateRange(e.target.value, dateTo)} />
      <span className={styles.sep}>—</span>
      <input type="date" value={dateTo} onChange={(e) => setDateRange(dateFrom, e.target.value)} />
    </div>
  );
}
