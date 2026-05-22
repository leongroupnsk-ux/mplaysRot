import { useEffect, useState } from "react";
import adminApi from "../../api/admin";
import styles from "./AdminAuditPage.module.css";

interface AuditEntry {
  id: string;
  admin_email: string;
  action: string;
  target_type: string | null;
  target_id: string | null;
  payload: Record<string, unknown> | null;
  ip_address: string | null;
  created_at: string;
}

const ACTION_COLOR: Record<string, string> = {
  create_plan: "green", update_plan: "blue", delete_plan: "red",
  assign_plan: "purple", create_promo: "green", delete_promo: "red",
  change_role: "yellow", block_user: "red", delete_segment: "red",
};

export default function AdminAuditPage() {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<string | null>(null);

  useEffect(() => {
    adminApi.get<AuditEntry[]>("/audit-log", { params: { limit: 100 } })
      .then((r) => setEntries(r.data))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.title}>Журнал аудита</h1>
        <p className={styles.subtitle}>Все действия администраторов · неизменяемый лог</p>
      </header>

      <div className={styles.tableWrap}>
        <table className={styles.table}>
          <thead>
            <tr><th>Время</th><th>Администратор</th><th>Действие</th><th>Объект</th><th>ID объекта</th><th>IP</th><th></th></tr>
          </thead>
          <tbody>
            {loading && (
              <tr><td colSpan={7} className={styles.cell}>Загрузка…</td></tr>
            )}
            {!loading && entries.length === 0 && (
              <tr><td colSpan={7} className={styles.cell}>Записей пока нет</td></tr>
            )}
            {entries.map((e) => (
              <>
                <tr key={e.id}>
                  <td className={styles.tdDate}>{new Date(e.created_at).toLocaleString("ru")}</td>
                  <td className={styles.tdEmail}>{e.admin_email}</td>
                  <td>
                    <span className={`${styles.action} ${styles[`action_${ACTION_COLOR[e.action] || "grey"}`]}`}>
                      {e.action}
                    </span>
                  </td>
                  <td>{e.target_type ?? "—"}</td>
                  <td className={styles.tdMono}>{e.target_id ? `${e.target_id.slice(0, 8)}…` : "—"}</td>
                  <td className={styles.tdMono}>{e.ip_address ?? "—"}</td>
                  <td>
                    {e.payload && (
                      <button
                        className={styles.expandBtn}
                        onClick={() => setExpanded(expanded === e.id ? null : e.id)}
                      >
                        {expanded === e.id ? "▲" : "▼"}
                      </button>
                    )}
                  </td>
                </tr>
                {expanded === e.id && e.payload && (
                  <tr key={`${e.id}-payload`}>
                    <td colSpan={7} className={styles.payloadRow}>
                      <pre className={styles.payload}>{JSON.stringify(e.payload, null, 2)}</pre>
                    </td>
                  </tr>
                )}
              </>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
