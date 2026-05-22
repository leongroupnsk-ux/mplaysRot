import { useState } from "react";
import DateRangePicker from "../components/shared/DateRangePicker";
import AttributionTable from "../components/campaign/AttributionTable";
import { useFilters } from "../store/filters";
import { exportReport } from "../api/reports";
import styles from "./Page.module.css";

export default function AttributionPage() {
  const { dateFrom, dateTo } = useFilters();
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  const handleExport = async () => {
    setExporting(true);
    setExportError(null);
    try {
      const { url, filename } = await exportReport({
        type: "attribution",
        date_from: dateFrom,
        date_to: dateTo,
      });
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      a.click();
    } catch {
      setExportError("Не удалось сформировать отчёт. Попробуйте позже.");
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className={styles.page}>
      <div className={styles.toolbar}>
        <h1 className={styles.heading}>Атрибуция</h1>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <DateRangePicker />
          <button
            onClick={handleExport}
            disabled={exporting}
            style={{
              padding: "7px 16px",
              border: "1px solid var(--border)",
              borderRadius: 8,
              fontSize: 13,
              color: exporting ? "var(--text-muted)" : "var(--text)",
              whiteSpace: "nowrap",
              transition: "border-color 0.15s",
            }}
          >
            {exporting ? "Экспорт…" : "↓ CSV"}
          </button>
        </div>
      </div>
      {exportError && (
        <div style={{
          background: "rgba(239,68,68,0.1)", border: "1px solid var(--red)",
          borderRadius: 8, padding: "10px 14px", fontSize: 13, color: "var(--red)",
        }}>
          {exportError}
        </div>
      )}
      <AttributionTable />
    </div>
  );
}
