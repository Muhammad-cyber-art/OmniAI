import { useAuth } from '../context/AuthContext';
import AdminDashboard   from '../components/AdminDashboard';
import MentorDashboard  from '../components/MentorDashboard';
import StudentDashboard from '../components/StudentDashboard';

/**
 * DashboardPage — Role-based dashboard router.
 *
 * Roles (from backend apps/users/models.py):
 *   ADMIN      → AdminDashboard   (full admin panel)
 *   INSTRUCTOR → MentorDashboard  (group & course management)
 *   STUDENT    → StudentDashboard (learning & simulations)
 *   RECRUITER  → StudentDashboard (fallback; recruiter view not yet built)
 *
 * The role is stored in user.role (uppercase string).
 * Mapped aliases (e.g., 'mentor', 'student') are also supported for
 * backward compatibility.
 */
export default function DashboardPage() {
  const { user, logout } = useAuth();

  const role = (user?.role || '').toUpperCase();

  if (role === 'ADMIN') {
    return <AdminDashboard  user={user} onLogout={logout} />;
  }

  if (role === 'INSTRUCTOR' || role === 'MENTOR') {
    return <MentorDashboard user={user} onLogout={logout} />;
  }

  // STUDENT, RECRUITER, or any unrecognized role → Student UI
  return <StudentDashboard user={user} onLogout={logout} />;
}
