import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { fetchLinkStats, type DailyStat, type FunnelStage, type SourceStat } from "../api/links";
import css from "./LinkStatsPage.module.css";

// ── Tiny bar chart ─────────────────────────────────────────────────────────────
function BarChart({ data }: { data: DailyStat[] }) {
  const max = Math.max(...data.map((d) => d.clicks), 1);
  const show = data.slice(-30);
  return (
    <div className={css.chart}>
      <div className={css.chartBars}>
        {show.map((d) => (
          <div key={d.date} className={css.barWrap} title={`${d.date}: ${d.clicks} кл.`}>
            <div
              className={css.bar}
              style={{ height: `${Math.max((d.clicks / max) * 100, d.clicks > 0 ? 4 : 0)}%` }}
            />
          </div>
        ))}
      </div>
      <div className={css.chartLabels}>
        {show.filter((_, i) => i % Math.ceil(show.length / 6) === 0).map((d) => (
          <span key={d.date} className={css.chartLabel}>
            {d.date.slice(5)}
          </span>
        ))}
      </div>
    </div>
  );
}

// ── Funnel ─────────────────────────────────────────────────────────────────────
function Funnel({ stages }: { stages: FunnelStage[] }) {
  const validStages = stages.filter((s) => s.value !== null);
  const maxVal = Math.max(...validStages.map((s) => s.value as number), 1);

  return (
    <div className={css.funnel}>
      {stages.map((s, i) => {
        const pct = s.value === null ? 0 : Math.max((s.value / maxVal) * 100, s.value > 0 ? 6 : 0);
        const conv =
          i > 0 && stages[i - 1].value && s.value
            ? ((s.value / (stages[i - 1].value as number)) * 100).toFixed(1)
            : null;
        return (
          <div key={s.stage} className={css.funnelStep}>
            <div className={css.funnelLeft}>
              <span className={css.funnelStage}>{s.stage}</span>
              {conv && <span className={css.funnelConv}>↓ {conv}%</span>}
            </div>
            <div className={css.funnelBarWrap}>
              <div
                className={`${css.funnelBar} ${s.value === null ? css.funnelBarEmpty : ""}`}
                style={{ width: `${pct}%` }}
              />
              <span className={css.funnelValue}>
                {s.value === null ? "—" : s.value.toLocaleString("ru-RU")}
              </span>
            </div>
            {s.note && <span className={css.funnelNote}>{s.note}</span>}
          </div>
        );
      })}
    </div>
  );
}

// ── Donut device chart ──────────────────────────────────────────────────────────
const DEVICE_LABELS: Record<string, string> = {
  mobile: "📱 Мобильный",
  desktop: "🖥 Десктоп",
  tablet: "📟 Планшет",
  unknown: "❓ Неизвестно",
};
const DEVICE_COLORS: Record<string, string> = {
  mobile: "#9043e7",
  desktop: "#6821ff",
  tablet: "#4ade80",
  unknown: "#8890a4",
};

function DevicePie({ devices }: { devices: Record<string, number> }) {
  const total = Object.values(devices).reduce((a, b) => a + b, 0);
  if (total === 0)
    return <div className={css.emptyMini}>Нет данных</div>;
  return (
    <div className={css.deviceList}>
      {Object.entries(devices)
        .filter(([, v]) => v > 0)
        .sort(([, a], [, b]) => b - a)
        .map(([key, val]) => (
          <div key={key} className={css.deviceRow}>
            <span className={css.deviceDot} style={{ background: DEVICE_COLORS[key] ?? "#888" }} />
            <span className={css.deviceLabel}>{DEVICE_LABELS[key] ?? key}</span>
            <div className={css.deviceBarWrap}>
              <div
                className={css.deviceBar}
                style={{
                  width: `${(val / total) * 100}%`,
                  background: DEVICE_COLORS[key] ?? "#888",
                }}
              />
            </div>
            <span className={css.devicePct}>{((val / total) * 100).toFixed(0)}%</span>
            <span className={css.deviceCount}>{val}</span>
          </div>
        ))}
    </div>
  );
}

// ── Multi-channel source table ──────────────────────────────────────────────────
function SourceTable({ sources, total }: { sources: SourceStat[]; total: number }) {
  if (!sources.length)
    return <div className={css.emptyMini}>Нет данных о источниках</div>;
  return (
    <table className={css.srcTable}>
      <thead>
        <tr>
          <th>Источник</th>
          <th>Переходы</th>
          <th>Доля</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        {sources.map(({ source, clicks }) => (
          <tr key={source}>
            <td className={css.srcName}>{source}</td>
            <td className={css.srcClicks}>{clicks}</td>
            <td className={css.srcPct}>
              {total > 0 ? ((clicks / total) * 100).toFixed(1) : 0}%
            </td>
            <td className={css.srcBarCell}>
              <div className={css.srcBarWrap}>
                <div
                  className={css.srcBar}
                  style={{ width: `${total > 0 ? (clicks / total) * 100 : 0}%` }}
                />
              </div>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

// ── Main page ───────────────────────────────────────────────────────────────────
const DAYS_OPTIONS = [7, 14, 30, 60, 90];

export default function LinkStatsPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [days, setDays] = useState(30);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["link-stats", id, days],
    queryFn: () => fetchLinkStats(id!, days),
    enabled: !!id,
    refetchOnWindowFocus: false,
  });

  if (isLoading)
    return (
      <div className={css.loadingWrap}>
        <div className={css.spinner} />
        <span>Загрузка статистики…</span>
      </div>
    );

  if (isError || !data)
    return (
      <div className={css.errorWrap}>
        <div className={css.errorIcon}>📊</div>
        <div className={css.errorTitle}>Не удалось загрузить статистику</div>
        <button className={css.btnBack} onClick={() => navigate("/links")}>
          ← Назад к ссылкам
        </button>
      </div>
    );

  const { link, summary, daily, devices, sources, funnel } = data;

  return (
    <div className={css.page}>
      {/* Header */}
      <div className={css.header}>
        <button className={css.btnBack} onClick={() => navigate("/links")}>
          ← Диплинки
        </button>
        <div className={css.headerMain}>
          <div className={css.linkMeta}>
            {link.product_image && (
              <img src={link.product_image} className={css.productImg} alt="" />
            )}
            <div>
              <div className={css.linkName}>
                {link.name || link.product_title || `Ссылка ${link.short_code}`}
              </div>
              <div className={css.linkSub}>
                <span className={css.tag}>{link.marketplace}</span>
                {link.utm_source && <span className={css.tag}>utm: {link.utm_source}</span>}
                {link.utm_campaign && <span className={css.tag}>{link.utm_campaign}</span>}
                <span className={css.tagMono}>/{link.short_code}</span>
              </div>
            </div>
          </div>
          <div className={css.daysFilter}>
            {DAYS_OPTIONS.map((d) => (
              <button
                key={d}
                className={`${css.dayBtn} ${d === days ? css.dayBtnActive : ""}`}
                onClick={() => setDays(d)}
              >
                {d}д
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Summary cards */}
      <div className={css.summaryGrid}>
        <div className={css.card}>
          <div className={css.cardLabel}>Клики</div>
          <div className={css.cardValue}>{summary.total_clicks.toLocaleString("ru-RU")}</div>
          <div className={css.cardSub}>за {summary.days} дней</div>
        </div>
        <div className={css.card}>
          <div className={css.cardLabel}>Уникальных</div>
          <div className={css.cardValue}>{summary.unique_visitors.toLocaleString("ru-RU")}</div>
          <div className={css.cardSub}>уник. посетителей</div>
        </div>
        <div className={css.card}>
          <div className={css.cardLabel}>Заказы</div>
          <div className={`${css.cardValue} ${css.cardValueMuted}`}>
            {summary.orders > 0 ? summary.orders : "—"}
          </div>
          <div className={css.cardSub}>из attribution</div>
        </div>
        <div className={css.card}>
          <div className={css.cardLabel}>Конверсия</div>
          <div className={`${css.cardValue} ${css.cardValueMuted}`}>
            {summary.conversion_rate > 0 ? `${summary.conversion_rate}%` : "—"}
          </div>
          <div className={css.cardSub}>клики → заказы</div>
        </div>
      </div>

      {/* Daily chart */}
      <div className={css.section}>
        <div className={css.sectionHeader}>
          <span className={css.sectionTitle}>Клики по дням</span>
          <span className={css.sectionSub}>{days} дней</span>
        </div>
        {daily.length > 0 ? (
          <BarChart data={daily} />
        ) : (
          <div className={css.emptyMini}>Нет данных за период</div>
        )}
      </div>

      {/* Two columns: funnel + devices */}
      <div className={css.twoCol}>
        {/* Sales funnel */}
        <div className={css.section}>
          <div className={css.sectionHeader}>
            <span className={css.sectionTitle}>Воронка продаж</span>
            <span className={css.sectionSub}>многоканальность</span>
          </div>
          <Funnel stages={funnel} />
        </div>

        {/* Device breakdown */}
        <div className={css.section}>
          <div className={css.sectionHeader}>
            <span className={css.sectionTitle}>Устройства</span>
          </div>
          <DevicePie devices={devices} />
        </div>
      </div>

      {/* Multi-channel source table */}
      <div className={css.section}>
        <div className={css.sectionHeader}>
          <span className={css.sectionTitle}>Источники трафика</span>
          <span className={css.sectionSub}>многоканальный анализ</span>
        </div>
        <SourceTable sources={sources} total={summary.total_clicks} />
      </div>
    </div>
  );
}
