import { useEffect } from "react";
import { Navigate, Outlet } from "react-router-dom";
import { useAuthStore } from "../../store/auth";
import { fetchMe } from "../../api/auth";

export default function ProtectedRoute() {
  const { isAuthenticated, user, setUser } = useAuthStore();

  // Lazy-load user profile once per session
  useEffect(() => {
    if (isAuthenticated && !user) {
      fetchMe().then(setUser).catch(() => {});
    }
  }, [isAuthenticated, user, setUser]);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}
