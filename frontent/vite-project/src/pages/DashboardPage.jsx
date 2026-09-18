import { useAuth } from '../context/AuthContext';
import { Link, useNavigate } from 'react-router-dom';

export default function DashboardPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate('/login');
  }

  return (
    <div className="min-h-screen bg-[#F4F6F8]">
      {/* Top bar */}
      <header className="bg-white border-b border-[#E5E9F0] sticky top-0 z-40 shadow-sm">
        <div className="max-w-[1200px] mx-auto px-8 h-16 flex items-center justify-between gap-4">
          <Link to="/" className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#0056D6] to-[#0041A8] flex items-center justify-center">
              <svg width="16" height="16" viewBox="0 0 20 20" fill="none">
                <circle cx="10" cy="10" r="4" fill="white" opacity="0.95" />
                <circle cx="10" cy="10" r="8" stroke="white" strokeWidth="1.5" opacity="0.35" />
              </svg>
            </div>
            <span className="font-display font-bold text-[17px] text-[#161C2D]">ChronosAI</span>
          </Link>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-2 bg-[#F4F6F8] rounded-lg">
              <div className="w-7 h-7 rounded-full bg-[#0056D6] flex items-center justify-center text-white text-[11px] font-bold">
                {user?.first_name?.[0] || user?.email?.[0]?.toUpperCase() || 'U'}
              </div>
              <span className="text-[14px] font-semibold text-[#161C2D]">
                {user?.first_name || user?.email || 'Foydalanuvchi'}
              </span>
            </div>
            <button
              id="dashboard-logout-btn"
              onClick={handleLogout}
              className="text-sm font-semibold text-[#6B7280] hover:text-red-500 px-3 py-2 rounded-lg hover:bg-red-50 transition-all"
            >
              Chiqish
            </button>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-[1200px] mx-auto px-8 py-12">
        <div className="mb-10">
          <h1 className="font-display font-extrabold text-[32px] text-[#161C2D] tracking-tight">
            Xush kelibsiz, {user?.first_name || 'Foydalanuvchi'}! 👋
          </h1>
          <p className="text-[#6B7280] mt-2 text-[16px]">
            Rol: <span className="font-semibold text-[#0056D6] capitalize">{user?.role || 'student'}</span>
          </p>
        </div>

        {/* Quick cards */}
        <div className="grid md:grid-cols-3 gap-6">
          {[
            { icon: '🎮', title: 'Simulyatsiyalar', desc: "Jonli AI simulyatsiyalarini boshlang", href: '#', color: 'from-blue-50 to-blue-100/50', accent: 'text-[#0056D6] bg-[#EBF2FF]' },
            { icon: '📚', title: 'Kurslar', desc: "Mavjud kurslarni ko'ring va davom eting", href: '#', color: 'from-emerald-50 to-emerald-100/50', accent: 'text-emerald-600 bg-emerald-50' },
            { icon: '👥', title: 'Guruhlar', desc: "Guruhingizni boshqaring yoki qo'shiling", href: '#', color: 'from-violet-50 to-violet-100/50', accent: 'text-violet-600 bg-violet-50' },
          ].map(({ icon, title, desc, href, color, accent }) => (
            <a
              key={title}
              href={href}
              className={`group p-6 rounded-2xl bg-gradient-to-br ${color} border border-white hover:shadow-[0_12px_36px_rgba(0,0,0,0.10)] hover:-translate-y-1 transition-all duration-300`}
            >
              <div className={`w-12 h-12 rounded-xl ${accent} text-2xl flex items-center justify-center mb-4 shadow-sm group-hover:scale-110 transition-transform`}>
                {icon}
              </div>
              <h3 className="font-display font-bold text-[#161C2D] text-[17px] mb-1">{title}</h3>
              <p className="text-[13px] text-[#6B7280]">{desc}</p>
            </a>
          ))}
        </div>

        {/* Coming soon notice */}
        <div className="mt-10 p-6 rounded-2xl bg-gradient-to-r from-[#0056D6] to-[#0081FF] text-white text-center">
          <p className="font-display font-bold text-[18px] mb-1">Dashboard tez orada to'liq bo'ladi 🚀</p>
          <p className="text-white/70 text-[14px]">Frontend jamoasi ushbu bo'limni faol ishlab chiqmoqda.</p>
        </div>
      </main>
    </div>
  );
}
