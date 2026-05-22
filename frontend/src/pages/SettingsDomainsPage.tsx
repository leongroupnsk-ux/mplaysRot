import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchDomains, addDomain, deleteDomain, fetchCnameTarget, type CustomDomain } from "../api/links";
import css from "./SettingsDomainsPage.module.css";

const STATUS_LABELS: Record<string, string> = {
  pending_cname: "Ожидает CNAME",
  pending_ssl:   "Ожидает SSL",
  active:        "Активен",
  error:         "Ошибка",
  suspended:     "Приостановлен",
};

function badgeClass(status: string): string {
  if (status === "active")        return css.badgeActive;
  if (status === "error")         return css.badgeError;
  if (status === "suspended")     return css.badgeSuspend;
  return css.badgePending;
}

export default function SettingsDomainsPage() {
  const qc = useQueryClient();
  const [domain, setDomain] = useState("");
  const [domainType, setDomainType] = useState<"own" | "purchased">("own");
  const [addError, setAddError] = useState<string | null>(null);

  const { data: domains = [], isLoading } = useQuery<CustomDomain[]>({
    queryKey: ["domains"],
    queryFn: fetchDomains,
  });

  const { data: cnameTarget } = useQuery({
    queryKey: ["cname-target"],
    queryFn: fetchCnameTarget,
  });

  const addMut = useMutation({
    mutationFn: () => addDomain({ domain: domain.trim(), domain_type: domainType }),
    onSuccess: () => {
      setDomain("");
      setAddError(null);
      qc.invalidateQueries({ queryKey: ["domains"] });
    },
    onError: (err: any) => {
      const msg = err?.response?.data?.detail || "Ошибка при добавлении домена";
      setAddError(typeof msg === "string" ? msg : JSON.stringify(msg));
    },
  });

  const deleteMut = useMutation({
    mutationFn: deleteDomain,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["domains"] }),
  });

  return (
    <div className={css.page}>
      <h2 className={css.title}>Кастомные домены</h2>

      {/* Info banner */}
      <div className={css.infoBanner}>
        <div className={css.infoBannerTitle}>Как подключить свой домен?</div>
        <div className={css.infoBannerText}>
          1. Добавьте домен в форму ниже.<br />
          2. В настройках DNS создайте CNAME-запись:
          {cnameTarget && (
            <div className={css.codeBlock}>
              {cnameTarget.cname}
            </div>
          )}
          <br />
          3. Дождитесь автоматической проверки (обычно до 24 часов).<br />
          4. После активации все ваши ссылки смогут использовать этот домен.
        </div>
      </div>

      {/* Add domain */}
      <div className={css.addCard}>
        <div className={css.addTitle}>Добавить домен</div>
        <div className={css.addRow}>
          <input
            className={css.input}
            placeholder="example.com"
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && domain.trim() && addMut.mutate()}
          />
          <select
            className={css.selectSmall}
            value={domainType}
            onChange={(e) => setDomainType(e.target.value as "own" | "purchased")}
          >
            <option value="own">Свой домен</option>
            <option value="purchased">Купленный</option>
          </select>
          <button
            className={css.btnAdd}
            disabled={!domain.trim() || addMut.isPending}
            onClick={() => addMut.mutate()}
          >
            {addMut.isPending ? "…" : "Добавить"}
          </button>
        </div>
        {addError && <div className={css.addError}>{addError}</div>}
      </div>

      {/* Domains list */}
      <div>
        <div className={css.listTitle}>Ваши домены</div>

        {isLoading && <div className={css.empty}>Загрузка…</div>}

        {!isLoading && domains.length === 0 && (
          <div className={css.empty}>
            Нет добавленных доменов. Добавьте первый домен выше.
          </div>
        )}

        {domains.map((d) => (
          <div key={d.id} className={css.domainCard}>
            <div className={css.domainIcon}>
              {d.status === "active" ? "🌐" : d.status === "error" ? "⚠️" : "⏳"}
            </div>
            <div className={css.domainInfo}>
              <div className={css.domainName}>{d.domain}</div>
              <div className={css.domainMeta}>
                <span>{d.domain_type === "own" ? "Свой" : "Купленный"}</span>
                <span>
                  Добавлен{" "}
                  {new Date(d.created_at).toLocaleDateString("ru-RU")}
                </span>
                {d.ssl_expires_at && (
                  <span>
                    SSL до {new Date(d.ssl_expires_at).toLocaleDateString("ru-RU")}
                  </span>
                )}
              </div>

              {/* CNAME instruction for pending domains */}
              {d.status === "pending_cname" && cnameTarget && (
                <div className={css.cnameBox}>
                  Добавьте CNAME-запись в ваш DNS:
                  <br />
                  <strong>Тип:</strong> CNAME &nbsp;
                  <strong>Хост:</strong>{" "}
                  <span className={css.cnameCode}>{d.domain}</span> &nbsp;
                  <strong>Значение:</strong>{" "}
                  <span className={css.cnameCode}>{cnameTarget.cname}</span> &nbsp;
                  <strong>TTL:</strong>{" "}
                  <span className={css.cnameCode}>{cnameTarget.ttl}</span>
                </div>
              )}

              {d.error_message && (
                <div style={{ marginTop: 6, fontSize: 12, color: "#ef4444" }}>
                  {d.error_message}
                </div>
              )}
            </div>

            <div className={css.domainActions}>
              <span className={`${css.badge} ${badgeClass(d.status)}`}>
                {STATUS_LABELS[d.status] ?? d.status}
              </span>
              <button
                className={css.btnDelete}
                onClick={() => {
                  if (confirm(`Удалить домен ${d.domain}?`)) {
                    deleteMut.mutate(d.id);
                  }
                }}
              >
                Удалить
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
