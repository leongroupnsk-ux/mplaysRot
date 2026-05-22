import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAdminAuthStore } from "../../store/adminAuth";
import styles from "./AdminLayout.module.css";

const NAV = [
  { to: "/admin", label: "Обзор", icon: "◈", end: true },
  { to: "/admin/users", label: "Пользователи", icon: "◉" },
  { to: "/admin/billing", label: "Биллинг", icon: "◇" },
  { to: "/admin/segments", label: "Сегменты", icon: "▣" },
  { to: "/admin/audit", label: "Аудит", icon: "◐" },
  { to: "/admin/blog",     label: "Блог",        icon: "✎" },
  { to: "/admin/domains",  label: "Домены",      icon: "🌐" },
  { to: "/admin/settings", label: "Настройки", icon: "◎" },
];

export default function AdminLayout() {
  const navigate = useNavigate();
  const { logout } = useAdminAuthStore();

  const handleLogout = () => {
    logout();
    navigate("/admin/login", { replace: true });
  };

  return (
    <div className={styles.shell}>
      <aside className={styles.sidebar}>
        <div className={styles.brand}>
          <div className={styles.brandMark}>MP</div>
          <span className={styles.brandText}>MPlays</span>
          <span className={styles.brandBadge}>Admin</span>
        </div>

        <nav className={styles.nav} aria-label="Admin navigation">
          {NAV.map(({ to, label, icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `${styles.navItem} ${isActive ? styles.navItemActive : ""}`
              }
            >
              <span className={styles.navIcon} aria-hidden>{icon}</span>
              {label}
            </NavLink>
          ))}
        </nav>

        <button className={styles.logoutBtn} onClick={handleLogout}>
          <span aria-hidden>⎋</span> Выйти
        </button>
      </aside>

      <main className={styles.main}>
        <Outlet />
      </main>
    </div>
  );
}
