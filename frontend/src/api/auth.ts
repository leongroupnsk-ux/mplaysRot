import api from "./client";

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
}

export interface Me {
  id: string;
  email: string;
  full_name: string | null;
  role: string;
  created_at: string;
}

export const login = (email: string, password: string) =>
  api.post<AuthTokens>("/auth/login", { email, password }).then((r) => r.data);

export const register = (email: string, password: string, full_name?: string) =>
  api.post<AuthTokens>("/auth/register", { email, password, full_name }).then((r) => r.data);

export const fetchMe = () =>
  api.get<Me>("/auth/me").then((r) => r.data);

export const refreshTokens = (refresh_token: string) =>
  api.post<AuthTokens>("/auth/refresh", { refresh_token }).then((r) => r.data);
