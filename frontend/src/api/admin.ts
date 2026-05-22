import axios from "axios";

const adminApi = axios.create({
  baseURL: "/api/admin",
  headers: { "Content-Type": "application/json" },
});

adminApi.interceptors.request.use((config) => {
  const token = localStorage.getItem("admin_access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

adminApi.interceptors.response.use(
  (r) => r,
  (error) => {
    if (error.response?.status === 401 || error.response?.status === 403) {
      localStorage.removeItem("admin_access_token");
      window.location.href = "/admin/login";
    }
    return Promise.reject(error);
  }
);

export interface AdminUser {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  is_stopped: boolean;
  totp_enabled: boolean;
  plan_id: string | null;
  plan_name: string | null;
  created_at: string;
  updated_at: string;
}

export interface AdminStats {
  total_users: number;
  active_users: number;
  admin_users: number;
  users_last_30d: number;
}

export async function adminLogin(email: string, password: string, totp_code: string | null): Promise<string> {
  const body: Record<string, unknown> = { email, password };
  if (totp_code) body.totp_code = totp_code;
  const { data } = await adminApi.post<{ access_token: string }>("/auth/login", body);
  return data.access_token;
}

export async function fetchAdminStats(): Promise<AdminStats> {
  const { data } = await adminApi.get<AdminStats>("/stats");
  return data;
}

export async function fetchAdminUsers(params?: {
  offset?: number;
  limit?: number;
  search?: string;
}): Promise<AdminUser[]> {
  const { data } = await adminApi.get<AdminUser[]>("/users", { params });
  return data;
}

export async function fetchAdminUser(id: string): Promise<AdminUser> {
  const { data } = await adminApi.get<AdminUser>(`/users/${id}`);
  return data;
}

export async function patchAdminUser(
  id: string,
  body: {
    role?: string;
    is_active?: boolean;
    is_stopped?: boolean;
    full_name?: string;
    email?: string;
    plan_id?: string | null;
  }
): Promise<AdminUser> {
  const { data } = await adminApi.patch<AdminUser>(`/users/${id}`, body);
  return data;
}

export async function changeUserPassword(
  id: string,
  newPassword: string
): Promise<{ message: string }> {
  const { data } = await adminApi.post<{ message: string }>(
    `/users/${id}/change-password`,
    { new_password: newPassword }
  );
  return data;
}

export async function toggleUserStop(
  id: string,
  isStopped: boolean
): Promise<AdminUser> {
  const { data } = await adminApi.patch<AdminUser>(`/users/${id}`, {
    is_stopped: isStopped,
  });
  return data;
}

export interface BillingPlan {
  id: string;
  name: string;
  price: number;
  features: string[];
  created_at: string;
}

export async function fetchBillingPlans(): Promise<BillingPlan[]> {
  const { data } = await adminApi.get<BillingPlan[]>("/billing/plans");
  return data;
}

export async function assignUserPlan(
  userId: string,
  planId: string
): Promise<AdminUser> {
  const { data } = await adminApi.patch<AdminUser>(`/users/${userId}`, {
    plan_id: planId,
  });
  return data;
}

export async function removeUserPlan(userId: string): Promise<AdminUser> {
  const { data } = await adminApi.patch<AdminUser>(`/users/${userId}`, {
    plan_id: null,
  });
  return data;
}

export async function fetchTotpSetup(): Promise<{ totp_secret: string; totp_uri: string; message: string }> {
  const { data } = await adminApi.get("/auth/totp-setup");
  return data;
}

// ── Platform settings ─────────────────────────────────────────────────────────

export interface PlatformSettingMeta {
  set: boolean;
  updated_at: string | null;
  updated_by: string | null;
}

export async function fetchPlatformSettings(): Promise<Record<string, PlatformSettingMeta>> {
  const { data } = await adminApi.get("/settings/platform");
  return data;
}

export async function setPlatformSetting(key: string, value: string): Promise<void> {
  await adminApi.put(`/settings/platform/${key}`, { value });
}

export async function deletePlatformSetting(key: string): Promise<void> {
  await adminApi.delete(`/settings/platform/${key}`);
}

export default adminApi;
