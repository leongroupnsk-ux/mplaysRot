import api from "./client";
import type { Notification } from "./types";

export const fetchNotifications = (params?: { unread_only?: boolean }) =>
  api.get<{ items: Notification[]; total: number }>("/notifications", { params })
    .then((r) => r.data.items ?? []);

export const markAllRead = () => api.post("/notifications/read-all");

export const markRead = (id: string) => api.post(`/notifications/${id}/read`);
