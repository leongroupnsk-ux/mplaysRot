import React, { useState, useMemo } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import pageStyles from "./Page.module.css";
import styles from "./LogisticsTrackerPage.module.css";
import { fetchWBStocks, type WBStockItem } from "../api/logistics";

// ── LocalStorage persistence ──────────────────────────────────────────────────

const LS_KEY = "wb_stocks_cache";
const LS_TS_KEY = "wb_stocks_cache_ts";

function loadCachedStocks(): WBStockItem[] | undefined {
  try {
    const raw = localStorage.getItem(LS_KEY);
    return raw ? JSON.parse(raw) : undefined;
  } catch { return undefined; }
}

function saveCachedStocks(data: WBStockItem[]) {
  try {
    localStorage.setItem(LS_KEY, JSON.stringify(data));
    localStorage.setItem(LS_TS_KEY, new Date().toISOString());
  } catch { /* ignore quota errors */ }
}

function loadCachedTs(): string | null {
  try { return localStorage.getItem(LS_TS_KEY); } catch { return null; }
}

function formatTs(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleDateString("ru-RU", { day: "numeric", month: "short" })
    + " в " + d.toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" });
}

// ── Types ─────────────────────────────────────────────────────────────────────

type StockStatus = "ok" | "warn" | "danger";

interface SizeWarehouseStock {
  quantityFull: number;
  quantity: number;
  inWayToClient: number;
  inWayFromClient: number;
}

interface ProductGroup {
  nmId: number;
  supplierArticle: string;
  brand: string;
  subject: string;
  category: string;
  totalQuantity: number;
  totalInWayToClient: number;
  totalInWayFromClient: number;
  // sizes × warehouses
  grid: Record<string, Record<string, SizeWarehouseStock>>;
  warehouses: string[];
  sizes: string[];
}

// ── Data grouping ─────────────────────────────────────────────────────────────

function groupStocks(items: WBStockItem[]): ProductGroup[] {
  const map = new Map<number, ProductGroup>();

  for (const item of items) {
    if (!map.has(item.nmId)) {
      map.set(item.nmId, {
        nmId: item.nmId,
        supplierArticle: item.supplierArticle,
        brand: item.brand,
        subject: item.subject,
        category: item.category,
        totalQuantity: 0,
        totalInWayToClient: 0,
        totalInWayFromClient: 0,
        grid: {},
        warehouses: [],
        sizes: [],
      });
    }

    const pg = map.get(item.nmId)!;
    pg.totalQuantity += item.quantity;
    pg.totalInWayToClient += item.inWayToClient;
    pg.totalInWayFromClient += item.inWayFromClient;

    const wh = item.warehouseName || "Неизвестный";
    const sz = item.techSize || "—";

    if (!pg.grid[sz]) pg.grid[sz] = {};
    if (!pg.grid[sz][wh]) {
      pg.grid[sz][wh] = { quantityFull: 0, quantity: 0, inWayToClient: 0, inWayFromClient: 0 };
    }
    const cell = pg.grid[sz][wh];
    cell.quantityFull += item.quantityFull;
    cell.quantity += item.quantity;
    cell.inWayToClient += item.inWayToClient;
    cell.inWayFromClient += item.inWayFromClient;

    if (!pg.warehouses.includes(wh)) pg.warehouses.push(wh);
    if (!pg.sizes.includes(sz)) pg.sizes.push(sz);
  }

  // Sort sizes: numeric (XS<S<M<L<XL) or alphabetic
  const sizeOrder = ["XS", "S", "M", "L", "XL", "XXL", "3XL", "4XL", "5XL"];
  for (const pg of map.values()) {
    pg.sizes.sort((a, b) => {
      const ia = sizeOrder.indexOf(a);
      const ib = sizeOrder.indexOf(b);
      if (ia >= 0 && ib >= 0) return ia - ib;
      // numeric sizes
      const na = parseFloat(a), nb = parseFloat(b);
      if (!isNaN(na) && !isNaN(nb)) return na - nb;
      return a.localeCompare(b);
    });
    pg.warehouses.sort();
  }

  return Array.from(map.values()).sort((a, b) => b.totalQuantity - a.totalQuantity);
}

function calcStatus(qty: number): StockStatus {
  if (qty === 0) return "danger";
  if (qty <= 10) return "warn";
  return "ok";
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function statusLabel(s: StockStatus) {
  if (s === "ok")     return { cls: styles.ok,     text: "В норме",   dot: "●" };
  if (s === "warn")   return { cls: styles.warn,   text: "Мало",      dot: "●" };
  if (s === "danger") return { cls: styles.danger, text: "Нет товара", dot: "●" };
  return { cls: "", text: s, dot: "●" };
}

function stockFillClass(s: StockStatus) {
  if (s === "danger") return styles.fillDanger;
  if (s === "warn") return styles.fillWarn;
  return styles.fillOk;
}

// ── Size grid sub-table ───────────────────────────────────────────────────────

function SizeGrid({ product }: { product: ProductGroup }) {
  const { sizes, warehouses, grid } = product;
  const hasMultipleWarehouses = warehouses.length > 1;

  return (
    <div className={styles.sizeGridWrap}>
      <div className={styles.sizeGridTitle}>
        Размерная сетка по складам
        <span className={styles.sizeGridMeta}>
          {sizes.length} {sizes.length === 1 ? "размер" : sizes.length < 5 ? "размера" : "размеров"}
          {" · "}
          {warehouses.length} {warehouses.length === 1 ? "склад" : warehouses.length < 5 ? "склада" : "складов"}
        </span>
      </div>

      <div className={styles.sizeGridTableWrap}>
        <table className={styles.sizeGridTable}>
          <thead>
            <tr>
              <th className={styles.sizeGridSizeCol}>Размер</th>
              {warehouses.map((wh) => (
                <th key={wh} className={styles.sizeGridWhCol}>{wh}</th>
              ))}
              {hasMultipleWarehouses && (
                <th className={styles.sizeGridTotalCol}>Итого</th>
              )}
              <th className={styles.sizeGridWhCol} style={{ color: "#60a5fa" }}>В пути ↓</th>
              <th className={styles.sizeGridWhCol} style={{ color: "#f472b6" }}>Возврат ↑</th>
            </tr>
          </thead>
          <tbody>
            {sizes.map((sz) => {
              const sizeTotal = warehouses.reduce(
                (sum, wh) => sum + (grid[sz]?.[wh]?.quantity ?? 0), 0
              );
              const sizeTotalInWay = warehouses.reduce(
                (sum, wh) => sum + (grid[sz]?.[wh]?.inWayToClient ?? 0), 0
              );
              const sizeTotalReturn = warehouses.reduce(
                (sum, wh) => sum + (grid[sz]?.[wh]?.inWayFromClient ?? 0), 0
              );
              const szStatus = calcStatus(sizeTotal);

              return (
                <tr key={sz} className={styles.sizeGridRow}>
                  <td className={`${styles.sizeGridSizeCell} ${styles[szStatus]}`}>
                    {sz}
                  </td>
                  {warehouses.map((wh) => {
                    const cell = grid[sz]?.[wh];
                    const qty = cell?.quantity ?? 0;
                    const qStatus = calcStatus(qty);
                    return (
                      <td key={wh} className={`${styles.sizeGridCell} ${styles[qStatus]}`}>
                        {cell ? (
                          <>
                            <span className={styles.sizeGridQty}>{qty}</span>
                            {cell.quantityFull !== qty && (
                              <span className={styles.sizeGridFull}> /{cell.quantityFull}</span>
                            )}
                          </>
                        ) : (
                          <span className={styles.sizeGridEmpty}>—</span>
                        )}
                      </td>
                    );
                  })}
                  {hasMultipleWarehouses && (
                    <td className={`${styles.sizeGridCell} ${styles.sizeGridTotalCell} ${styles[szStatus]}`}>
                      <span className={styles.sizeGridQty}>{sizeTotal}</span>
                    </td>
                  )}
                  <td className={styles.sizeGridCell} style={{ color: "#60a5fa" }}>
                    {sizeTotalInWay > 0 ? `+${sizeTotalInWay}` : "—"}
                  </td>
                  <td className={styles.sizeGridCell} style={{ color: "#f472b6" }}>
                    {sizeTotalReturn > 0 ? `+${sizeTotalReturn}` : "—"}
                  </td>
                </tr>
              );
            })}
          </tbody>
          <tfoot>
            <tr className={styles.sizeGridFooter}>
              <td className={styles.sizeGridSizeCell}>Итого</td>
              {warehouses.map((wh) => {
                const whTotal = sizes.reduce(
                  (sum, sz) => sum + (grid[sz]?.[wh]?.quantity ?? 0), 0
                );
                return (
                  <td key={wh} className={`${styles.sizeGridCell} ${styles.sizeGridTotalCell}`}>
                    {whTotal}
                  </td>
                );
              })}
              {hasMultipleWarehouses && (
                <td className={`${styles.sizeGridCell} ${styles.sizeGridTotalCell}`}>
                  {product.totalQuantity}
                </td>
              )}
              <td className={`${styles.sizeGridCell} ${styles.sizeGridTotalCell}`} style={{ color: "#60a5fa" }}>
                {product.totalInWayToClient > 0 ? `+${product.totalInWayToClient}` : "—"}
              </td>
              <td className={`${styles.sizeGridCell} ${styles.sizeGridTotalCell}`} style={{ color: "#f472b6" }}>
                {product.totalInWayFromClient > 0 ? `+${product.totalInWayFromClient}` : "—"}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function LogisticsTrackerPage() {
  const [search, setSearch] = useState("");
  const [filterStatus, setFilterStatus] = useState<"all" | StockStatus>("all");
  const [filterWarehouse, setFilterWarehouse] = useState("all");
  const [expanded, setExpanded] = useState<Set<number>>(new Set());
  const [lastUpdatedTs, setLastUpdatedTs] = useState<string | null>(loadCachedTs);

  const queryClient = useQueryClient();

  const { data: rawStocks, isLoading, isFetching, isError, error } = useQuery({
    queryKey: ["wb-stocks"],
    queryFn: async () => {
      const data = await fetchWBStocks();
      saveCachedStocks(data);
      setLastUpdatedTs(new Date().toISOString());
      return data;
    },
    // Данные никогда не считаются устаревшими — только ручное обновление
    staleTime: Infinity,
    gcTime: 30 * 60_000,
    // Начальные данные из localStorage — страница не делает запрос при открытии
    initialData: loadCachedStocks,
    initialDataUpdatedAt: () => {
      const ts = loadCachedTs();
      return ts ? new Date(ts).getTime() : 0;
    },
    refetchOnMount: false,
    refetchOnWindowFocus: false,
    retry: (failCount, err) => {
      const status = (err as { response?: { status?: number } })?.response?.status;
      if (status === 429 || status === 404) return false;
      return failCount < 1;
    },
  });

  function handleRefresh() {
    queryClient.invalidateQueries({ queryKey: ["wb-stocks"] });
  }

  const products = useMemo(
    () => groupStocks(rawStocks ?? []),
    [rawStocks]
  );

  // All unique warehouses across all products
  const allWarehouses = useMemo(() => {
    const set = new Set<string>();
    products.forEach((p) => p.warehouses.forEach((wh) => set.add(wh)));
    return Array.from(set).sort();
  }, [products]);

  const filtered = useMemo(() => {
    return products.filter((p) => {
      const status = calcStatus(p.totalQuantity);
      if (filterStatus !== "all" && status !== filterStatus) return false;
      if (filterWarehouse !== "all" && !p.warehouses.includes(filterWarehouse)) return false;
      if (search) {
        const q = search.toLowerCase();
        if (
          !p.supplierArticle.toLowerCase().includes(q) &&
          !p.subject.toLowerCase().includes(q) &&
          !p.brand.toLowerCase().includes(q) &&
          !String(p.nmId).includes(q)
        ) return false;
      }
      return true;
    });
  }, [products, filterStatus, filterWarehouse, search]);

  // Summary counters
  const totalProducts = products.length;
  const criticalCount = products.filter((p) => calcStatus(p.totalQuantity) === "danger").length;
  const warnCount = products.filter((p) => calcStatus(p.totalQuantity) === "warn").length;
  const totalInWay = products.reduce((s, p) => s + p.totalInWayToClient, 0);

  function toggleExpand(nmId: number) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(nmId)) next.delete(nmId);
      else next.add(nmId);
      return next;
    });
  }

  // ── Render ──────────────────────────────────────────────────────────────────

  // Если при обновлении пришла ошибка, но есть кэш — показываем таблицу с баннером ошибки
  const hasCache = (rawStocks?.length ?? 0) > 0;

  const errorBanner = isError ? (() => {
    const axiosErr = error as { response?: { data?: { detail?: string }; status?: number; headers?: Record<string, string> } };
    const status = axiosErr?.response?.status;
    const msg = axiosErr?.response?.data?.detail ?? String(error);
    const noConnection = status === 404;
    const rateLimit = status === 429;
    const retryAfter = rateLimit ? (axiosErr?.response?.headers?.["retry-after"] ?? "60") : null;

    if (!hasCache) {
      // Нет кэша — показываем полноэкранную ошибку
      return (
        <div className={pageStyles.page}>
          <div className={pageStyles.toolbar}>
            <h1 className={pageStyles.heading}>Logistics Tracker</h1>
          </div>
          <div className={styles.errorState}>
            <div className={styles.errorIcon}>
              {rateLimit ? "⏳" : noConnection ? "🔌" : "⚠️"}
            </div>
            <div className={styles.errorTitle}>
              {rateLimit ? "WB API: лимит запросов"
                : noConnection ? "Нет подключённого кабинета Wildberries"
                : "Ошибка загрузки данных"}
            </div>
            <div className={styles.errorMsg}>
              {rateLimit
                ? `Wildberries ограничивает частоту запросов. Попробуйте через ${retryAfter} сек.`
                : noConnection
                ? "Подключите кабинет WB в разделе «Интеграции», чтобы видеть остатки."
                : msg}
            </div>
          </div>
        </div>
      );
    }

    // Есть кэш — вернём inline-баннер
    return (
      <div className={styles.refreshErrorBanner}>
        <span>{rateLimit ? "⏳" : "⚠️"}</span>
        <span>
          {rateLimit
            ? `WB API лимит. Попробуйте через ${retryAfter} сек.`
            : noConnection ? "Нет активного подключения WB"
            : msg}
          {" "}Показаны данные на {formatTs(lastUpdatedTs)}.
        </span>
        <button className={styles.btnRefreshSmall} onClick={handleRefresh}>
          Повторить
        </button>
      </div>
    );
  })() : null;

  if (isError && !hasCache) return errorBanner as React.ReactElement;

  return (
    <div className={pageStyles.page}>
      {/* Header */}
      <div className={pageStyles.toolbar}>
        <h1 className={pageStyles.heading}>Logistics Tracker</h1>
        <div className={styles.headerRight}>
          {lastUpdatedTs && !isFetching && (
            <span className={styles.lastUpdate}>
              Обновлено {formatTs(lastUpdatedTs)}
            </span>
          )}
          {isFetching && (
            <span className={styles.fetchingLabel}>
              <span className={styles.spinnerInline} /> Загрузка…
            </span>
          )}
          <button
            className={styles.btnRefresh}
            onClick={handleRefresh}
            disabled={isFetching}
            title="Запросить свежие данные из WB"
          >
            {isFetching ? "Обновление…" : "↻ Обновить"}
          </button>
        </div>
      </div>

      {/* Error banner (при наличии кэша) */}
      {errorBanner}

      {/* Alert banner */}
      {criticalCount > 0 && (
        <div className={styles.alertBanner}>
          <span className={styles.alertIcon}>⚠️</span>
          <span className={styles.alertText}>
            <strong>{criticalCount} {criticalCount === 1 ? "товар" : criticalCount < 5 ? "товара" : "товаров"}</strong>
            {" "}полностью отсутствует на складах.
          </span>
        </div>
      )}

      {/* Summary cards */}
      <div className={styles.summaryGrid}>
        <div className={styles.summaryCard}>
          <div className={styles.summaryLabel}>Позиций в базе</div>
          <div className={styles.summaryValue}>{isLoading ? "…" : totalProducts}</div>
          <div className={styles.summarySub}>уникальных артикулов</div>
        </div>
        <div className={styles.summaryCard}>
          <div className={styles.summaryLabel}>Нет на складе</div>
          <div className={`${styles.summaryValue} ${criticalCount > 0 ? styles.danger : styles.ok}`}>
            {isLoading ? "…" : criticalCount}
          </div>
          <div className={styles.summarySub}>quantity = 0</div>
        </div>
        <div className={styles.summaryCard}>
          <div className={styles.summaryLabel}>Мало остатков</div>
          <div className={`${styles.summaryValue} ${warnCount > 0 ? styles.warn : styles.ok}`}>
            {isLoading ? "…" : warnCount}
          </div>
          <div className={styles.summarySub}>≤ 10 единиц</div>
        </div>
        <div className={styles.summaryCard}>
          <div className={styles.summaryLabel}>В пути к клиентам</div>
          <div className={`${styles.summaryValue} ${styles.ok}`}>{isLoading ? "…" : totalInWay}</div>
          <div className={styles.summarySub}>единиц в доставке</div>
        </div>
      </div>

      {/* Filters */}
      <div className={styles.filters}>
        <input
          className={styles.searchInput}
          type="text"
          placeholder="Поиск по артикулу, бренду, категории, nmId…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select
          className={styles.filterSelect}
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value as typeof filterStatus)}
        >
          <option value="all">Все статусы</option>
          <option value="danger">Нет товара</option>
          <option value="warn">Мало</option>
          <option value="ok">В норме</option>
        </select>
        <select
          className={styles.filterSelect}
          value={filterWarehouse}
          onChange={(e) => setFilterWarehouse(e.target.value)}
        >
          <option value="all">Все склады WB</option>
          {allWarehouses.map((wh) => (
            <option key={wh} value={wh}>{wh}</option>
          ))}
        </select>
        {(filterStatus !== "all" || filterWarehouse !== "all" || search) && (
          <button
            className={styles.btnClearFilter}
            onClick={() => { setSearch(""); setFilterStatus("all"); setFilterWarehouse("all"); }}
          >
            Сбросить
          </button>
        )}
      </div>

      {/* Table */}
      <div className={styles.tableWrap}>
        {isLoading && !hasCache ? (
          <div className={styles.loadingState}>
            <div className={styles.spinner} />
            <span>Загрузка остатков из Wildberries…</span>
          </div>
        ) : (
          <table className={styles.table}>
            <thead>
              <tr>
                <th style={{ width: 32 }} />
                <th>Артикул / Товар</th>
                <th>Склады</th>
                <th>Остаток</th>
                <th>В пути ↓</th>
                <th>Возврат ↑</th>
                <th>Статус</th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={7} className={styles.emptyCell}>
                    {rawStocks?.length === 0
                      ? "Остатки WB не найдены — возможно, нет товаров на складах"
                      : "Товары не найдены по фильтру"}
                  </td>
                </tr>
              )}
              {filtered.map((product) => {
                const status = calcStatus(product.totalQuantity);
                const sl = statusLabel(status);
                const isOpen = expanded.has(product.nmId);
                const maxQty = Math.max(...filtered.map((p) => p.totalQuantity), 1);
                const fillPct = Math.min(100, (product.totalQuantity / maxQty) * 100);

                return (
                  <React.Fragment key={product.nmId}>
                    <tr
                      className={`${styles.productRow} ${isOpen ? styles.productRowOpen : ""}`}
                      onClick={() => toggleExpand(product.nmId)}
                    >
                      {/* Expand toggle */}
                      <td className={styles.expandCell}>
                        <span className={`${styles.expandIcon} ${isOpen ? styles.expandIconOpen : ""}`}>
                          ›
                        </span>
                      </td>

                      {/* Article / Product */}
                      <td>
                        <div className={styles.productCell}>
                          <div>
                            <div className={styles.productName}>
                              {product.subject}
                              {product.brand && product.brand !== product.subject && (
                                <span className={styles.productBrand}> · {product.brand}</span>
                              )}
                            </div>
                            <div className={styles.productSku}>
                              {product.supplierArticle}
                              <span className={styles.nmId}> · nmId {product.nmId}</span>
                            </div>
                          </div>
                        </div>
                      </td>

                      {/* Warehouses */}
                      <td>
                        <div className={styles.whList}>
                          {product.warehouses.slice(0, 3).map((wh) => (
                            <span key={wh} className={styles.whChip}>{wh}</span>
                          ))}
                          {product.warehouses.length > 3 && (
                            <span className={styles.whChipMore}>+{product.warehouses.length - 3}</span>
                          )}
                        </div>
                      </td>

                      {/* Stock bar */}
                      <td>
                        <div className={styles.stockCell}>
                          <div className={styles.stockBar}>
                            <div
                              className={`${styles.stockFill} ${stockFillClass(status)}`}
                              style={{ width: `${fillPct}%` }}
                            />
                          </div>
                          <span className={styles.stockCount}>{product.totalQuantity} шт.</span>
                        </div>
                      </td>

                      {/* In way to client */}
                      <td>
                        {product.totalInWayToClient > 0 ? (
                          <span className={styles.inWayClient}>+{product.totalInWayToClient}</span>
                        ) : (
                          <span className={styles.muted}>—</span>
                        )}
                      </td>

                      {/* Returns */}
                      <td>
                        {product.totalInWayFromClient > 0 ? (
                          <span className={styles.inWayReturn}>+{product.totalInWayFromClient}</span>
                        ) : (
                          <span className={styles.muted}>—</span>
                        )}
                      </td>

                      {/* Status */}
                      <td>
                        <span className={`${styles.badge} ${sl.cls}`}>
                          {sl.dot} {sl.text}
                        </span>
                      </td>
                    </tr>

                    {/* Expanded size grid */}
                    {isOpen && (
                      <tr className={styles.expandedRow}>
                        <td colSpan={7} className={styles.expandedCell}>
                          <SizeGrid product={product} />
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
