import axios from "axios";

const api = axios.create({
  baseURL: "/api/v1",
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

let _refreshing: Promise<string> | null = null;

api.interceptors.response.use(
  (r) => r,
  async (error) => {
    const original = error.config;

    if (error.response?.status !== 401 || original._retry) {
      return Promise.reject(error);
    }

    const refresh = localStorage.getItem("refresh_token");
    if (!refresh) {
      _redirectLogin();
      return Promise.reject(error);
    }

    // Deduplicate concurrent refresh calls
    if (!_refreshing) {
      _refreshing = axios
        .post<{ access_token: string; refresh_token: string }>("/api/v1/auth/refresh", {
          refresh_token: refresh,
        })
        .then((res) => {
          localStorage.setItem("access_token", res.data.access_token);
          localStorage.setItem("refresh_token", res.data.refresh_token);
          return res.data.access_token;
        })
        .catch(() => {
          _redirectLogin();
          return Promise.reject(new Error("Session expired"));
        })
        .finally(() => { _refreshing = null; });
    }

    try {
      const newToken = await _refreshing;
      original._retry = true;
      original.headers.Authorization = `Bearer ${newToken}`;
      return api(original);
    } catch {
      return Promise.reject(error);
    }
  }
);

function _redirectLogin() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  window.location.href = "/login";
}

export default api;
