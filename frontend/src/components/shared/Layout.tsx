import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import NotificationPanel from "./NotificationPanel";
import { useNotificationsWS } from "../../hooks/useNotificationsWS";
import styles from "./Layout.module.css";

export default function Layout() {
  useNotificationsWS();

  return (
    <div className={styles.root}>
      <Sidebar />
      <div className={styles.main}>
        <Outlet />
      </div>
      <NotificationPanel />
    </div>
  );
}
