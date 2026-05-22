import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useFilters } from "../../store/filters";
import { fetchAttributionLog } from "../../api/attribution";
import styles from "./AttributionTable.module.css";

interface Props { campaignId?: string; }

export default function AttributionTable({ campaignId }: Props) {
  const { dateFrom, dateTo } = useFilters();
  const [minConf, setMinConf] = useState(0);
  const [offset, setOffset] = useState(0);
  const limit = 20;

  const { data, isLoading } = useQuery({
    queryKey: ["attribution-log", dateFrom, dateTo, campaignId, minConf, offset],
    queryFn: () =>
      fetchAttributionLog({
        date_from: dateFrom,
        date_to: dateTo,
        campaign_id: campaignId,
        min_confidence: minConf,
        limit,
        offset,
      }),
  });

  const total = data?.total ?? 0;
  const items = data?.items ?? [];

  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <h3 className={styles.title}>Лог атрибуций</h3>
        <div className={styles.filters}>
          <label className={styles.filterLabel}>
            Мин. уверенность:
            <select value={minConf} onChange={(e) => { setMinConf(Number(e.target.value)); setOffset(0); }}>
              <option value={0}>Все</option>
              <option value={0.5}>≥ 50%</option>
              <option value={0.7}>≥ 70%</option>
              <option value={0.9}>≥ 90%</option>
            </select>
          </label>
        </div>
      </div>

      <div className={styles.tableWrap}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Заказ</th>
              <th>Товар</th>
              <th>Сумма</th>
              <th>Время клика</th>
              <th>Время заказа</th>
              <th>Ч. до заказа</th>
              <th>Метод</th>
              <th>Уверенность</th>
            </tr>
          </thead>
          <tbody>
            {isLoading
              ? Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i}><td colSpan={8}><div className={styles.skeletonRow} /></td></tr>
                ))
              : items.map((row) => (
                  <tr key={row.attribution_id}>
                    <td className={styles.mono}>{row.order_id.slice(-8)}</td>
                    <td>{row.product_id}</td>
                    <td>{row.order_amount.toLocaleString("ru")} ₽</td>
                    <td>{new Date(row.click_at).toLocaleString("ru")}</td>
                    <td>{new Date(row.order_at).toLocaleString("ru")}</td>
                    <td>{row.hours_to_order.toFixed(1)}ч</td>
                    <td>
                      <span className={row.attribution_method === "strict" ? styles.strict : styles.prob}>
                        {row.attribution_method === "strict" ? "Строгая" : "ML"}
                      </span>
                    </td>
                    <td>
                      <span
                        className={styles.confidence}
                        style={{ color: row.confidence >= 0.7 ? "var(--green)" : "var(--yellow)" }}
                      >
                        {(row.confidence * 100).toFixed(0)}%
                      </span>
                    </td>
                  </tr>
                ))}
          </tbody>
        </table>
      </div>

      <div className={styles.pagination}>
        <span className={styles.total}>{total.toLocaleString("ru")} записей</span>
        <div className={styles.pages}>
          <button disabled={offset === 0} onClick={() => setOffset((o) => Math.max(0, o - limit))}>←</button>
          <span>{Math.floor(offset / limit) + 1} / {Math.ceil(total / limit) || 1}</span>
          <button
            disabled={offset + limit >= total}
            onClick={() => setOffset((o) => o + limit)}
          >→</button>
        </div>
      </div>
    </div>
  );
}
