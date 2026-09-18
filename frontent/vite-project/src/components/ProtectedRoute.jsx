import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

/**
 * ProtectedRoute — wraps pages that require authentication.
 * If not authenticated → redirect to /login (preserving intended destination).
 * While session is loading → show full-screen spinner.
 *
 * @param {string[]} roles - Optional whitelist of allowed roles.
 *   Comparison is case-insensitive (handles both 'ADMIN' and 'admin').
 */
export default function ProtectedRoute({ children, roles = [] }) {
  const { isAuthenticated, isLoading, user } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white">
        <div className="flex flex-col items-center gap-4">
          <div className="w-10 h-10 border-[3px] border-[#E5E9F0] border-t-[#0056D6] rounded-full animate-spin" />
          <p className="text-sm text-[#6B7280] font-medium">Yuklanmoqda...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Role-based guard (case-insensitive)
  if (roles.length > 0 && user?.role) {
    const userRole = user.role.toUpperCase();
    const allowed  = roles.map(r => r.toUpperCase());
    if (!allowed.includes(userRole)) {
      return <Navigate to="/dashboard" replace />;
    }
  }

  return children;
}
