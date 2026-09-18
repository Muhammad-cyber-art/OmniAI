import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { simulationApi, curriculumApi } from '../services/api';
import AppleSticker from './AppleSticker';

function StatCard({ icon, label, value, color }) {
  return (
    <div className={`p-5 rounded-2xl bg-gradient-to-br ${color} border border-white hover:shadow-[0_8px_24px_rgba(0,0,0,0.08)] hover:-translate-y-0.5 transition-all duration-300`}>
      <div className="w-10 h-10 rounded-xl bg-white/70 flex items-center justify-center mb-3">
        <AppleSticker symbol={icon} size={22} />
      </div>
      <div className="font-display font-extrabold text-[26px] text-[#161C2D] leading-tight">{value ?? '—'}</div>
      <div className="text-[12px] font-semibold text-[#6B7280] mt-0.5">{label}</div>
    </div>
  );
}

export default function StudentDashboard({ user, onLogout }) {
  const navigate = useNavigate();
  const [courses,   setCourses]   = useState([]);
  const [sessions,  setSessions]  = useState([]);
  const [loading,   setLoading]   = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const [cRes, sRes] = await Promise.allSettled([
          curriculumApi.getCourses(),
          simulationApi.getMySessions(),
        ]);
        if (cRes.status === 'fulfilled') {
          const d = cRes.value.data;
          setCourses(Array.isArray(d) ? d.slice(0, 6) : (d?.results || []).slice(0, 6));
        }
        if (sRes.status === 'fulfilled') {
          const d = sRes.value.data;
          setSessions(Array.isArray(d) ? d.slice(0, 5) : (d?.results || []).slice(0, 5));
        }
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  async function handleLogout() {
    await onLogout();
    navigate('/login');
  }

  const profile = user?.profile || {};

  return (
    <div className="min-h-screen bg-[#F4F6F8]">
      {/* Header */}
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
              <div className="w-7 h-7 rounded-full bg-gradient-to-br from-[#0056D6] to-[#0041A8] flex items-center justify-center text-white text-[11px] font-bold">
                {(user?.first_name?.[0] || user?.email?.[0] || 'T').toUpperCase()}
              </div>
              <span className="text-[14px] font-semibold text-[#161C2D] hidden md:inline">
                {user?.first_name || 'Talaba'}
              </span>
            </div>
            <button
              id="student-logout-btn"
              onClick={handleLogout}
              className="text-sm font-semibold text-[#6B7280] hover:text-red-500 px-3 py-2 rounded-lg hover:bg-red-50 transition-all"
            >
              Chiqish
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-[1200px] mx-auto px-8 py-10 flex flex-col gap-10">
        {/* Welcome */}
        <div className="flex items-start justify-between flex-wrap gap-4">
          <div>
            <h1 className="font-display font-extrabold text-[30px] text-[#161C2D] tracking-tight flex items-center gap-2">
              Salom, {user?.first_name || 'Talaba'}! <AppleSticker symbol="👋" size={30} />
            </h1>
            <p className="text-[#6B7280] mt-1 text-[15px]">Kurslaringizni davom ettirib, simulyatsiyalarda ishtirok eting.</p>
          </div>
          {/* Streak */}
          {profile.current_streak_days > 0 && (
            <div className="flex items-center gap-2 px-4 py-2 bg-amber-50 border border-amber-100 rounded-xl">
              <AppleSticker symbol="🔥" size={20} />
              <span className="text-[14px] font-bold text-amber-700">{profile.current_streak_days} kunlik seriya!</span>
            </div>
          )}
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard
            icon="🎮"
            label="Simulyatsiyalar"
            value={loading ? '...' : (profile.total_simulations_completed ?? sessions.length)}
            color="from-blue-50 to-blue-100/50"
          />
          <StatCard
            icon="🏆"
            label="Tanga"
            value={loading ? '...' : (profile.total_coins_earned ?? '—')}
            color="from-amber-50 to-amber-100/50"
          />
          <StatCard
            icon="📚"
            label="Mavjud kurslar"
            value={loading ? '...' : courses.length}
            color="from-emerald-50 to-emerald-100/50"
          />
          <StatCard
            icon="🔥"
            label="Uzun seriya"
            value={loading ? '...' : (profile.longest_streak_days ?? '—')}
            color="from-violet-50 to-violet-100/50"
          />
        </div>

        {/* Available Courses */}
        <section>
          <div className="flex items-center justify-between mb-5">
            <h2 className="font-display font-bold text-[20px] text-[#161C2D] flex items-center gap-2">
              <AppleSticker symbol="📚" size={22} />
              Mavjud kurslar
            </h2>
          </div>

          {loading ? (
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 animate-pulse">
              {[1,2,3].map(i => <div key={i} className="h-40 rounded-2xl bg-[#F4F6F8]" />)}
            </div>
          ) : courses.length === 0 ? (
            <div className="bg-white border border-[#E5E9F0] rounded-2xl p-10 text-center">
              <AppleSticker symbol="📚" size={40} className="mx-auto mb-3" />
              <p className="font-semibold text-[#161C2D]">Hali kurslar mavjud emas</p>
              <p className="text-[13px] text-[#6B7280] mt-1">Mentor kurslar qo'shganda bu yerda ko'rinadi</p>
            </div>
          ) : (
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {courses.map(c => {
                const DIFF_COLOR = {
                  BEGINNER:     'bg-emerald-100 text-emerald-700',
                  INTERMEDIATE: 'bg-amber-100 text-amber-700',
                  ADVANCED:     'bg-red-100 text-red-700',
                };
                const DIFF_LABEL = {
                  BEGINNER:     "Boshlang'ich",
                  INTERMEDIATE: "O'rta",
                  ADVANCED:     "Ilg'or",
                };
                return (
                  <div
                    key={c.id}
                    className="bg-white border border-[#E5E9F0] rounded-2xl p-5 flex flex-col gap-3 hover:shadow-[0_8px_28px_rgba(0,0,0,0.08)] hover:-translate-y-0.5 transition-all duration-300"
                  >
                    <div className="flex items-start gap-3">
                      <div className="w-11 h-11 rounded-xl bg-[#EBF2FF] flex items-center justify-center shrink-0">
                        <AppleSticker symbol="📚" size={22} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className="font-display font-bold text-[#161C2D] text-[14px] leading-tight line-clamp-2">{c.title}</h3>
                        <p className="text-[11px] text-[#9CA3AF] mt-0.5">{c.instructor_name || 'Mentor'}</p>
                      </div>
                    </div>
                    <p className="text-[12px] text-[#6B7280] line-clamp-2 flex-1">{c.description || 'Tavsif mavjud emas'}</p>
                    <div className="flex items-center justify-between">
                      <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${DIFF_COLOR[c.difficulty] || 'bg-gray-100 text-gray-600'}`}>
                        {DIFF_LABEL[c.difficulty] || c.difficulty}
                      </span>
                      <button className="text-[12px] font-semibold text-[#0056D6] hover:underline">
                        Ko'rish →
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </section>

        {/* My Simulation Sessions */}
        <section>
          <div className="flex items-center justify-between mb-5">
            <h2 className="font-display font-bold text-[20px] text-[#161C2D] flex items-center gap-2">
              <AppleSticker symbol="🎮" size={22} />
              Mening simulyatsiyalarim
            </h2>
          </div>

          {loading ? (
            <div className="bg-white border border-[#E5E9F0] rounded-2xl h-24 animate-pulse" />
          ) : sessions.length === 0 ? (
            <div className="bg-white border border-[#E5E9F0] rounded-2xl p-10 text-center">
              <AppleSticker symbol="🎮" size={40} className="mx-auto mb-3" />
              <p className="font-semibold text-[#161C2D]">Hali simulyatsiya o'tkazilmagan</p>
              <p className="text-[13px] text-[#6B7280] mt-1">Birinchi simulyatsiyangizni boshlang!</p>
              <button className="mt-4 px-6 py-2.5 bg-[#0056D6] text-white text-[14px] font-semibold rounded-xl hover:bg-[#0047b3] transition-all">
                Simulyatsiya boshlash
              </button>
            </div>
          ) : (
            <div className="bg-white border border-[#E5E9F0] rounded-2xl overflow-hidden">
              {sessions.map((s) => (
                <div
                  key={s.id}
                  className="flex items-center gap-4 px-6 py-4 border-b border-[#F0F2F5] last:border-0 hover:bg-[#F4F6F8]/50 transition-colors"
                >
                  <div className="w-10 h-10 rounded-xl bg-[#EBF2FF] flex items-center justify-center shrink-0">
                    <AppleSticker symbol="🎮" size={20} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-semibold text-[14px] text-[#161C2D]">
                      {s.case_title || s.case || `Sessiya ${s.id?.slice(0, 8)}`}
                    </div>
                    <div className="text-[12px] text-[#6B7280]">
                      {s.started_at ? new Date(s.started_at).toLocaleString('uz-UZ') : '—'}
                    </div>
                  </div>
                  <span className={`text-[11px] font-bold px-2.5 py-0.5 rounded-full border ${
                    s.status === 'COMPLETED' ? 'bg-emerald-50 text-emerald-700 border-emerald-100' :
                    s.status === 'IN_PROGRESS' ? 'bg-blue-50 text-blue-700 border-blue-100' :
                    'bg-gray-50 text-gray-600 border-gray-100'
                  }`}>
                    {s.status === 'COMPLETED' ? 'Yakunlangan' : s.status === 'IN_PROGRESS' ? 'Davom etmoqda' : s.status || '—'}
                  </span>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Quick actions */}
        <section className="grid sm:grid-cols-2 gap-4">
          <div className="p-6 rounded-2xl bg-gradient-to-r from-[#0056D6] to-[#0081FF] text-white flex flex-col gap-3">
            <div className="flex items-center gap-2">
              <AppleSticker symbol="🎮" size={24} />
              <span className="font-display font-bold text-[17px]">Simulyatsiya boshlash</span>
            </div>
            <p className="text-white/70 text-[13px]">AI bilan jonli simulyatsiyada qatnashing va bilimingizni sinab ko'ring.</p>
            <button className="mt-1 self-start px-5 py-2 bg-white text-[#0056D6] text-[13px] font-bold rounded-xl hover:bg-[#EBF2FF] transition-all">
              Boshlash →
            </button>
          </div>
          <div className="p-6 rounded-2xl bg-gradient-to-r from-violet-500 to-violet-700 text-white flex flex-col gap-3">
            <div className="flex items-center gap-2">
              <AppleSticker symbol="🏆" size={24} />
              <span className="font-display font-bold text-[17px]">Reyting</span>
            </div>
            <p className="text-white/70 text-[13px]">Boshqa talabalar bilan taqqoslang va eng yaxshi natijaga erishing.</p>
            <button className="mt-1 self-start px-5 py-2 bg-white text-violet-700 text-[13px] font-bold rounded-xl hover:bg-violet-50 transition-all">
              Ko'rish →
            </button>
          </div>
        </section>
      </main>
    </div>
  );
}
