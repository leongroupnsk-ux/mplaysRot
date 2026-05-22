import { useEffect, useState } from "react";
import { fetchAdminStats, type AdminStats } from "../../api/admin";
import styles from "./AdminDashboardPage.module.css";

export default function AdminDashboardPage() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAdminStats()
      .then(setStats)
      .catch(() => setError("Не удалось загрузить статистику."));
  }, []);

  const tiles = stats
    ? [
        { label: "Всего пользователей", value: stats.total_users.toLocaleString("ru") },
        { label: "Активных пользователей", value: stats.active_users.toLocaleString("ru") },
        { label: "Новых за 30 дней", value: stats.users_last_30d.toLocaleString("ru") },
        { label: "Администраторов", value: stats.admin_users.toLocaleString("ru") },
      ]
    : [];

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.title}>Обзор платформы</h1>
        <p className={styles.subtitle}>Ключевые показатели в реальном времени</p>
      </header>

      {error && <p className={styles.error}>{error}</p>}

      {!stats && !error && (
        <div className={styles.grid}>
          {[1, 2, 3, 4].map((i) => <div key={i} className={`${styles.tile} ${styles.tileSkeleton}`} />)}
        </div>
      )}

      {stats && (
        <div className={styles.grid}>
          {tiles.map((t) => (
            <div key={t.label} className={styles.tile}>
              <p className={styles.tileLabel}>{t.label}</p>
              <p className={styles.tileValue}>{t.value}</p>
            </div>
          ))}
        </div>
      )}

      <section className={styles.infoSection}>
        <h2 className={styles.sectionTitle}>Быстрые действия</h2>
        <div className={styles.quickActions}>
          <a href="/admin/users" className={styles.actionCard}>
            <span className={styles.actionIcon}>◉</span>
            <div>
              <p className={styles.actionTitle}>Управление пользователями</p>
              <p className={styles.actionDesc}>Просмотр, блокировка, смена ролей</p>
            </div>
          </a>
          <a href="/admin/settings" className={styles.actionCard}>
            <span className={styles.actionIcon}>◎</span>
            <div>
              <p className={styles.actionTitle}>Настройки</p>
              <p className={styles.actionDesc}>TOTP, системные параметры</p>
            </div>
          </a>
        </div>
      </section>
    </div>
  );
}
