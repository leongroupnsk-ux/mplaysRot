import { useOverview } from "../hooks/useAnalytics";
import MetricCard from "../components/shared/MetricCard";
import DateRangePicker from "../components/shared/DateRangePicker";
import SpendRevenueChart from "../components/dashboard/SpendRevenueChart";
import TopCreativesTable from "../components/dashboard/TopCreativesTable";
import StoresWidget from "../components/dashboard/StoresWidget";
import GeoMap from "../components/dashboard/GeoMap";
import styles from "./Page.module.css";

function pctDelta(current: number, prev?: number): number | undefined {
  if (!prev || prev === 0) return undefined;
  return ((current - prev) / prev) * 100;
}

export default function DashboardPage() {
  const { data } = useOverview();
  const p = data?.previous_period;

  return (
    <div className={styles.page}>
      <div className={styles.toolbar}>
        <h1 className={styles.heading}>Обзор</h1>
        <DateRangePicker />
      </div>

      <div className={styles.metrics}>
        <MetricCard
          label="ROAS"
          value={data ? data.roas.toFixed(2) : "—"}
          suffix="x"
          delta={pctDelta(data?.roas ?? 0, p?.roas)}
          highlight
        />
        <MetricCard
          label="Доход"
          value={data ? data.total_revenue.toLocaleString("ru") : "—"}
          suffix="₽"
          delta={pctDelta(data?.total_revenue ?? 0, p?.total_revenue)}
        />
        <MetricCard
          label="Расходы"
          value={data ? data.total_spend.toLocaleString("ru") : "—"}
          suffix="₽"
          delta={pctDelta(data?.total_spend ?? 0, p?.total_spend)}
        />
        <MetricCard
          label="Заказы"
          value={data ? data.attributed_orders.toLocaleString("ru") : "—"}
          delta={pctDelta(data?.attributed_orders ?? 0, p?.attributed_orders)}
        />
        <MetricCard
          label="Ср. чек"
          value={data ? data.avg_order_value.toLocaleString("ru") : "—"}
          suffix="₽"
          delta={pctDelta(data?.avg_order_value ?? 0, p?.avg_order_value)}
        />
        <MetricCard
          label="Конверсия"
          value={data ? (data.click_to_order_rate * 100).toFixed(2) : "—"}
          suffix="%"
          delta={pctDelta(data?.click_to_order_rate ?? 0, p?.click_to_order_rate)}
        />
      </div>

      <StoresWidget />
      <SpendRevenueChart />
      <div className={styles.grid2}>
        <GeoMap />
        <TopCreativesTable />
      </div>
    </div>
  );
}
