import { useState } from "react";
import { exportReport, type ReportType } from "../api/reports";
import { useFilters } from "../store/filters";
import DateRangePicker from "../components/shared/DateRangePicker";
import pageStyles from "./Page.module.css";
import styles from "./ReportsPage.module.css";

interface ExportRecord {
  id: number;
  type: ReportType;
  filename: string;
  rows: number;
  url: string;
  createdAt: string;
}

const REPORT_TYPES: { type: ReportType; label: string; description: string }[] = [
  {
    type: "attribution",
    label: "Атрибуция",
    description: "Все атрибутированные заказы: trax_id, метод, уверенность, сумма",
  },
  {
    type: "overview",
    label: "Сводка по дням",
    description: "Ежедневные показатели: показы, клики, расходы, доход, ROAS",
  },
  {
    type: "campaigns",
    label: "По кампаниям",
    description: "Агрегированные результаты каждой кампании за период",
  },
];

let _idSeq = 0;

export default function ReportsPage() {
  const { dateFrom, dateTo } = useFilters();
  const [records, setRecords] = useState<ExportRecord[]>([]);
  const [loading, setLoading] = useState<ReportType | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleExport = async (type: ReportType) => {
    setLoading(type);
    setError(null);
    try {
      const result = await exportReport({ type, date_from: dateFrom, date_to: dateTo });
      setRecords((prev) => [
        {
          id: ++_idSeq,
          type,
          filename: result.filename,
          rows: result.rows,
          url: result.url,
          createdAt: new Date().toISOString(),
        },
        ...prev,
      ]);
      const a = document.createElement("a");
      a.href = result.url;
      a.download = result.filename;
      a.click();
    } catch {
      setError("Не удалось сформировать отчёт. Попробуйте позже.");
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className={pageStyles.page}>
      <div className={pageStyles.toolbar}>
        <h1 className={pageStyles.heading}>Отчёты</h1>
        <DateRangePicker />
      </div>

      {error && (
        <div className={styles.errorBanner}>{error}</div>
      )}

      {/* Report type cards */}
      <div className={styles.grid}>
        {REPORT_TYPES.map(({ type, label, description }) => (
          <div key={type} className={styles.reportCard}>
            <div className={styles.reportIcon}>{type === "attribution" ? "📊" : type === "overview" ? "📈" : "🗂"}</div>
            <div className={styles.reportInfo}>
              <div className={styles.reportLabel}>{label}</div>
              <div className={styles.reportDesc}>{description}</div>
            </div>
            <button
              className={styles.btnExport}
              onClick={() => handleExport(type)}
              disabled={loading === type}
              type="button"
            >
              {loading === type ? "Генерация…" : "↓ CSV"}
            </button>
          </div>
        ))}
      </div>

      {/* Export history */}
      {records.length > 0 && (
        <div className={styles.historySection}>
          <h2 className={styles.historyTitle}>История экспортов</h2>
          <div className={styles.historyList}>
            {records.map((rec) => (
              <div key={rec.id} className={styles.historyRow}>
                <div className={styles.historyMeta}>
                  <span className={styles.historyName}>{rec.filename}</span>
                  <span className={styles.historyRows}>{rec.rows.toLocaleString("ru")} строк</span>
                </div>
                <span className={styles.historyDate}>
                  {new Date(rec.createdAt).toLocaleString("ru")}
                </span>
                <a
                  href={rec.url}
                  download={rec.filename}
                  className={styles.historyDownload}
                >
                  Скачать
                </a>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
