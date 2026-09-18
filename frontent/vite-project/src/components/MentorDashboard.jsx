import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { groupsApi, curriculumApi } from '../services/api';
import AppleSticker from './AppleSticker';

function StatCard({ icon, label, value, color }) {
  return (
    <div className={`p-6 rounded-2xl bg-gradient-to-br ${color} border border-white hover:shadow-[0_12px_36px_rgba(0,0,0,0.10)] hover:-translate-y-0.5 transition-all duration-300`}>
      <div className="w-11 h-11 rounded-xl bg-white/70 flex items-center justify-center mb-4">
        <AppleSticker symbol={icon} size={24} />
      </div>
      <div className="font-display font-extrabold text-[30px] text-[#161C2D] leading-tight">{value ?? '—'}</div>
      <div className="text-[13px] font-semibold text-[#6B7280] mt-1">{label}</div>
    </div>
  );
}

export default function MentorDashboard({ user, onLogout }) {
  const navigate = useNavigate();
  const [groups,  setGroups]  = useState([]);
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const [gRes, cRes] = await Promise.allSettled([
          groupsApi.list(),
          curriculumApi.getCourses(),
        ]);

        if (gRes.status === 'fulfilled') {
          const d = gRes.value.data;
          setGroups(Array.isArray(d) ? d : d?.results || []);
        }
        if (cRes.status === 'fulfilled') {
          const d = cRes.value.data;
          setCourses(Array.isArray(d) ? d : d?.results || []);
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

  async function handleGenerateInvite(groupId) {
    try {
      const res = await groupsApi.generateInvite(groupId);
      const token = res.data?.data?.token || res.data?.token;
      if (token) {
        const url = `${window.location.origin}/join/${token}`;
        await navigator.clipboard.writeText(url);
        alert('Invite havola nusxalandi: ' + url);
      }
    } catch {
      alert("Invite link yaratishda xatolik yuz berdi.");
    }
  }

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
            <span className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-violet-50 border border-violet-100 text-[12px] font-bold text-violet-700">
              <AppleSticker symbol="👨‍🏫" size={14} />
              MENTOR
            </span>
            <div className="flex items-center gap-2 px-3 py-2 bg-[#F4F6F8] rounded-lg">
              <div className="w-7 h-7 rounded-full bg-gradient-to-br from-violet-500 to-violet-700 flex items-center justify-center text-white text-[11px] font-bold">
                {(user?.first_name?.[0] || user?.email?.[0] || 'M').toUpperCase()}
              </div>
              <span className="text-[14px] font-semibold text-[#161C2D] hidden md:inline">
                {user?.first_name || 'Mentor'}
              </span>
            </div>
            <button
              id="mentor-logout-btn"
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
        <div>
          <h1 className="font-display font-extrabold text-[30px] text-[#161C2D] tracking-tight flex items-center gap-2">
            Salom, {user?.first_name || 'Mentor'}! <AppleSticker symbol="👋" size={30} />
          </h1>
          <p className="text-[#6B7280] mt-1 text-[15px]">Guruhlaringiz va kurslaringizni bu yerdan boshqaring.</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard icon="👥" label="Guruhlar" value={loading ? '...' : groups.length} color="from-blue-50 to-blue-100/50" />
          <StatCard icon="📚" label="Kurslar"  value={loading ? '...' : courses.length} color="from-violet-50 to-violet-100/50" />
          <StatCard icon="🎓" label="Talabalar" value={loading ? '...' : groups.reduce((sum, g) => sum + (g.student_count || 0), 0)} color="from-emerald-50 to-emerald-100/50" />
          <StatCard icon="🎮" label="Simulyatsiyalar" value="—" color="from-amber-50 to-amber-100/50" />
        </div>

        {/* Groups */}
        <section>
          <div className="flex items-center justify-between mb-5">
            <h2 className="font-display font-bold text-[20px] text-[#161C2D] flex items-center gap-2">
              <AppleSticker symbol="👥" size={22} />
              Mening guruhlarim
            </h2>
            <Link
              to="#"
              className="text-[13px] font-semibold text-[#0056D6] border border-[#0056D6]/20 px-4 py-2 rounded-lg hover:bg-[#EBF2FF] transition-all"
            >
              + Yangi guruh
            </Link>
          </div>

          {loading ? (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4 animate-pulse">
              {[1,2,3].map(i => (
                <div key={i} className="h-36 rounded-2xl bg-[#F4F6F8]" />
              ))}
            </div>
          ) : groups.length === 0 ? (
            <div className="bg-white border border-[#E5E9F0] rounded-2xl p-10 text-center">
              <AppleSticker symbol="👥" size={40} className="mx-auto mb-3" />
              <p className="font-semibold text-[#161C2D]">Hali guruh yo'q</p>
              <p className="text-[13px] text-[#6B7280] mt-1">Birinchi guruhingizni yarating</p>
            </div>
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {groups.map(g => (
                <div
                  key={g.id}
                  className="bg-white border border-[#E5E9F0] rounded-2xl p-5 flex flex-col gap-3 hover:shadow-[0_8px_28px_rgba(0,0,0,0.08)] hover:-translate-y-0.5 transition-all duration-300"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="font-display font-bold text-[#161C2D] text-[15px] leading-tight">{g.name}</h3>
                      <p className="text-[12px] text-[#6B7280] mt-0.5 line-clamp-2">{g.description || "Tavsif yo'q"}</p>
                    </div>
                    <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full shrink-0 ${g.is_active ? 'bg-emerald-50 text-emerald-600' : 'bg-[#F4F6F8] text-[#9CA3AF]'}`}>
                      {g.is_active ? 'Faol' : 'Nofaol'}
                    </span>
                  </div>

                  <div className="flex items-center gap-3 text-[12px] text-[#6B7280]">
                    <span className="flex items-center gap-1">
                      <AppleSticker symbol="🎓" size={14} />
                      {g.student_count || 0} talaba
                    </span>
                    <span className="flex items-center gap-1">
                      <AppleSticker symbol="📚" size={14} />
                      {g.courses_count || 0} kurs
                    </span>
                  </div>

                  <button
                    onClick={() => handleGenerateInvite(g.id)}
                    className="w-full mt-1 text-[13px] font-semibold text-[#0056D6] border border-[#0056D6]/20 py-2 rounded-lg hover:bg-[#EBF2FF] transition-all flex items-center justify-center gap-2"
                  >
                    <AppleSticker symbol="🔗" size={14} />
                    Invite link yaratish
                  </button>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Courses */}
        <section>
          <div className="flex items-center justify-between mb-5">
            <h2 className="font-display font-bold text-[20px] text-[#161C2D] flex items-center gap-2">
              <AppleSticker symbol="📚" size={22} />
              Kurslar
            </h2>
          </div>

          {loading ? (
            <div className="bg-white border border-[#E5E9F0] rounded-2xl h-32 animate-pulse" />
          ) : courses.length === 0 ? (
            <div className="bg-white border border-[#E5E9F0] rounded-2xl p-10 text-center">
              <AppleSticker symbol="📚" size={40} className="mx-auto mb-3" />
              <p className="font-semibold text-[#161C2D]">Kurslar mavjud emas</p>
            </div>
          ) : (
            <div className="bg-white border border-[#E5E9F0] rounded-2xl overflow-hidden">
              {courses.slice(0, 8).map((c, i) => (
                <div
                  key={c.id}
                  className="flex items-center gap-4 px-6 py-4 border-b border-[#F0F2F5] last:border-0 hover:bg-[#F4F6F8]/50 transition-colors"
                >
                  <div className="w-10 h-10 rounded-xl bg-[#EBF2FF] flex items-center justify-center shrink-0">
                    <AppleSticker symbol="📚" size={20} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-semibold text-[14px] text-[#161C2D] truncate">{c.title}</div>
                    <div className="text-[12px] text-[#6B7280]">{c.domain_name || '—'} · {c.difficulty || '—'}</div>
                  </div>
                  <span className={`text-[11px] font-bold px-2.5 py-0.5 rounded-full border ${c.is_published ? 'bg-emerald-50 text-emerald-700 border-emerald-100' : 'bg-amber-50 text-amber-700 border-amber-100'}`}>
                    {c.is_published ? 'Chiqarilgan' : 'Qoralama'}
                  </span>
                </div>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
