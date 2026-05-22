import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  adminFetchDomains,
  adminVerifyDomain,
  adminActivateDomain,
  adminSuspendDomain,
  adminDeleteDomain,
  type CustomDomain,
} from "../../api/links";

const STATUS_LABELS: Record<string, string> = {
  pending_cname: "Ожидает CNAME",
  pending_ssl:   "Ожидает SSL",
  active:        "Активен",
  error:         "Ошибка",
  suspended:     "Приостановлен",
};

function statusColor(status: string): React.CSSProperties {
  const map: Record<string, React.CSSProperties> = {
    active:        { background: "#d1fae5", color: "#065f46" },
    pending_cname: { background: "#fef3c7", color: "#92400e" },
    pending_ssl:   { background: "#dbeafe", color: "#1e40af" },
    error:         { background: "#fee2e2", color: "#991b1b" },
    suspended:     { background: "#f3f4f6", color: "#374151" },
  };
  return map[status] ?? {};
}

export default function AdminDomainsPage() {
  const qc = useQueryClient();
  const [statusFilter, setStatusFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");

  const { data: domains = [], isLoading, isError } = useQuery<CustomDomain[]>({
    queryKey: ["admin-domains", statusFilter, typeFilter],
    queryFn: () =>
      adminFetchDomains({
        status: statusFilter || undefined,
        domain_type: typeFilter || undefined,
      }),
  });

  const verify   = useMutation({ mutationFn: adminVerifyDomain,   onSuccess: () => qc.invalidateQueries({ queryKey: ["admin-domains"] }) });
  const activate = useMutation({ mutationFn: adminActivateDomain, onSuccess: () => qc.invalidateQueries({ queryKey: ["admin-domains"] }) });
  const suspend  = useMutation({ mutationFn: adminSuspendDomain,  onSuccess: () => qc.invalidateQueries({ queryKey: ["admin-domains"] }) });
  const remove   = useMutation({ mutationFn: adminDeleteDomain,   onSuccess: () => qc.invalidateQueries({ queryKey: ["admin-domains"] }) });

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700 }}>Управление доменами</h1>
        <div style={{ display: "flex", gap: 10 }}>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            style={{ padding: "7px 12px", border: "1px solid var(--border)", borderRadius: 8, background: "var(--bg-card)", color: "var(--text)", fontSize: 13 }}
          >
            <option value="">Все статусы</option>
            <option value="pending_cname">Ожидает CNAME</option>
            <option value="pending_ssl">Ожидает SSL</option>
            <option value="active">Активен</option>
            <option value="error">Ошибка</option>
            <option value="suspended">Приостановлен</option>
          </select>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            style={{ padding: "7px 12px", border: "1px solid var(--border)", borderRadius: 8, background: "var(--bg-card)", color: "var(--text)", fontSize: 13 }}
          >
            <option value="">Все типы</option>
            <option value="own">Свой</option>
            <option value="purchased">Купленный</option>
          </select>
        </div>
      </div>

      {isLoading && <p style={{ color: "var(--text-muted)", textAlign: "center", padding: "60px 0" }}>Загрузка…</p>}
      {isError   && <p style={{ color: "#ef4444",       textAlign: "center", padding: "60px 0" }}>Ошибка загрузки</p>}

      {!isLoading && !isError && (
        <div style={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: "var(--radius)", overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
            <thead>
              <tr>
                {["Домен", "Тип", "Пользователь", "Статус", "CNAME", "Создан", "Действия"].map((h) => (
                  <th
                    key={h}
                    style={{
                      padding: "11px 16px",
                      textAlign: "left",
                      fontSize: 11,
                      fontWeight: 600,
                      color: "var(--text-muted)",
                      textTransform: "uppercase",
                      borderBottom: "1px solid var(--border)",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {domains.length === 0 && (
                <tr>
                  <td colSpan={7} style={{ padding: "40px 16px", textAlign: "center", color: "var(--text-muted)" }}>
                    Нет доменов
                  </td>
                </tr>
              )}
              {domains.map((d) => (
                <tr
                  key={d.id}
                  style={{ borderBottom: "1px solid var(--border)" }}
                >
                  <td style={{ padding: "12px 16px", fontWeight: 500 }}>
                    <div>{d.domain}</div>
                    {d.error_message && (
                      <div style={{ fontSize: 11, color: "#ef4444", marginTop: 2 }}>
                        {d.error_message}
                      </div>
                    )}
                  </td>
                  <td style={{ padding: "12px 16px", color: "var(--text-muted)" }}>
                    {d.domain_type === "own" ? "Свой" : "Купленный"}
                  </td>
                  <td style={{ padding: "12px 16px", fontFamily: "monospace", fontSize: 11, color: "var(--text-muted)" }}>
                    {d.user_id.slice(0, 8)}…
                  </td>
                  <td style={{ padding: "12px 16px" }}>
                    <span
                      style={{
                        display: "inline-flex",
                        padding: "3px 8px",
                        borderRadius: 12,
                        fontSize: 11,
                        fontWeight: 600,
                        ...statusColor(d.status),
                      }}
                    >
                      {STATUS_LABELS[d.status] ?? d.status}
                    </span>
                  </td>
                  <td style={{ padding: "12px 16px", textAlign: "center" }}>
                    {d.cname_verified ? "✅" : "⬜"}
                  </td>
                  <td style={{ padding: "12px 16px", color: "var(--text-muted)", whiteSpace: "nowrap" }}>
                    {new Date(d.created_at).toLocaleDateString("ru-RU")}
                  </td>
                  <td style={{ padding: "12px 16px" }}>
                    <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                      {d.status === "pending_cname" && (
                        <button
                          onClick={() => verify.mutate(d.id)}
                          style={actionBtnStyle("#dbeafe", "#1e40af")}
                        >
                          Verify CNAME
                        </button>
                      )}
                      {(d.status === "pending_ssl" || d.status === "pending_cname") && (
                        <button
                          onClick={() => activate.mutate(d.id)}
                          style={actionBtnStyle("#d1fae5", "#065f46")}
                        >
                          Активировать
                        </button>
                      )}
                      {d.status === "active" && (
                        <button
                          onClick={() => {
                            if (confirm(`Приостановить ${d.domain}?`)) suspend.mutate(d.id);
                          }}
                          style={actionBtnStyle("#fef3c7", "#92400e")}
                        >
                          Приостановить
                        </button>
                      )}
                      {d.status === "suspended" && (
                        <button
                          onClick={() => activate.mutate(d.id)}
                          style={actionBtnStyle("#d1fae5", "#065f46")}
                        >
                          Восстановить
                        </button>
                      )}
                      <button
                        onClick={() => {
                          if (confirm(`Удалить домен ${d.domain}?`)) remove.mutate(d.id);
                        }}
                        style={actionBtnStyle("#fee2e2", "#991b1b")}
                      >
                        Удалить
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function actionBtnStyle(bg: string, color: string): React.CSSProperties {
  return {
    padding: "4px 10px",
    borderRadius: 6,
    fontSize: 11,
    fontWeight: 600,
    border: "none",
    cursor: "pointer",
    background: bg,
    color,
    whiteSpace: "nowrap" as const,
  };
}
