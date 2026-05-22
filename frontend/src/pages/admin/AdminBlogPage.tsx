import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  adminFetchArticles, adminDeleteArticle, adminUpdateArticle,
} from "../../api/blog";

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  published: { label: "Опубликована", color: "#4ade80" },
  draft:     { label: "Черновик",     color: "#fbbf24" },
  archived:  { label: "Архив",        color: "#6b7280" },
};

const CAT_LABELS: Record<string, string> = {
  traffic: "Внешний трафик", logistics: "Логистика",
  analytics: "Аналитика", ai: "AI",
  integrations: "Интеграции", news: "Новости", general: "Общее",
};

function formatDate(iso: string | null) {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("ru-RU", { day: "2-digit", month: "2-digit", year: "2-digit" });
}

export default function AdminBlogPage() {
  const qc = useQueryClient();
  const [filterStatus, setFilterStatus] = useState("");
  const [deleteId, setDeleteId] = useState<number | null>(null);

  const { data = [], isLoading } = useQuery({
    queryKey: ["admin-blog-articles", filterStatus],
    queryFn: () => adminFetchArticles(filterStatus ? { status: filterStatus } : undefined),
    staleTime: 30_000,
  });

  const deleteMut = useMutation({
    mutationFn: adminDeleteArticle,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["admin-blog-articles"] });
      setDeleteId(null);
    },
  });

  const archiveMut = useMutation({
    mutationFn: ({ id }: { id: number }) => adminUpdateArticle(id, { status: "archived" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin-blog-articles"] }),
  });

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20, maxWidth: 1200 }}>
      {/* Toolbar */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 12 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, margin: 0 }}>Блог — статьи</h1>
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            style={selectStyle}
          >
            <option value="">Все статусы</option>
            <option value="published">Опубликованные</option>
            <option value="draft">Черновики</option>
            <option value="archived">Архив</option>
          </select>
          <Link to="/admin/blog/new" style={btnPrimary}>+ Новая статья</Link>
        </div>
      </div>

      {/* Table */}
      <div style={tableWrapStyle}>
        {isLoading ? (
          <div style={emptyStyle}>Загрузка…</div>
        ) : data.length === 0 ? (
          <div style={emptyStyle}>Статьи не найдены</div>
        ) : (
          <table style={tableStyle}>
            <thead>
              <tr>
                {["ID", "Заголовок", "Категория", "Статус", "Просмотры", "Лайки", "Дата", "Автор", ""].map((h) => (
                  <th key={h} style={thStyle}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.map((a) => {
                const sl = STATUS_LABELS[a.status] ?? { label: a.status, color: "#888" };
                return (
                  <tr key={a.id} style={trStyle}>
                    <td style={tdStyle}><span style={idStyle}>{a.id}</span></td>
                    <td style={{ ...tdStyle, maxWidth: 260 }}>
                      <div style={{ fontWeight: 500, fontSize: 13, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {a.title}
                      </div>
                      <div style={{ fontSize: 11, color: "#8890a4" }}>/blog/{a.slug}</div>
                    </td>
                    <td style={tdStyle}><span style={catStyle}>{CAT_LABELS[a.category] ?? a.category}</span></td>
                    <td style={tdStyle}>
                      <span style={{ ...badgeBase, color: sl.color, background: sl.color + "20" }}>
                        {sl.label}
                      </span>
                    </td>
                    <td style={{ ...tdStyle, textAlign: "right" }}>{a.view_count.toLocaleString("ru-RU")}</td>
                    <td style={{ ...tdStyle, textAlign: "right" }}>{a.like_count}</td>
                    <td style={{ ...tdStyle, fontSize: 12, color: "#8890a4" }}>{formatDate(a.published_at)}</td>
                    <td style={{ ...tdStyle, fontSize: 12, color: "#8890a4" }}>{a.author}</td>
                    <td style={tdStyle}>
                      <div style={{ display: "flex", gap: 6 }}>
                        <Link to={`/admin/blog/${a.id}`} style={btnEdit}>Ред.</Link>
                        <a href={`/blog/${a.slug}`} target="_blank" rel="noopener noreferrer" style={btnView}>
                          Просмотр
                        </a>
                        {a.status !== "archived" && (
                          <button
                            style={btnArchive}
                            onClick={() => archiveMut.mutate({ id: a.id })}
                          >
                            Архив
                          </button>
                        )}
                        <button style={btnDelete} onClick={() => setDeleteId(a.id)}>
                          Удалить
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* Delete confirm modal */}
      {deleteId !== null && (
        <div style={overlayStyle}>
          <div style={modalStyle}>
            <div style={{ fontSize: 17, fontWeight: 700, marginBottom: 10 }}>Удалить статью?</div>
            <div style={{ fontSize: 13, color: "#8890a4", marginBottom: 24 }}>
              Это действие необратимо. Статья будет удалена вместе со счётчиками просмотров и лайков.
            </div>
            <div style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
              <button style={btnCancel} onClick={() => setDeleteId(null)}>Отмена</button>
              <button
                style={btnDeleteConfirm}
                onClick={() => deleteMut.mutate(deleteId)}
                disabled={deleteMut.isPending}
              >
                {deleteMut.isPending ? "Удаляем…" : "Удалить"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Inline styles ─────────────────────────────────────────────────────────────

const selectStyle: React.CSSProperties = {
  background: "#141626", border: "1px solid rgba(255,255,255,0.1)",
  borderRadius: 8, padding: "7px 10px", fontSize: 13, color: "#e8eaf0", outline: "none",
};

const btnPrimary: React.CSSProperties = {
  padding: "8px 16px", background: "#7c3aed", color: "#fff",
  borderRadius: 8, fontSize: 13, fontWeight: 600, textDecoration: "none",
};

const tableWrapStyle: React.CSSProperties = {
  background: "#141626", border: "1px solid rgba(255,255,255,0.08)",
  borderRadius: 12, overflow: "auto",
};

const tableStyle: React.CSSProperties = {
  width: "100%", borderCollapse: "collapse", fontSize: 13, minWidth: 900,
};

const thStyle: React.CSSProperties = {
  padding: "10px 14px", fontSize: 10, fontWeight: 700,
  textTransform: "uppercase", letterSpacing: "0.07em",
  color: "#8890a4", borderBottom: "1px solid rgba(255,255,255,0.08)",
  textAlign: "left", whiteSpace: "nowrap", background: "rgba(255,255,255,0.02)",
};

const trStyle: React.CSSProperties = { borderBottom: "1px solid rgba(255,255,255,0.04)" };

const tdStyle: React.CSSProperties = { padding: "11px 14px", color: "#e8eaf0", verticalAlign: "middle" };

const idStyle: React.CSSProperties = {
  fontSize: 11, color: "#8890a4", fontFamily: "monospace",
};

const catStyle: React.CSSProperties = {
  fontSize: 11, padding: "2px 7px",
  background: "rgba(167,139,250,0.12)", color: "#a78bfa", borderRadius: 8,
};

const badgeBase: React.CSSProperties = {
  display: "inline-block", padding: "3px 8px",
  borderRadius: 10, fontSize: 11, fontWeight: 700,
};

const emptyStyle: React.CSSProperties = {
  textAlign: "center", padding: "48px 20px", color: "#8890a4", fontSize: 14,
};

const btnEdit: React.CSSProperties = {
  padding: "4px 10px", background: "rgba(255,255,255,0.06)",
  border: "1px solid rgba(255,255,255,0.1)", borderRadius: 6,
  color: "#e8eaf0", fontSize: 12, textDecoration: "none", whiteSpace: "nowrap",
};

const btnView: React.CSSProperties = {
  padding: "4px 10px", background: "rgba(96,165,250,0.1)",
  border: "1px solid rgba(96,165,250,0.2)", borderRadius: 6,
  color: "#60a5fa", fontSize: 12, textDecoration: "none", whiteSpace: "nowrap",
};

const btnArchive: React.CSSProperties = {
  padding: "4px 10px", background: "rgba(251,191,36,0.1)",
  border: "1px solid rgba(251,191,36,0.2)", borderRadius: 6,
  color: "#fbbf24", fontSize: 12, cursor: "pointer", whiteSpace: "nowrap",
};

const btnDelete: React.CSSProperties = {
  padding: "4px 10px", background: "rgba(248,113,113,0.1)",
  border: "1px solid rgba(248,113,113,0.2)", borderRadius: 6,
  color: "#f87171", fontSize: 12, cursor: "pointer", whiteSpace: "nowrap",
};

const overlayStyle: React.CSSProperties = {
  position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)",
  backdropFilter: "blur(4px)", display: "flex",
  alignItems: "center", justifyContent: "center", zIndex: 999,
};

const modalStyle: React.CSSProperties = {
  background: "#141626", border: "1px solid rgba(255,255,255,0.1)",
  borderRadius: 14, padding: 28, width: 380, maxWidth: "90vw",
};

const btnCancel: React.CSSProperties = {
  padding: "9px 18px", background: "transparent",
  border: "1px solid rgba(255,255,255,0.12)", borderRadius: 8,
  color: "#8890a4", fontSize: 13, cursor: "pointer",
};

const btnDeleteConfirm: React.CSSProperties = {
  padding: "9px 20px", background: "#ef4444",
  border: "none", borderRadius: 8, color: "#fff",
  fontSize: 13, fontWeight: 600, cursor: "pointer",
};
