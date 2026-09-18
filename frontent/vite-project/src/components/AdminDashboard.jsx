import { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { adminApi } from '../services/api';
import AppleSticker from './AppleSticker';

/* ── Generic hook for paginated admin list ─────────────────── */
function useAdminList(fetcher, deps = []) {
  const [data, setData]       = useState([]);
  const [count, setCount]     = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState(null);
  const [search, setSearch]   = useState('');
  const [page, setPage]       = useState(1);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetcher({ search, page });
      const d = res.data;
      // Handle both paginated and plain list responses
      if (d && typeof d.count === 'number') {
        setData(d.results || []);
        setCount(d.count);
      } else if (Array.isArray(d)) {
        setData(d);
        setCount(d.length);
      } else if (d?.data && Array.isArray(d.data)) {
        setData(d.data);
        setCount(d.data.length);
      } else {
        setData([]);
        setCount(0);
      }
    } catch (e) {
      setError(e?.response?.data?.error?.message || 'Xatolik yuz berdi');
      setData([]);
    } finally {
      setLoading(false);
    }
  }, [search, page, ...deps]); // eslint-disable-line

  useEffect(() => { load(); }, [load]);

  return { data, count, loading, error, search, setSearch, page, setPage, reload: load };
}

/* ── Role badge colors ─────────────────────────────────────── */
const ROLE_STYLES = {
  ADMIN:      { label: 'Admin',     cls: 'bg-red-100 text-red-700 border-red-200' },
  INSTRUCTOR: { label: 'Mentor',    cls: 'bg-violet-100 text-violet-700 border-violet-200' },
  STUDENT:    { label: 'Talaba',    cls: 'bg-blue-100 text-blue-700 border-blue-200' },
  RECRUITER:  { label: 'Recruiter', cls: 'bg-amber-100 text-amber-700 border-amber-200' },
};

function RoleBadge({ role }) {
  const s = ROLE_STYLES[role] || { label: role, cls: 'bg-gray-100 text-gray-700' };
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-bold border ${s.cls}`}>
      {s.label}
    </span>
  );
}

function StatusDot({ active }) {
  return (
    <span className={`inline-flex items-center gap-1.5 text-[12px] font-semibold ${active ? 'text-emerald-600' : 'text-red-500'}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${active ? 'bg-emerald-500' : 'bg-red-400'}`} />
      {active ? 'Faol' : 'Nofaol'}
    </span>
  );
}

/* ── Search bar ─────────────────────────────────────────────── */
function SearchBar({ value, onChange, placeholder }) {
  return (
    <div className="relative">
      <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#6B7280]" viewBox="0 0 20 20" fill="currentColor">
        <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
      </svg>
      <input
        type="text"
        value={value}
        onChange={e => onChange(e.target.value)}
        placeholder={placeholder || 'Qidirish...'}
        className="w-full pl-9 pr-4 py-2.5 rounded-xl border border-[#E5E9F0] bg-white text-[14px] text-[#161C2D] placeholder:text-[#9CA3AF] focus:outline-none focus:border-[#0056D6] focus:ring-2 focus:ring-[#0056D6]/10 transition-all"
      />
    </div>
  );
}

/* ── Table skeleton ─────────────────────────────────────────── */
function TableSkeleton({ cols = 5, rows = 6 }) {
  return (
    <div className="animate-pulse">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex gap-4 px-6 py-3.5 border-b border-[#F0F2F5]">
          {Array.from({ length: cols }).map((_, j) => (
            <div key={j} className={`h-4 rounded bg-[#F4F6F8] ${j === 0 ? 'w-8' : 'flex-1'}`} />
          ))}
        </div>
      ))}
    </div>
  );
}

/* ── Empty state ─────────────────────────────────────────────── */
function EmptyState({ icon, title, desc }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="mb-4"><AppleSticker symbol={icon} size={48} /></div>
      <h3 className="font-display font-bold text-[#161C2D] text-[17px] mb-1">{title}</h3>
      <p className="text-[14px] text-[#6B7280]">{desc}</p>
    </div>
  );
}

/* ── Error state ────────────────────────────────────────────── */
function ErrorState({ msg, onRetry }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="w-12 h-12 rounded-full bg-red-50 flex items-center justify-center mb-4">
        <svg className="w-6 h-6 text-red-500" viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
        </svg>
      </div>
      <p className="text-[14px] text-red-600 font-medium mb-3">{msg}</p>
      {onRetry && (
        <button onClick={onRetry} className="text-[13px] font-semibold text-[#0056D6] hover:underline">
          Qayta urinish
        </button>
      )}
    </div>
  );
}

/* ════════════════════════════════════════════
   TAB: FOYDALANUVCHILAR RO'YXATI
   ════════════════════════════════════════════ */
function UsersTab() {
  const [roleFilter, setRoleFilter] = useState('');
  const { data, count, loading, error, search, setSearch, reload } = useAdminList(
    ({ search }) => adminApi.getUsers({ search, role: roleFilter || undefined }),
    [roleFilter]
  );

  const ROLE_OPTS = [
    { value: '',           label: "Barchasi" },
    { value: 'STUDENT',    label: "Talabalar" },
    { value: 'INSTRUCTOR', label: "Mentorlar" },
    { value: 'ADMIN',      label: "Adminlar" },
    { value: 'RECRUITER',  label: "Recruiterlar" },
  ];

  return (
    <div className="flex flex-col gap-5">
      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex-1 min-w-[200px]">
          <SearchBar value={search} onChange={setSearch} placeholder="Email, username, ism..." />
        </div>
        <div className="flex items-center gap-2">
          {ROLE_OPTS.map(o => (
            <button
              key={o.value}
              onClick={() => setRoleFilter(o.value)}
              className={`px-3.5 py-2 rounded-lg text-[13px] font-semibold transition-all ${
                roleFilter === o.value
                  ? 'bg-[#0056D6] text-white shadow-sm'
                  : 'bg-white border border-[#E5E9F0] text-[#6B7280] hover:text-[#161C2D] hover:border-[#0056D6]/40'
              }`}
            >
              {o.label}
            </button>
          ))}
        </div>
        <span className="text-[13px] text-[#6B7280] font-medium shrink-0">
          Jami: <strong className="text-[#161C2D]">{count}</strong>
        </span>
      </div>

      {/* Table */}
      <div className="bg-white rounded-2xl border border-[#E5E9F0] overflow-hidden shadow-sm">
        <div className="grid grid-cols-[2rem_3fr_2.5fr_1.2fr_1.2fr_1fr] text-[11px] font-bold uppercase tracking-wider text-[#6B7280] px-6 py-3 bg-[#F4F6F8] border-b border-[#E5E9F0]">
          <span>#</span>
          <span>Foydalanuvchi</span>
          <span>Email</span>
          <span>Rol</span>
          <span>Holat</span>
          <span>Qo'shilgan</span>
        </div>

        {loading ? (
          <TableSkeleton cols={6} rows={8} />
        ) : error ? (
          <ErrorState msg={error} onRetry={reload} />
        ) : data.length === 0 ? (
          <EmptyState icon="👥" title="Foydalanuvchi topilmadi" desc="Qidiruv shartlarini o'zgartiring" />
        ) : (
          data.map((u, i) => (
            <div
              key={u.id}
              className="grid grid-cols-[2rem_3fr_2.5fr_1.2fr_1.2fr_1fr] px-6 py-3.5 border-b border-[#F0F2F5] last:border-0 hover:bg-[#F4F6F8]/50 transition-colors items-center"
            >
              <span className="text-[12px] font-semibold text-[#9CA3AF]">{i + 1}</span>
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#0056D6] to-[#0041A8] flex items-center justify-center text-white text-[11px] font-bold shrink-0">
                  {(u.first_name?.[0] || u.email?.[0] || '?').toUpperCase()}
                </div>
                <div>
                  <div className="text-[13px] font-semibold text-[#161C2D] leading-tight">
                    {u.full_name || `${u.first_name || ''} ${u.last_name || ''}`.trim() || u.username}
                  </div>
                  <div className="text-[11px] text-[#9CA3AF]">@{u.username}</div>
                </div>
              </div>
              <span className="text-[13px] text-[#6B7280] truncate">{u.email}</span>
              <RoleBadge role={u.role} />
              <StatusDot active={u.is_active} />
              <span className="text-[12px] text-[#9CA3AF]">
                {u.date_joined ? new Date(u.date_joined).toLocaleDateString('uz-UZ') : '—'}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

/* ════════════════════════════════════════════
   TAB: MENTORLAR RO'YXATI
   ════════════════════════════════════════════ */
function MentorsTab() {
  const { data, count, loading, error, search, setSearch, reload } = useAdminList(
    ({ search }) => adminApi.getMentors({ search })
  );

  return (
    <div className="flex flex-col gap-5">
      <div className="flex items-center gap-3">
        <div className="flex-1">
          <SearchBar value={search} onChange={setSearch} placeholder="Mentor nomi yoki emaili..." />
        </div>
        <span className="text-[13px] text-[#6B7280] font-medium shrink-0">
          Jami: <strong className="text-[#161C2D]">{count}</strong>
        </span>
      </div>

      <div className="bg-white rounded-2xl border border-[#E5E9F0] overflow-hidden shadow-sm">
        <div className="grid grid-cols-[2rem_3fr_2.5fr_1.5fr_1fr] text-[11px] font-bold uppercase tracking-wider text-[#6B7280] px-6 py-3 bg-[#F4F6F8] border-b border-[#E5E9F0]">
          <span>#</span>
          <span>Mentor</span>
          <span>Email</span>
          <span>Holat</span>
          <span>Qo'shilgan</span>
        </div>

        {loading ? (
          <TableSkeleton cols={5} rows={6} />
        ) : error ? (
          <ErrorState msg={error} onRetry={reload} />
        ) : data.length === 0 ? (
          <EmptyState icon="👨‍🏫" title="Mentor topilmadi" desc="Hali birorta mentor ro'yxatdan o'tmagan" />
        ) : (
          data.map((m, i) => (
            <div
              key={m.id}
              className="grid grid-cols-[2rem_3fr_2.5fr_1.5fr_1fr] px-6 py-4 border-b border-[#F0F2F5] last:border-0 hover:bg-[#F4F6F8]/50 transition-colors items-center"
            >
              <span className="text-[12px] font-semibold text-[#9CA3AF]">{i + 1}</span>
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-full bg-gradient-to-br from-violet-500 to-violet-700 flex items-center justify-center text-white text-[12px] font-bold shrink-0">
                  {(m.first_name?.[0] || m.email?.[0] || 'M').toUpperCase()}
                </div>
                <div>
                  <div className="text-[13px] font-semibold text-[#161C2D]">
                    {m.full_name || `${m.first_name || ''} ${m.last_name || ''}`.trim() || m.username}
                  </div>
                  <div className="text-[11px] text-[#9CA3AF]">@{m.username}</div>
                </div>
              </div>
              <span className="text-[13px] text-[#6B7280]">{m.email}</span>
              <StatusDot active={m.is_active} />
              <span className="text-[12px] text-[#9CA3AF]">
                {m.date_joined ? new Date(m.date_joined).toLocaleDateString('uz-UZ') : '—'}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

/* ════════════════════════════════════════════
   TAB: KURSLAR RO'YXATI
   ════════════════════════════════════════════ */
const DIFFICULTY_STYLES = {
  BEGINNER:     { label: "Boshlang'ich", cls: 'bg-emerald-100 text-emerald-700 border-emerald-200' },
  INTERMEDIATE: { label: 'O\'rta',        cls: 'bg-amber-100 text-amber-700 border-amber-200' },
  ADVANCED:     { label: 'Ilg\'or',       cls: 'bg-red-100 text-red-700 border-red-200' },
};

function CoursesTab() {
  const { data, count, loading, error, search, setSearch, reload } = useAdminList(
    ({ search }) => adminApi.getCourses({ search })
  );

  return (
    <div className="flex flex-col gap-5">
      <div className="flex items-center gap-3">
        <div className="flex-1">
          <SearchBar value={search} onChange={setSearch} placeholder="Kurs nomi, domenga qarab..." />
        </div>
        <span className="text-[13px] text-[#6B7280] font-medium shrink-0">
          Jami: <strong className="text-[#161C2D]">{count}</strong>
        </span>
      </div>

      <div className="bg-white rounded-2xl border border-[#E5E9F0] overflow-hidden shadow-sm">
        <div className="grid grid-cols-[2rem_3fr_1.5fr_1.5fr_1.2fr_1fr] text-[11px] font-bold uppercase tracking-wider text-[#6B7280] px-6 py-3 bg-[#F4F6F8] border-b border-[#E5E9F0]">
          <span>#</span>
          <span>Kurs nomi</span>
          <span>Mentor</span>
          <span>Domen</span>
          <span>Daraja</span>
          <span>Holat</span>
        </div>

        {loading ? (
          <TableSkeleton cols={6} rows={6} />
        ) : error ? (
          <ErrorState msg={error} onRetry={reload} />
        ) : data.length === 0 ? (
          <EmptyState icon="📚" title="Kurs topilmadi" desc="Hali birorta kurs yaratilmagan" />
        ) : (
          data.map((c, i) => {
            const diff = DIFFICULTY_STYLES[c.difficulty] || { label: c.difficulty, cls: 'bg-gray-100 text-gray-700' };
            return (
              <div
                key={c.id}
                className="grid grid-cols-[2rem_3fr_1.5fr_1.5fr_1.2fr_1fr] px-6 py-4 border-b border-[#F0F2F5] last:border-0 hover:bg-[#F4F6F8]/50 transition-colors items-center"
              >
                <span className="text-[12px] font-semibold text-[#9CA3AF]">{i + 1}</span>
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-[#EBF2FF] flex items-center justify-center shrink-0">
                    <AppleSticker symbol="📚" size={20} />
                  </div>
                  <div>
                    <div className="text-[13px] font-semibold text-[#161C2D] leading-tight">{c.title}</div>
                    <div className="text-[11px] text-[#9CA3AF] truncate max-w-[200px]">{c.description || c.slug}</div>
                  </div>
                </div>
                <span className="text-[13px] text-[#6B7280]">{c.instructor_name || '—'}</span>
                <span className="text-[13px] text-[#6B7280]">{c.domain_name || '—'}</span>
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-bold border ${diff.cls}`}>
                  {diff.label}
                </span>
                <span className={`inline-flex items-center gap-1.5 text-[12px] font-semibold ${c.is_published ? 'text-emerald-600' : 'text-amber-500'}`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${c.is_published ? 'bg-emerald-500' : 'bg-amber-400'}`} />
                  {c.is_published ? 'Chiqarilgan' : 'Qoralama'}
                </span>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

/* ════════════════════════════════════════════
   STATS CARD
   ════════════════════════════════════════════ */
function StatCard({ icon, label, value, color, sub }) {
  return (
    <div className={`relative p-6 rounded-2xl border border-white bg-gradient-to-br ${color} overflow-hidden group hover:shadow-[0_12px_36px_rgba(0,0,0,0.10)] hover:-translate-y-0.5 transition-all duration-300`}>
      <div className="flex items-start justify-between mb-4">
        <div className="w-12 h-12 rounded-xl bg-white/70 flex items-center justify-center shadow-sm">
          <AppleSticker symbol={icon} size={26} />
        </div>
      </div>
      <div className="font-display font-extrabold text-[32px] text-[#161C2D] leading-tight">{value ?? '—'}</div>
      <div className="text-[13px] font-semibold text-[#6B7280] mt-1">{label}</div>
      {sub && <div className="text-[11px] text-[#9CA3AF] mt-0.5">{sub}</div>}
    </div>
  );
}

/* ════════════════════════════════════════════
   SIDEBAR NAV ITEM
   ════════════════════════════════════════════ */
function SideNavItem({ icon, label, active, onClick, badge }) {
  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-left transition-all duration-200 ${
        active
          ? 'bg-[#0056D6] text-white shadow-[0_4px_14px_rgba(0,86,214,0.35)]'
          : 'text-[#6B7280] hover:bg-[#F4F6F8] hover:text-[#161C2D]'
      }`}
    >
      <span className="text-lg"><AppleSticker symbol={icon} size={20} /></span>
      <span className="text-[14px] font-semibold flex-1">{label}</span>
      {badge != null && (
        <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${
          active ? 'bg-white/25 text-white' : 'bg-[#EBF2FF] text-[#0056D6]'
        }`}>
          {badge}
        </span>
      )}
    </button>
  );
}

/* ════════════════════════════════════════════
   MAIN: ADMIN DASHBOARD
   ════════════════════════════════════════════ */
const TABS = [
  { id: 'overview',  label: 'Umumiy',            icon: '📊' },
  { id: 'users',     label: 'Foydalanuvchilar',  icon: '👥' },
  { id: 'mentors',   label: 'Mentorlar',          icon: '👨‍🏫' },
  { id: 'courses',   label: 'Kurslar',            icon: '📚' },
];

export default function AdminDashboard({ user, onLogout }) {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('overview');

  // Stats
  const [stats, setStats] = useState({ users: null, mentors: null, students: null, courses: null });
  const [statsLoading, setStatsLoading] = useState(true);

  useEffect(() => {
    async function loadStats() {
      setStatsLoading(true);
      try {
        const [usersRes, mentorsRes, studentsRes, coursesRes] = await Promise.allSettled([
          adminApi.getUsers({ page: 1 }),
          adminApi.getMentors({ page: 1 }),
          adminApi.getStudents({ page: 1 }),
          adminApi.getCourses({ page: 1 }),
        ]);

        const getCount = (res) => {
          if (res.status !== 'fulfilled') return null;
          const d = res.value.data;
          if (typeof d.count === 'number') return d.count;
          if (Array.isArray(d)) return d.length;
          return null;
        };

        setStats({
          users:    getCount(usersRes),
          mentors:  getCount(mentorsRes),
          students: getCount(studentsRes),
          courses:  getCount(coursesRes),
        });
      } catch {
        // Silently fail stats
      } finally {
        setStatsLoading(false);
      }
    }
    loadStats();
  }, []);

  async function handleLogout() {
    await onLogout();
    navigate('/login');
  }

  return (
    <div className="min-h-screen bg-[#F4F6F8] flex flex-col">
      {/* ── Top Header ── */}
      <header className="bg-white border-b border-[#E5E9F0] sticky top-0 z-40 shadow-sm">
        <div className="max-w-[1440px] mx-auto px-6 h-16 flex items-center justify-between gap-4">
          <Link to="/" className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#0056D6] to-[#0041A8] flex items-center justify-center shadow-sm">
              <svg width="16" height="16" viewBox="0 0 20 20" fill="none">
                <circle cx="10" cy="10" r="4" fill="white" opacity="0.95" />
                <circle cx="10" cy="10" r="8" stroke="white" strokeWidth="1.5" opacity="0.35" />
              </svg>
            </div>
            <span className="font-display font-bold text-[17px] text-[#161C2D]">ChronosAI</span>
          </Link>

          <div className="flex items-center gap-3">
            <span className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-50 border border-red-100 text-[12px] font-bold text-red-600">
              <span className="w-1.5 h-1.5 rounded-full bg-red-500" />
              ADMIN PANEL
            </span>
            <div className="flex items-center gap-2 px-3 py-2 bg-[#F4F6F8] rounded-lg">
              <div className="w-7 h-7 rounded-full bg-gradient-to-br from-red-500 to-red-700 flex items-center justify-center text-white text-[11px] font-bold">
                {(user?.first_name?.[0] || user?.email?.[0] || 'A').toUpperCase()}
              </div>
              <span className="text-[14px] font-semibold text-[#161C2D] hidden md:inline">
                {user?.first_name || 'Admin'}
              </span>
            </div>
            <button
              id="admin-logout-btn"
              onClick={handleLogout}
              className="text-sm font-semibold text-[#6B7280] hover:text-red-500 px-3 py-2 rounded-lg hover:bg-red-50 transition-all"
            >
              Chiqish
            </button>
          </div>
        </div>
      </header>

      {/* ── Body: Sidebar + Content ── */}
      <div className="flex flex-1 max-w-[1440px] mx-auto w-full px-6 py-8 gap-8">
        {/* Sidebar */}
        <aside className="hidden lg:flex flex-col gap-2 w-[220px] shrink-0">
          <div className="mb-4">
            <p className="text-[11px] font-bold uppercase tracking-widest text-[#9CA3AF] px-4 mb-2">Navigatsiya</p>
            {TABS.map(t => (
              <SideNavItem
                key={t.id}
                icon={t.icon}
                label={t.label}
                active={activeTab === t.id}
                onClick={() => setActiveTab(t.id)}
                badge={
                  !statsLoading && t.id === 'users'   ? stats.users   :
                  !statsLoading && t.id === 'mentors'  ? stats.mentors  :
                  !statsLoading && t.id === 'courses'  ? stats.courses  :
                  undefined
                }
              />
            ))}
          </div>
        </aside>

        {/* Mobile tab bar */}
        <div className="lg:hidden flex gap-2 overflow-x-auto pb-1 mb-4 fixed bottom-0 left-0 right-0 bg-white border-t border-[#E5E9F0] px-4 py-2 z-30">
          {TABS.map(t => (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id)}
              className={`flex-1 flex flex-col items-center gap-1 py-1 rounded-lg transition-all ${
                activeTab === t.id ? 'text-[#0056D6]' : 'text-[#9CA3AF]'
              }`}
            >
              <AppleSticker symbol={t.icon} size={22} />
              <span className="text-[10px] font-semibold">{t.label.split(' ')[0]}</span>
            </button>
          ))}
        </div>

        {/* Main content */}
        <main className="flex-1 min-w-0 pb-20 lg:pb-0">
          {/* Overview tab */}
          {activeTab === 'overview' && (
            <div className="flex flex-col gap-8">
              {/* Page title */}
              <div>
                <h1 className="font-display font-extrabold text-[28px] text-[#161C2D] tracking-tight flex items-center gap-2">
                  <AppleSticker symbol="📊" size={30} />
                  Boshqaruv paneli
                </h1>
                <p className="text-[14px] text-[#6B7280] mt-1">
                  Tizim statistikasi va umumiy ko'rinish
                </p>
              </div>

              {/* Stats grid */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard
                  icon="👥"
                  label="Jami foydalanuvchilar"
                  value={statsLoading ? '...' : (stats.users ?? 'N/A')}
                  color="from-blue-50 to-blue-100/50"
                  sub="Barcha rollar"
                />
                <StatCard
                  icon="👨‍🏫"
                  label="Mentorlar"
                  value={statsLoading ? '...' : (stats.mentors ?? 'N/A')}
                  color="from-violet-50 to-violet-100/50"
                  sub="INSTRUCTOR roli"
                />
                <StatCard
                  icon="🎓"
                  label="Talabalar"
                  value={statsLoading ? '...' : (stats.students ?? 'N/A')}
                  color="from-emerald-50 to-emerald-100/50"
                  sub="STUDENT roli"
                />
                <StatCard
                  icon="📚"
                  label="Kurslar"
                  value={statsLoading ? '...' : (stats.courses ?? 'N/A')}
                  color="from-amber-50 to-amber-100/50"
                  sub="Barcha kurslar"
                />
              </div>

              {/* Quick actions */}
              <div>
                <h2 className="font-display font-bold text-[18px] text-[#161C2D] mb-4">Tezkor harakatlar</h2>
                <div className="grid sm:grid-cols-3 gap-4">
                  {[
                    { icon: '👥', label: 'Barcha foydalanuvchilar', desc: "To'liq foydalanuvchilar ro'yxati", tab: 'users',   color: 'from-blue-50 to-blue-100/50' },
                    { icon: '👨‍🏫', label: 'Mentorlar',              desc: "Mentorlar va o'qituvchilar",     tab: 'mentors', color: 'from-violet-50 to-violet-100/50' },
                    { icon: '📚', label: 'Kurslar',                 desc: "Barcha kurslar va darslar",       tab: 'courses', color: 'from-amber-50 to-amber-100/50' },
                  ].map(item => (
                    <button
                      key={item.tab}
                      onClick={() => setActiveTab(item.tab)}
                      className={`group text-left p-6 rounded-2xl bg-gradient-to-br ${item.color} border border-white hover:shadow-[0_12px_36px_rgba(0,0,0,0.10)] hover:-translate-y-1 transition-all duration-300`}
                    >
                      <div className="w-10 h-10 rounded-xl bg-white/70 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
                        <AppleSticker symbol={item.icon} size={22} />
                      </div>
                      <div className="font-display font-bold text-[#161C2D] text-[15px] mb-1">{item.label}</div>
                      <div className="text-[12px] text-[#6B7280]">{item.desc}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Recent users preview */}
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h2 className="font-display font-bold text-[18px] text-[#161C2D]">So'nggi foydalanuvchilar</h2>
                  <button
                    onClick={() => setActiveTab('users')}
                    className="text-[13px] font-semibold text-[#0056D6] hover:underline"
                  >
                    Barchasini ko'rish →
                  </button>
                </div>
                <UsersTab />
              </div>
            </div>
          )}

          {activeTab === 'users'   && (
            <div className="flex flex-col gap-6">
              <h1 className="font-display font-extrabold text-[26px] text-[#161C2D] flex items-center gap-2">
                <AppleSticker symbol="👥" size={28} />
                Foydalanuvchilar ro'yxati
              </h1>
              <UsersTab />
            </div>
          )}

          {activeTab === 'mentors' && (
            <div className="flex flex-col gap-6">
              <h1 className="font-display font-extrabold text-[26px] text-[#161C2D] flex items-center gap-2">
                <AppleSticker symbol="👨‍🏫" size={28} />
                Mentorlar ro'yxati
              </h1>
              <MentorsTab />
            </div>
          )}

          {activeTab === 'courses' && (
            <div className="flex flex-col gap-6">
              <h1 className="font-display font-extrabold text-[26px] text-[#161C2D] flex items-center gap-2">
                <AppleSticker symbol="📚" size={28} />
                Kurslar ro'yxati
              </h1>
              <CoursesTab />
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
