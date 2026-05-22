import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchNotifications, markAllRead, markRead } from "../../api/notifications";
import type { Notification } from "../../api/types";
import styles from "./NotificationPanel.module.css";

const TYPE_LABEL: Record<Notification["type"], string> = {
  anomaly_detected: "Аномалия",
  segment_ready: "Сегмент готов",
  attribution_complete: "Атрибуция",
  low_roas: "Низкий ROAS",
  budget_depleted: "Бюджет исчерпан",
};

export default function NotificationPanel() {
  const [open, setOpen] = useState(false);
  const qc = useQueryClient();

  const { data: notifications = [] } = useQuery({
    queryKey: ["notifications"],
    queryFn: () => fetchNotifications(),
    refetchInterval: 30_000,
  });

  const unread = notifications.filter((n) => !n.is_read).length;

  const readAll = useMutation({
    mutationFn: markAllRead,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["notifications"] }),
  });

  const readOne = useMutation({
    mutationFn: (id: string) => markRead(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["notifications"] }),
  });

  return (
    <>
      <button className={styles.bell} onClick={() => setOpen((v) => !v)}>
        🔔
        {unread > 0 && <span className={styles.badge}>{unread}</span>}
      </button>

      {open && (
        <div className={styles.panel}>
          <div className={styles.header}>
            <span>Уведомления</span>
            {unread > 0 && (
              <button className={styles.readAll} onClick={() => readAll.mutate()}>
                Прочитать все
              </button>
            )}
          </div>

          <div className={styles.list}>
            {notifications.length === 0 && (
              <p className={styles.empty}>Нет уведомлений</p>
            )}
            {notifications.map((n) => (
              <div
                key={n.id}
                className={[styles.item, n.is_read ? "" : styles.unread].join(" ")}
                onClick={() => !n.is_read && readOne.mutate(n.id)}
              >
                <span className={styles.type}>{TYPE_LABEL[n.type]}</span>
                <p className={styles.title}>{n.title}</p>
                <p className={styles.body}>{n.body}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  );
}
