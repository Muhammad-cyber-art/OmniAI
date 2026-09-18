import { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

/* ──────────────────────────────────────────────────────────
   Google Identity Services (GSI) loader helper
   ────────────────────────────────────────────────────────── */
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

/* ──────────────────────────────────────────────────────────
   LogoIcon
   ────────────────────────────────────────────────────────── */
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

/* ──────────────────────────────────────────────────────────
   Google Sign-in Button
   ────────────────────────────────────────────────────────── */
function GoogleButton({ onClick, loading }) {
  return (
    <button
      type="button"
      id="login-google-btn"
      onClick={onClick}
      disabled={loading}
      className="w-full flex items-center justify-center gap-3 py-3 px-4 rounded-xl border border-[#E5E9F0] bg-white hover:bg-[#F4F6F8] hover:border-[#D0D7E3] disabled:opacity-60 disabled:cursor-not-allowed transition-all duration-200 text-[15px] font-semibold text-[#161C2D] shadow-sm hover:shadow group"
    >
      {/* Google SVG logo */}
      <svg width="20" height="20" viewBox="0 0 48 48" aria-hidden="true">
        <path fill="#FFC107" d="M43.6 20.1H42V20H24v8h11.3C33.7 32.1 29.3 35 24 35c-6.1 0-11-4.9-11-11s4.9-11 11-11c2.8 0 5.3 1 7.2 2.7l5.7-5.7C33.5 7.1 29 5 24 5 12.9 5 4 13.9 4 25s8.9 20 20 20 20-8.9 20-20c0-1.3-.1-2.6-.4-3.9z" />
        <path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.7 15.4 19 12 24 12c2.8 0 5.3 1 7.2 2.7l5.7-5.7C33.5 5.8 29 4 24 4 16.3 4 9.7 8.3 6.3 14.7z" />
        <path fill="#4CAF50" d="M24 44c4.9 0 9.3-1.8 12.7-4.8l-5.9-5c-1.7 1.2-3.9 1.8-6.8 1.8-5.3 0-9.7-3-11.3-7.1l-6.5 5C9.8 39.6 16.4 44 24 44z" />
        <path fill="#1976D2" d="M43.6 20.1H42V20H24v8h11.3c-.8 2.1-2.2 3.9-3.9 5.1l5.9 5C40.9 36 44 31 44 25c0-1.3-.1-2.6-.4-3.9z" />
      </svg>
      {loading ? 'Kutilmoqda...' : 'Google orqali kirish'}
    </button>
  );
}

/* ──────────────────────────────────────────────────────────
   INPUT FIELD
   ────────────────────────────────────────────────────────── */
function InputField({ id, label, type = 'text', value, onChange, placeholder, autoComplete, error, icon }) {
  const [show, setShow] = useState(false);
  const isPassword = type === 'password';

  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="text-[13px] font-semibold text-[#161C2D]">
        {label}
      </label>
      <div className="relative">
        {icon && (
          <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#6B7280]">
            {icon}
          </span>
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
    </div>
  );
}

/* ══════════════════════════════════════════════════════════
   LOGIN PAGE
   ══════════════════════════════════════════════════════════ */
export default function LoginPage() {
  const { login, googleLogin, isAuthenticated, authError, clearAuthError } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = location.state?.from?.pathname || '/dashboard';

  const [form, setForm] = useState({ email: '', password: '' });
  const [errors, setErrors] = useState({});
  // apiError comes from AuthContext (backend error) or local validation
  const [localError, setLocalError] = useState('');
  const apiError = authError || localError;
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);

  // Already authenticated → redirect
  useEffect(() => {
    if (isAuthenticated) navigate(from, { replace: true });
  }, [isAuthenticated, navigate, from]);

  /* ── Validation ── */
  function validate() {
    const e = {};
    if (!form.email.trim()) e.email = "Email manzil kiritilishi shart";
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) e.email = "Email format noto'g'ri";
    if (!form.password) e.password = "Parol kiritilishi shart";
    else if (form.password.length < 6) e.password = "Parol kamida 6 ta belgidan iborat bo'lishi kerak";
    setErrors(e);
    return Object.keys(e).length === 0;
  }

  /* ── Email/Password submit ── */
  async function handleSubmit(e) {
    e.preventDefault();
    clearAuthError();
    setLocalError('');
    if (!validate()) return;
    setLoading(true);
    try {
      await login(form.email, form.password);
      navigate(from, { replace: true });
    } catch {
      // authError is set automatically by AuthContext
    } finally {
      setLoading(false);
    }
  }

  /* ── Google OAuth ── */
  async function handleGoogleLogin() {
    clearAuthError();
    setLocalError('');
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
      if (!authError) setLocalError(err.message || "Google orqali kirishda xatolik yuz berdi");
    } finally {
      setGoogleLoading(false);
    }
  }

  /* ── Render ── */
  return (
    <div className="min-h-screen bg-[#F4F6F8] flex items-center justify-center px-4 py-12">
      {/* Background decoration */}
      <div className="pointer-events-none fixed inset-0 overflow-hidden" aria-hidden="true">
        <div className="absolute -top-40 -right-40 w-[500px] h-[500px] rounded-full bg-[#0056D6] opacity-[0.04] blur-[100px]" />
        <div className="absolute -bottom-40 -left-40 w-[400px] h-[400px] rounded-full bg-[#0056D6] opacity-[0.03] blur-[80px]" />
      </div>

      <div className="relative w-full max-w-[420px] anim-fade-up">
        {/* Card */}
        <div className="bg-white rounded-2xl shadow-[0_8px_40px_rgba(0,0,0,0.10)] border border-[#E5E9F0] p-8">
          {/* Header */}
          <div className="flex flex-col items-center gap-3 mb-8">
            <Link to="/" className="flex items-center gap-2.5 group">
              <LogoIcon />
              <span className="font-display font-bold text-[20px] text-[#161C2D] tracking-tight group-hover:text-[#0056D6] transition-colors">
                ChronosAI
              </span>
            </Link>
            <div className="text-center">
              <h1 className="font-display font-bold text-[22px] text-[#161C2D] tracking-tight">
                Xush kelibsiz!
              </h1>
              <p className="text-[14px] text-[#6B7280] mt-1">
                Hisobingizga kirish uchun ma'lumotlarni kiriting
              </p>
            </div>
          </div>

          {/* Google button */}
          <GoogleButton onClick={handleGoogleLogin} loading={googleLoading} />

          {/* Divider */}
          <div className="flex items-center gap-3 my-5">
            <div className="flex-1 h-px bg-[#E5E9F0]" />
            <span className="text-[12px] text-[#9CA3AF] font-medium uppercase tracking-wide">yoki</span>
            <div className="flex-1 h-px bg-[#E5E9F0]" />
          </div>

          {/* Form */}
          <form id="login-form" onSubmit={handleSubmit} noValidate className="flex flex-col gap-4">
            <InputField
              id="login-email"
              label="Email manzil"
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              placeholder="sizning@email.com"
              autoComplete="email"
              error={errors.email}
              icon={
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
              }
            />

            <div className="flex flex-col gap-1.5">
              <InputField
                id="login-password"
                label="Parol"
                type="password"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                placeholder="••••••••"
                autoComplete="current-password"
                error={errors.password}
                icon={
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                }
              />
              <div className="flex justify-end">
                <Link to="/forgot-password" className="text-[12px] text-[#0056D6] font-semibold hover:underline">
                  Parolni unutdingizmi?
                </Link>
              </div>
            </div>

            {/* API Error */}
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
              id="login-submit-btn"
              type="submit"
              disabled={loading}
              className="w-full py-3.5 rounded-xl text-[15px] font-semibold text-white bg-[#0056D6] hover:bg-[#0047b3] disabled:bg-[#0056D6]/60 disabled:cursor-not-allowed shadow-[0_4px_16px_rgba(0,86,214,0.30)] hover:shadow-[0_6px_24px_rgba(0,86,214,0.42)] transition-all duration-200 hover:-translate-y-0.5 active:translate-y-0 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Kirish...
                </>
              ) : 'Tizimga kirish'}
            </button>
          </form>

          {/* Footer */}
          <p className="text-center text-[14px] text-[#6B7280] mt-6">
            Hisobingiz yo'qmi?{' '}
            <Link to="/register" id="login-to-register" className="text-[#0056D6] font-semibold hover:underline">
              Ro'yxatdan o'tish
            </Link>
          </p>
        </div>

        {/* Bottom note */}
        <p className="text-center text-[12px] text-[#9CA3AF] mt-5">
          Kirish orqali siz{' '}
          <a href="/terms" className="hover:text-[#6B7280] underline underline-offset-2">Foydalanish shartlari</a>
          {' '}va{' '}
          <a href="/privacy" className="hover:text-[#6B7280] underline underline-offset-2">Maxfiylik siyosati</a>
          ga rozilik bildirasiz.
        </p>
      </div>
    </div>
  );
}
