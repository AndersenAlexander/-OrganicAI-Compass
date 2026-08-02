import { Navigate, Outlet } from "react-router-dom";
import { LoadingState } from "../components/shared/LoadingState";
import { useAuth } from "../context/AuthContext";

export function ProtectedRoute() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) return <LoadingState label="Checking your session..." />;
  if (!isAuthenticated) return <Navigate to="/login" replace />;

  return <Outlet />;
}
