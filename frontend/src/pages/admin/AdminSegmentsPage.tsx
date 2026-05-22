import { useEffect, useState, useCallback } from "react";
import adminApi from "../../api/admin";
import styles from "./AdminSegmentsPage.module.css";

interface Segment {
  id: string;
  user_id: string;
  campaign_id: string;
  ad_platform: string;
  status: string;
  lookalike: boolean;
  created_at: string | null;
}

const STATUS_COLORS: Record<string, string> = {
  pending: "yellow",
  processing: "blue",
  done: "green",
  failed: "red",
};

export default function AdminSegmentsPage() {
  const [segments, setSegments] = useState<Segment[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [deleting, setDeleting] = useState<string | null>(null);

  const load = useCallback(async (userId?: string) => {
    setLoading(true);
    try {
      const { data } = await adminApi.get<Segment[]>("/segments", {
        params: { limit: 100, user_id: userId || undefined },
      });
      setSegments(data);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    load(search || undefined);
  };

  const deleteSegment = async (id: string) => {
    if (!confirm("Удалить сегмент? Действие необратимо.")) return;
    setDeleting(id);
    try {
      await adminApi.delete(`/segments/${id}`);
      setSegments((prev) => prev.filter((s) => s.id !== id));
    } finally {
      setDeleting(null);
    }
  };

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div>
          <h1 className={styles.title}>Сегменты</h1>
          <p className={styles.subtitle}>{segments.length} записей</p>
        </div>
        <form className={styles.searchForm} onSubmit={handleSearch}>
          <input
            className={styles.searchInput}
            placeholder="Фильтр по user_id…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <button className={styles.searchBtn} type="submit">Найти</button>
          {search && (
            <button className={styles.clearBtn} type="button" onClick={() => { setSearch(""); load(); }}>
              Сбросить
            </button>
          )}
        </form>
      </header>

      <div className={styles.tableWrap}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th>ID сегмента</th>
              <th>User ID</th>
              <th>Платформа</th>
              <th>Look-alike</th>
              <th>Статус</th>
              <th>Создан</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr><td colSpan={7} className={styles.cell}>Загрузка…</td></tr>
            )}
            {!loading && segments.length === 0 && (
              <tr><td colSpan={7} className={styles.cell}>Сегменты не найдены</td></tr>
            )}
            {segments.map((s) => (
              <tr key={s.id}>
                <td className={styles.tdMono}>{s.id.slice(0, 8)}…</td>
                <td className={styles.tdMono}>{s.user_id.slice(0, 8)}…</td>
                <td>{s.ad_platform}</td>
                <td>{s.lookalike ? <span className={styles.yes}>✓</span> : <span className={styles.no}>—</span>}</td>
                <td>
                  <span className={`${styles.status} ${styles[`status_${STATUS_COLORS[s.status] || "grey"}`]}`}>
                    {s.status}
                  </span>
                </td>
                <td className={styles.tdDate}>
                  {s.created_at ? new Date(s.created_at).toLocaleDateString("ru") : "—"}
                </td>
                <td>
                  <button
                    className={styles.deleteBtn}
                    onClick={() => deleteSegment(s.id)}
                    disabled={deleting === s.id}
                  >
                    {deleting === s.id ? "…" : "✕"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
