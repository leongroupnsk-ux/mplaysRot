import { NavLink, useNavigate } from "react-router-dom";
import { useAuthStore } from "../../store/auth";
import { useTheme } from "../../hooks/useTheme";
import styles from "./Sidebar.module.css";

const NAV_MAIN = [
  { to: "/dashboard", label: "Обзор" },
  { to: "/canvas", label: "🎨 Canvas" },
  { to: "/campaigns", label: "Кампании" },
  { to: "/attribution", label: "Атрибуция" },
  { to: "/audience", label: "Аудитории" },
  { to: "/links", label: "Диплинки" },
  { to: "/logistics", label: "Logistics Tracker" },
  { to: "/reports", label: "Отчёты" },
];

const NAV_SETTINGS = [
  { to: "/settings/integrations", label: "Интеграции" },
  { to: "/settings/domains", label: "Домены" },
  { to: "/settings/profile", label: "Профиль" },
];

export default function Sidebar() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const { theme, toggle } = useTheme();

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  const navLink = (to: string, label: string) => (
    <NavLink
      key={to}
      to={to}
      className={({ isActive }) =>
        [styles.link, isActive ? styles.active : ""].join(" ")
      }
    >
      {label}
    </NavLink>
  );

  return (
    <aside className={styles.sidebar}>
      <div className={styles.logo}>
        <span className={styles.logoMark}>MP</span>
        <span className={styles.logoText}>MPlays</span>
      </div>

      <nav className={styles.nav}>
        {NAV_MAIN.map(({ to, label }) => navLink(to, label))}

        <div className={styles.navDivider} />
        <span className={styles.navGroup}>Настройки</span>
        {NAV_SETTINGS.map(({ to, label }) => navLink(to, label))}
      </nav>

      <div className={styles.userRow}>
        <div className={styles.userInfo}>
          <div className={styles.userName}>{user?.full_name ?? user?.email ?? "Профиль"}</div>
          {user?.full_name && <div className={styles.userEmail}>{user.email}</div>}
        </div>
        <button
          className={styles.themeBtn}
          onClick={toggle}
          title={theme === "dark" ? "Светлая тема" : "Тёмная тема"}
          type="button"
        >
          {theme === "dark" ? "☀️" : "🌙"}
        </button>
        <button className={styles.logoutBtn} onClick={handleLogout} title="Выйти" type="button">
          ↩
        </button>
      </div>
    </aside>
  );
}
