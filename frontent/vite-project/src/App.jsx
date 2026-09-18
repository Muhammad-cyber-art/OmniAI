import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import './index.css';

import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';

// Landing page sections
import Navbar       from './components/Navbar';
import Hero         from './components/Hero';
import HowItWorks   from './components/HowItWorks';
import Features     from './components/Features';
import Testimonials from './components/Testimonials';
import Pricing      from './components/Pricing';
import Footer       from './components/Footer';

// Auth pages
import LoginPage    from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';

// Dashboard & Simulation pages
import DashboardPage  from './pages/DashboardPage';
import SimulationPage from './pages/SimulationPage';

/* ── Landing Page (assembled) ── */
function LandingPage() {
  return (
    <div className="min-h-screen bg-white">
      <Navbar />
      <main>
        <Hero />
        <HowItWorks />
        <Features />
        <Testimonials />
        <Pricing />
      </main>
      <Footer />
    </div>
  );
}

/* ── Root App ── */
export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public routes */}
          <Route path="/"         element={<LandingPage />} />
          <Route path="/login"    element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Main dashboard (role-router: ADMIN → AdminDashboard, INSTRUCTOR → MentorDashboard, STUDENT → StudentDashboard) */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            }
          />

          {/* AI Simulation Lab route */}
          <Route
            path="/simulation"
            element={
              <ProtectedRoute>
                <SimulationPage />
              </ProtectedRoute>
            }
          />

          {/* Admin-only shortcut route */}
          <Route
            path="/admin/*"
            element={
              <ProtectedRoute roles={['ADMIN']}>
                <DashboardPage />
              </ProtectedRoute>
            }
          />

          {/* Mentor-only shortcut route */}
          <Route
            path="/mentor/*"
            element={
              <ProtectedRoute roles={['INSTRUCTOR', 'ADMIN']}>
                <DashboardPage />
              </ProtectedRoute>
            }
          />

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
