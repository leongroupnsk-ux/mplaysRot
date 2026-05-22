import { useTopCreatives } from "../../hooks/useAnalytics";
import styles from "./TopCreativesTable.module.css";

const PLATFORM_LABELS: Record<string, string> = {
  yandex_direct: "Яндекс", vk_ads: "VK Ads", vk_blogger: "VK Blogger",
  telegram_ads: "Telegram", messenger_max: "MAX",
};

export default function TopCreativesTable() {
  const { data = [], isLoading } = useTopCreatives(10);

  return (
    <div className={styles.card}>
      <h3 className={styles.title}>Топ объявлений по ROAS</h3>
      <table className={styles.table}>
        <thead>
          <tr>
            <th>Объявление</th>
            <th>Площадка</th>
            <th>Расходы</th>
            <th>Клики</th>
            <th>Заказы</th>
            <th>ROAS</th>
          </tr>
        </thead>
        <tbody>
          {isLoading
            ? Array.from({ length: 5 }).map((_, i) => (
                <tr key={i}><td colSpan={6}><div className={styles.skeletonRow} /></td></tr>
              ))
            : data.map((row) => (
                <tr key={row.external_ad_id}>
                  <td className={styles.adName} title={row.ad_name}>{row.ad_name || row.external_ad_id}</td>
                  <td>{PLATFORM_LABELS[row.ad_platform] ?? row.ad_platform}</td>
                  <td>{row.spend.toLocaleString("ru")} ₽</td>
                  <td>{row.clicks.toLocaleString("ru")}</td>
                  <td>{row.orders.toLocaleString("ru")}</td>
                  <td className={styles.roas}>{row.roas.toFixed(2)}x</td>
                </tr>
              ))}
        </tbody>
      </table>
    </div>
  );
}
