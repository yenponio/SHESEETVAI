import AppShell from "./AppShell";
import { Navigate } from "react-router-dom";

function ProtectedRoute({ children }) {
  const isLoggedIn = localStorage.getItem("osaLoggedIn") === "true";

  if (!isLoggedIn) {
    return <Navigate to="/osa" replace />;
  }

  return <AppShell>{children}</AppShell>;
}

export default ProtectedRoute;