import { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';

function loadGSI() {
  return new Promise((resolve) => {
    if (window.google?.accounts) return resolve(window.google.accounts);
    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.onload = () => resolve(window.google?.accounts);
    document.head.appendChild(script);
  });
}

function LogoIcon() {
  return (
    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#0056D6] to-[#0041A8] flex items-center justify-center shadow-[0_4px_16px_rgba(0,86,214,0.35)]">
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <circle cx="10" cy="10" r="4" fill="white" opacity="0.95" />
        <circle cx="10" cy="10" r="8" stroke="white" strokeWidth="1.5" opacity="0.35" />
      </svg>
    </div>
  );
}

function GoogleButton({ onClick, loading }) {
  return (
    <button
      type="button"
      id="register-google-btn"
      onClick={onClick}
      disabled={loading}
      className="w-full flex items-center justify-center gap-3 py-3 px-4 rounded-xl border border-[#E5E9F0] bg-white hover:bg-[#F4F6F8] hover:border-[#D0D7E3] disabled:opacity-60 disabled:cursor-not-allowed transition-all duration-200 text-[15px] font-semibold text-[#161C2D] shadow-sm hover:shadow"
    >
      <svg width="20" height="20" viewBox="0 0 48 48" aria-hidden="true">
        <path fill="#FFC107" d="M43.6 20.1H42V20H24v8h11.3C33.7 32.1 29.3 35 24 35c-6.1 0-11-4.9-11-11s4.9-11 11-11c2.8 0 5.3 1 7.2 2.7l5.7-5.7C33.5 7.1 29 5 24 5 12.9 5 4 13.9 4 25s8.9 20 20 20 20-8.9 20-20c0-1.3-.1-2.6-.4-3.9z" />
        <path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.7 15.4 19 12 24 12c2.8 0 5.3 1 7.2 2.7l5.7-5.7C33.5 5.8 29 4 24 4 16.3 4 9.7 8.3 6.3 14.7z" />
        <path fill="#4CAF50" d="M24 44c4.9 0 9.3-1.8 12.7-4.8l-5.9-5c-1.7 1.2-3.9 1.8-6.8 1.8-5.3 0-9.7-3-11.3-7.1l-6.5 5C9.8 39.6 16.4 44 24 44z" />
        <path fill="#1976D2" d="M43.6 20.1H42V20H24v8h11.3c-.8 2.1-2.2 3.9-3.9 5.1l5.9 5C40.9 36 44 31 44 25c0-1.3-.1-2.6-.4-3.9z" />
      </svg>
      {loading ? 'Kutilmoqda...' : 'Google orqali ro\'yxatdan o\'tish'}
    </button>
  );
}

function InputField({ id, label, type = 'text', value, onChange, placeholder, autoComplete, error, icon, hint }) {
  const [show, setShow] = useState(false);
  const isPassword = type === 'password';

  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="text-[13px] font-semibold text-[#161C2D]">
        {label}
      </label>
      <div className="relative">
        {icon && (
          <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#6B7280]">{icon}</span>
        )}
        <input
          id={id}
          type={isPassword ? (show ? 'text' : 'password') : type}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          autoComplete={autoComplete}
          className={`w-full ${icon ? 'pl-10' : 'pl-4'} ${isPassword ? 'pr-11' : 'pr-4'} py-3 rounded-xl border text-[15px] text-[#161C2D] placeholder:text-[#9CA3AF] outline-none transition-all duration-200 ${
            error
              ? 'border-red-400 bg-red-50 focus:border-red-500 focus:ring-2 focus:ring-red-100'
              : 'border-[#E5E9F0] bg-white focus:border-[#0056D6] focus:ring-2 focus:ring-[#0056D6]/10'
          }`}
        />
        {isPassword && (
          <button
            type="button"
            onClick={() => setShow(!show)}
            className="absolute right-3.5 top-1/2 -translate-y-1/2 text-[#9CA3AF] hover:text-[#6B7280] transition-colors"
            aria-label={show ? "Parolni yashirish" : "Parolni ko'rsatish"}
          >
            {show ? (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
            ) : (
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
            )}
          </button>
        )}
      </div>
      {error && <p className="text-[12px] text-red-500 font-medium">{error}</p>}
      {hint && !error && <p className="text-[12px] text-[#9CA3AF]">{hint}</p>}
    </div>
  );
}

/* ── Role selection card ── */
function RoleCard({ id, value, selected, onChange, icon, title, desc }) {
  return (
    <label
      htmlFor={id}
      className={`flex items-start gap-3 p-4 rounded-xl border cursor-pointer transition-all duration-200 ${
        selected
          ? 'border-[#0056D6] bg-[#EBF2FF] shadow-[0_0_0_3px_rgba(0,86,214,0.10)]'
          : 'border-[#E5E9F0] bg-white hover:border-[#0056D6]/40 hover:bg-[#F4F6F8]'
      }`}
    >
      <input
        id={id}
        type="radio"
        name="role"
        value={value}
        checked={selected}
        onChange={onChange}
        className="sr-only"
      />
      <span className="text-xl mt-0.5 shrink-0">{icon}</span>
      <div>
        <div className={`text-[14px] font-bold ${selected ? 'text-[#0056D6]' : 'text-[#161C2D]'}`}>
          {title}
        </div>
        <div className="text-[12px] text-[#6B7280] mt-0.5 leading-relaxed">{desc}</div>
      </div>
      {selected && (
        <span className="ml-auto shrink-0">
          <svg className="w-5 h-5 text-[#0056D6]" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
        </span>
      )}
    </label>
  );
}

/* ══════════════════════════════════════════════════════════
   REGISTER PAGE
   ══════════════════════════════════════════════════════════ */
export default function RegisterPage() {
  const { register, googleLogin, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = location.state?.from?.pathname || '/dashboard';

  const [form, setForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
    password: '',
    password2: '',
    role: 'student',
  });
  const [errors, setErrors]   = useState({});
  const [apiError, setApiError] = useState('');
  const [loading, setLoading]   = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);

  useEffect(() => {
    if (isAuthenticated) navigate(from, { replace: true });
  }, [isAuthenticated, navigate, from]);

  /* ── Validation ── */
  function validate() {
    const e = {};
    if (!form.first_name.trim()) e.first_name = "Ism kiritilishi shart";
    if (!form.last_name.trim()) e.last_name = "Familiya kiritilishi shart";
    if (!form.email.trim()) e.email = "Email manzil kiritilishi shart";
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) e.email = "Email format noto'g'ri";
    if (!form.password) e.password = "Parol kiritilishi shart";
    else if (form.password.length < 8) e.password = "Parol kamida 8 ta belgidan iborat bo'lishi kerak";
    if (form.password !== form.password2) e.password2 = "Parollar mos kelmayapti";
    setErrors(e);
    return Object.keys(e).length === 0;
  }

  /* ── Password strength ── */
  function getPasswordStrength(pw) {
    if (!pw) return { level: 0, label: '', color: '' };
    let score = 0;
    if (pw.length >= 8) score++;
    if (/[A-Z]/.test(pw)) score++;
    if (/[0-9]/.test(pw)) score++;
    if (/[^A-Za-z0-9]/.test(pw)) score++;
    const levels = [
      { level: 0, label: '', color: '' },
      { level: 1, label: "Juda zaif", color: 'bg-red-500' },
      { level: 2, label: "Zaif", color: 'bg-orange-400' },
      { level: 3, label: "O\'rtacha", color: 'bg-amber-400' },
      { level: 4, label: "Kuchli", color: 'bg-emerald-500' },
    ];
    return levels[score] || levels[0];
  }

  const strength = getPasswordStrength(form.password);

  /* ── Submit ── */
  async function handleSubmit(e) {
    e.preventDefault();
    setApiError('');
    if (!validate()) return;
    setLoading(true);
    try {
      await register({
        first_name: form.first_name,
        last_name:  form.last_name,
        email:      form.email,
        password:   form.password,
        password2:  form.password2,
        role:       form.role,
      });
      navigate(from, { replace: true });
    } catch (err) {
      const data = err.response?.data;
      if (data?.error?.details) {
        // Field-level errors from DRF serializer
        setErrors((prev) => ({ ...prev, ...data.error.details }));
      } else {
        setApiError(
          data?.error?.message ||
          data?.detail ||
          "Ro'yxatdan o'tishda xatolik yuz berdi. Qaytadan urinib ko'ring."
        );
      }
    } finally {
      setLoading(false);
    }
  }

  /* ── Google ── */
  async function handleGoogleRegister() {
    setApiError('');
    setGoogleLoading(true);
    try {
      const accounts = await loadGSI();
      if (!accounts) throw new Error('Google GSI yuklanmadi');

      const idToken = await new Promise((resolve, reject) => {
        accounts.id.initialize({
          client_id: GOOGLE_CLIENT_ID,
          callback: ({ credential, error }) => {
            if (credential) resolve(credential);
            else reject(new Error(error || 'Google login bekor qilindi'));
          },
        });
        accounts.id.prompt((notification) => {
          if (notification.isNotDisplayed() || notification.isSkippedMoment()) {
            accounts.oauth2.initTokenClient({
              client_id: GOOGLE_CLIENT_ID,
              scope: 'email profile',
              callback: (res) => {
                if (res.access_token) resolve(res.access_token);
                else reject(new Error('Token olinmadi'));
              },
            }).requestAccessToken();
          }
        });
      });

      await googleLogin(idToken);
      navigate(from, { replace: true });
    } catch (err) {
      setApiError(err.message || "Google orqali ro'yxatdan o'tishda xatolik yuz berdi");
    } finally {
      setGoogleLoading(false);
    }
  }

  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value });

  /* ── Render ── */
  return (
    <div className="min-h-screen bg-[#F4F6F8] flex items-center justify-center px-4 py-12">
      {/* Background blobs */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden" aria-hidden="true">
        <div className="absolute -top-40 -right-40 w-[500px] h-[500px] rounded-full bg-[#0056D6] opacity-[0.04] blur-[100px]" />
        <div className="absolute -bottom-40 -left-40 w-[400px] h-[400px] rounded-full bg-[#0056D6] opacity-[0.03] blur-[80px]" />
      </div>

      <div className="relative w-full max-w-[480px] anim-fade-up">
        <div className="bg-white rounded-2xl shadow-[0_8px_40px_rgba(0,0,0,0.10)] border border-[#E5E9F0] p-8">
          {/* Header */}
          <div className="flex flex-col items-center gap-3 mb-7">
            <Link to="/" className="flex items-center gap-2.5 group">
              <LogoIcon />
              <span className="font-display font-bold text-[20px] text-[#161C2D] tracking-tight group-hover:text-[#0056D6] transition-colors">
                ChronosAI
              </span>
            </Link>
            <div className="text-center">
              <h1 className="font-display font-bold text-[22px] text-[#161C2D] tracking-tight">
                Hisob yarating
              </h1>
              <p className="text-[14px] text-[#6B7280] mt-1">
                Bepul boshlang — karta kerak emas
              </p>
            </div>
          </div>

          {/* Google */}
          <GoogleButton onClick={handleGoogleRegister} loading={googleLoading} />

          {/* Divider */}
          <div className="flex items-center gap-3 my-5">
            <div className="flex-1 h-px bg-[#E5E9F0]" />
            <span className="text-[12px] text-[#9CA3AF] font-medium uppercase tracking-wide">yoki</span>
            <div className="flex-1 h-px bg-[#E5E9F0]" />
          </div>

          {/* Form */}
          <form id="register-form" onSubmit={handleSubmit} noValidate className="flex flex-col gap-4">
            {/* Name row */}
            <div className="grid grid-cols-2 gap-3">
              <InputField
                id="register-first-name"
                label="Ism"
                value={form.first_name}
                onChange={set('first_name')}
                placeholder="Jasur"
                autoComplete="given-name"
                error={errors.first_name}
              />
              <InputField
                id="register-last-name"
                label="Familiya"
                value={form.last_name}
                onChange={set('last_name')}
                placeholder="Toshmatov"
                autoComplete="family-name"
                error={errors.last_name}
              />
            </div>

            <InputField
              id="register-email"
              label="Email manzil"
              type="email"
              value={form.email}
              onChange={set('email')}
              placeholder="sizning@email.com"
              autoComplete="email"
              error={errors.email}
              icon={
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
              }
            />

            {/* Password + strength */}
            <div className="flex flex-col gap-1.5">
              <InputField
                id="register-password"
                label="Parol"
                type="password"
                value={form.password}
                onChange={set('password')}
                placeholder="Kamida 8 ta belgi"
                autoComplete="new-password"
                error={errors.password}
                icon={
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                }
              />
              {form.password && (
                <div className="flex items-center gap-2 mt-1">
                  <div className="flex gap-1 flex-1">
                    {[1,2,3,4].map((i) => (
                      <div
                        key={i}
                        className={`h-1 flex-1 rounded-full transition-all duration-300 ${
                          i <= strength.level ? strength.color : 'bg-[#E5E9F0]'
                        }`}
                      />
                    ))}
                  </div>
                  <span className="text-[11px] font-semibold text-[#6B7280] shrink-0">{strength.label}</span>
                </div>
              )}
            </div>

            <InputField
              id="register-password2"
              label="Parolni tasdiqlang"
              type="password"
              value={form.password2}
              onChange={set('password2')}
              placeholder="Parolni qayta kiriting"
              autoComplete="new-password"
              error={errors.password2}
              icon={
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
              }
            />

            {/* Role selection */}
            <div className="flex flex-col gap-2">
              <label className="text-[13px] font-semibold text-[#161C2D]">Rolingizni tanlang</label>
              <div className="grid grid-cols-2 gap-2.5">
                <RoleCard
                  id="role-student"
                  value="student"
                  selected={form.role === 'student'}
                  onChange={set('role')}
                  icon="🎓"
                  title="Talaba"
                  desc="Simulyatsiyalarda ishtirok etaman"
                />
                <RoleCard
                  id="role-mentor"
                  value="mentor"
                  selected={form.role === 'mentor'}
                  onChange={set('role')}
                  icon="👨‍🏫"
                  title="Mentor"
                  desc="Darslar va guruhlar boshqaraman"
                />
              </div>
            </div>

            {/* API error */}
            {apiError && (
              <div className="flex items-start gap-2.5 p-3.5 rounded-xl bg-red-50 border border-red-200">
                <svg className="w-4 h-4 text-red-500 shrink-0 mt-0.5" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
                <p className="text-[13px] text-red-600 font-medium">{apiError}</p>
              </div>
            )}

            {/* Submit */}
            <button
              id="register-submit-btn"
              type="submit"
              disabled={loading}
              className="w-full py-3.5 rounded-xl text-[15px] font-semibold text-white bg-[#0056D6] hover:bg-[#0047b3] disabled:bg-[#0056D6]/60 disabled:cursor-not-allowed shadow-[0_4px_16px_rgba(0,86,214,0.30)] hover:shadow-[0_6px_24px_rgba(0,86,214,0.42)] transition-all duration-200 hover:-translate-y-0.5 active:translate-y-0 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Ro'yxatdan o'tilmoqda...
                </>
              ) : "Ro'yxatdan o'tish"}
            </button>
          </form>

          {/* Footer link */}
          <p className="text-center text-[14px] text-[#6B7280] mt-6">
            Hisobingiz bormi?{' '}
            <Link to="/login" id="register-to-login" className="text-[#0056D6] font-semibold hover:underline">
              Tizimga kirish
            </Link>
          </p>
        </div>

        <p className="text-center text-[12px] text-[#9CA3AF] mt-5">
          Ro'yxatdan o'tish orqali siz{' '}
          <a href="/terms" className="hover:text-[#6B7280] underline underline-offset-2">Foydalanish shartlari</a>
          {' '}va{' '}
          <a href="/privacy" className="hover:text-[#6B7280] underline underline-offset-2">Maxfiylik siyosati</a>
          ga rozilik bildirasiz.
        </p>
      </div>
    </div>
  );
}
