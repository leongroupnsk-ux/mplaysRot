import { useState, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import {
  fetchLinks,
  deleteLink,
  updateLink,
  buildShortUrl,
  type DeepLink,
  type CustomDomain,
  fetchDomains,
} from "../api/links";
import CreateLinkModal from "../components/links/CreateLinkModal";
import css from "./LinksPage.module.css";

const MARKETPLACE_LABELS: Record<string, string> = {
  wildberries: "Wildberries",
  ozon: "Ozon",
};

function statusBadgeClass(status: DeepLink["status"]): string {
  if (status === "active") return css.badgeActive;
  if (status === "paused") return css.badgePaused;
  return css.badgeUnavail;
}

function statusLabel(status: DeepLink["status"]): string {
  if (status === "active") return "Активна";
  if (status === "paused") return "Пауза";
  return "Недоступен";
}

export default function LinksPage() {
  const qc = useQueryClient();
  const navigate = useNavigate();
  const [showCreate, setShowCreate] = useState(false);
  const [marketplace, setMarketplace] = useState("");
  const [linkType, setLinkType] = useState("");
  const [search, setSearch] = useState("");
  const [copied, setCopied] = useState<string | null>(null);

  const { data: links = [], isLoading, isError } = useQuery({
    queryKey: ["links", marketplace, linkType],
    queryFn: () =>
      fetchLinks({ marketplace: marketplace || undefined, link_type: linkType || undefined }),
  });

  const { data: domains = [] } = useQuery({
    queryKey: ["domains"],
    queryFn: fetchDomains,
  });

  const domainMap = useMemo(
    () => Object.fromEntries(domains.map((d: CustomDomain) => [d.id, d])),
    [domains]
  );

  const deleteMut = useMutation({
    mutationFn: deleteLink,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["links"] }),
  });

  const togglePause = useMutation({
    mutationFn: (link: DeepLink) =>
      updateLink(link.id, { status: link.status === "active" ? "paused" : "active" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["links"] }),
  });

  const copyUrl = (url: string, id: string) => {
    navigator.clipboard.writeText(url).then(() => {
      setCopied(id);
      setTimeout(() => setCopied(null), 1500);
    });
  };

  const filtered = useMemo(() => {
    if (!search.trim()) return links;
    const q = search.toLowerCase();
    return links.filter(
      (l) =>
        l.short_code.toLowerCase().includes(q) ||
        l.product_title?.toLowerCase().includes(q) ||
        l.name?.toLowerCase().includes(q) ||
        l.external_product_id.toLowerCase().includes(q)
    );
  }, [links, search]);

  const totalClicks = links.reduce((s, l) => s + l.click_count, 0);
  const activeCount = links.filter((l) => l.status === "active").length;

  return (
    <div className={css.page}>
      {/* Header */}
      <div className={css.header}>
        <h1 className={css.title}>Диплинки</h1>
        <div className={css.headerRight}>
          <button className={css.btnCreate} onClick={() => setShowCreate(true)}>
            + Создать ссылку
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className={css.statsRow}>
        <div className={css.statCard}>
          <div className={css.statLabel}>Всего ссылок</div>
          <div className={css.statValue}>{links.length}</div>
        </div>
        <div className={css.statCard}>
          <div className={css.statLabel}>Активных</div>
          <div className={css.statValue}>{activeCount}</div>
        </div>
        <div className={css.statCard}>
          <div className={css.statLabel}>Всего кликов</div>
          <div className={css.statValue}>{totalClicks.toLocaleString("ru-RU")}</div>
        </div>
        <div className={css.statCard}>
          <div className={css.statLabel}>Ср. кликов</div>
          <div className={css.statValue}>
            {links.length > 0 ? Math.round(totalClicks / links.length) : 0}
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className={css.filters}>
        <input
          className={css.searchInput}
          placeholder="Поиск по названию, коду, SKU…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select
          className={css.filterSelect}
          value={marketplace}
          onChange={(e) => setMarketplace(e.target.value)}
        >
          <option value="">Все маркетплейсы</option>
          <option value="wildberries">Wildberries</option>
          <option value="ozon">Ozon</option>
        </select>
        <select
          className={css.filterSelect}
          value={linkType}
          onChange={(e) => setLinkType(e.target.value)}
        >
          <option value="">Все типы</option>
          <option value="deeplink">Диплинк</option>
          <option value="autolanding">Автолендинг</option>
        </select>
      </div>

      {/* Table */}
      {isLoading && <div className={css.loading}>Загрузка…</div>}
      {isError && <div className={css.error}>Ошибка загрузки ссылок</div>}

      {!isLoading && !isError && (
        <>
          {filtered.length === 0 ? (
            <div className={css.emptyState}>
              <div className={css.emptyIcon}>🔗</div>
              <div className={css.emptyTitle}>Нет ссылок</div>
              <div className={css.emptyHint}>
                Создайте первую диплинк-ссылку, чтобы начать отслеживать трафик с маркетплейсов.
              </div>
              <button className={css.btnCreate} onClick={() => setShowCreate(true)}>
                + Создать первую ссылку
              </button>
            </div>
          ) : (
            <div className={css.tableWrap}>
              <table className={css.table}>
                <thead>
                  <tr>
                    <th>Товар</th>
                    <th>Маркетплейс</th>
                    <th>Тип</th>
                    <th>Короткая ссылка</th>
                    <th>Статус</th>
                    <th>Клики</th>
                    <th>Создана</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((link) => {
                    const url = buildShortUrl(link, domainMap);
                    return (
                      <tr key={link.id}>
                        {/* Product */}
                        <td>
                          <div className={css.productCell}>
                            {link.product_image && (
                              <img
                                className={css.productThumb}
                                src={link.product_image}
                                alt=""
                              />
                            )}
                            <div>
                              <div className={css.productName}>
                                {link.name || link.product_title || "—"}
                              </div>
                              <div className={css.productSku}>
                                SKU: {link.external_product_id}
                              </div>
                            </div>
                          </div>
                        </td>

                        {/* Marketplace */}
                        <td>
                          <span
                            className={`${css.badge} ${
                              link.marketplace === "wildberries" ? css.badgeWb : css.badgeOzon
                            }`}
                          >
                            {MARKETPLACE_LABELS[link.marketplace] ?? link.marketplace}
                          </span>
                        </td>

                        {/* Type */}
                        <td>
                          <span
                            className={`${css.badge} ${
                              link.link_type === "deeplink" ? css.badgeDeep : css.badgeAuto
                            }`}
                          >
                            {link.link_type === "deeplink" ? "Диплинк" : "Автолендинг"}
                          </span>
                        </td>

                        {/* Short URL */}
                        <td>
                          <div className={css.urlCell}>
                            <span className={css.shortUrl}>{url}</span>
                            <button
                              className={css.copyBtn}
                              title="Скопировать"
                              onClick={() => copyUrl(url, link.id)}
                            >
                              {copied === link.id ? "✓" : "⎘"}
                            </button>
                          </div>
                        </td>

                        {/* Status */}
                        <td>
                          <span className={`${css.badge} ${statusBadgeClass(link.status)}`}>
                            {statusLabel(link.status)}
                          </span>
                        </td>

                        {/* Clicks */}
                        <td>{link.click_count.toLocaleString("ru-RU")}</td>

                        {/* Created at */}
                        <td>
                          {new Date(link.created_at).toLocaleDateString("ru-RU", {
                            day: "2-digit",
                            month: "2-digit",
                            year: "2-digit",
                          })}
                        </td>

                        {/* Actions */}
                        <td>
                          <div className={css.actionsCell}>
                            <button
                              className={`${css.actionBtn} ${css.actionBtnStats}`}
                              onClick={() => navigate(`/links/${link.id}/stats`)}
                              title="Статистика"
                            >
                              📊
                            </button>
                            <button
                              className={css.actionBtn}
                              onClick={() => togglePause.mutate(link)}
                              title={link.status === "active" ? "Поставить на паузу" : "Возобновить"}
                            >
                              {link.status === "active" ? "⏸" : "▶"}
                            </button>
                            <button
                              className={`${css.actionBtn} ${css.actionBtnDanger}`}
                              onClick={() => {
                                if (confirm("Удалить ссылку?")) deleteMut.mutate(link.id);
                              }}
                              title="Удалить"
                            >
                              🗑
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      {showCreate && <CreateLinkModal onClose={() => setShowCreate(false)} />}
    </div>
  );
}
