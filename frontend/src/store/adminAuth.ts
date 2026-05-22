import { create } from "zustand";
import { persist } from "zustand/middleware";

interface AdminAuthState {
  token: string | null;
  setToken: (token: string) => void;
  logout: () => void;
  isAuthenticated: boolean;
}

export const useAdminAuthStore = create<AdminAuthState>()(
  persist(
    (set) => ({
      token: null,
      isAuthenticated: false,
      setToken: (token) => {
        localStorage.setItem("admin_access_token", token);
        set({ token, isAuthenticated: true });
      },
      logout: () => {
        localStorage.removeItem("admin_access_token");
        set({ token: null, isAuthenticated: false });
      },
    }),
    { name: "admin-auth" }
  )
);
