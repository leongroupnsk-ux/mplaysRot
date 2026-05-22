import { Navigate, Outlet } from "react-router-dom";
import { useAdminAuthStore } from "../../store/adminAuth";

export default function AdminProtectedRoute() {
  const { isAuthenticated } = useAdminAuthStore();
  if (!isAuthenticated) {
    return <Navigate to="/admin/login" replace />;
  }
  return <Outlet />;
}
