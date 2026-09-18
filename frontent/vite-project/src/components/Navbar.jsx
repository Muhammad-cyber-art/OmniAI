import { useState, useEffect, useRef } from 'react';

const NAV_LINKS = [
  { label: 'Qanday ishlaydi', href: '#how-it-works' },
  { label: 'Jonli Simulyator', href: '#simulator' },
  { label: "Raqobatchilar tahlili", href: '#compare' },
  { label: 'Maktablar uchun', href: '#enterprise' },
];

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  useEffect(() => {
    const handler = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setMobileOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  return (
    <header
      ref={ref}
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 glass ${
        scrolled
          ? 'border-b border-[#E5E9F0] shadow-[0_1px_20px_rgba(0,0,0,0.06)]'
          : 'border-b border-transparent'
      }`}
    >
      <div className="max-w-[1200px] mx-auto px-8 h-[68px] flex items-center gap-8">
        {/* Logo */}
        <a href="/" id="nav-logo" className="flex items-center gap-2.5 shrink-0 group">
          <div className="w-9 h-9 rounded-[10px] bg-gradient-to-br from-[#0056D6] to-[#0041A8] flex items-center justify-center shadow-[0_4px_12px_rgba(0,86,214,0.35)] transition-transform duration-300 group-hover:scale-105 group-hover:-rotate-3">
            <svg width="18" height="18" viewBox="0 0 20 20" fill="none">
              <circle cx="10" cy="10" r="4" fill="white" opacity="0.95" />
              <circle cx="10" cy="10" r="8" stroke="white" strokeWidth="1.5" opacity="0.35" />
            </svg>
          </div>
          <span className="font-display font-bold text-[19px] text-[#161C2D] tracking-tight">
            ChronosAI
          </span>
        </a>

        {/* Desktop Nav */}
        <nav className="hidden lg:flex items-center gap-1 flex-1 justify-center">
          {NAV_LINKS.map((l) => (
            <a
              key={l.href}
              href={l.href}
              className="text-sm font-medium text-[#6B7280] hover:text-[#161C2D] hover:bg-[#F4F6F8] px-3.5 py-2 rounded-lg transition-all duration-150"
            >
              {l.label}
            </a>
          ))}
        </nav>

        {/* Actions */}
        <div className="hidden md:flex items-center gap-2.5 shrink-0">
          <span
            id="nav-beta-badge"
            className="text-[10px] font-bold tracking-widest uppercase text-[#0056D6] bg-[#EBF2FF] border border-[#0056D6]/20 px-2.5 py-1.5 rounded-md"
          >
            PRIVATE BETA 2.0
          </span>
          <a
            href="/login"
            id="nav-login-btn"
            className="text-sm font-semibold text-[#161C2D] border border-[#E5E9F0] hover:border-[#0056D6] hover:text-[#0056D6] hover:bg-[#EBF2FF] px-5 py-2 rounded-full transition-all duration-200"
          >
            Tizimga kirish
          </a>
          <a
            href="/register"
            id="nav-register-btn"
            className="text-sm font-semibold text-white bg-[#0056D6] hover:bg-[#0047b3] px-5 py-2 rounded-full shadow-[0_4px_16px_rgba(0,86,214,0.30)] hover:shadow-[0_6px_24px_rgba(0,86,214,0.40)] transition-all duration-200 hover:-translate-y-0.5"
          >
            Ro'yxatdan o'tish
          </a>
        </div>

        {/* Hamburger */}
        <button
          id="nav-mobile-menu-btn"
          onClick={() => setMobileOpen(!mobileOpen)}
          aria-label="Menyuni ochish"
          className="md:hidden ml-auto flex flex-col gap-[5px] p-2 rounded-lg hover:bg-[#F4F6F8] transition-colors"
        >
          <span className={`block w-5 h-[2px] bg-[#161C2D] rounded transition-all duration-300 ${mobileOpen ? 'translate-y-[7px] rotate-45' : ''}`} />
          <span className={`block w-5 h-[2px] bg-[#161C2D] rounded transition-all duration-300 ${mobileOpen ? 'opacity-0 scale-x-0' : ''}`} />
          <span className={`block w-5 h-[2px] bg-[#161C2D] rounded transition-all duration-300 ${mobileOpen ? '-translate-y-[7px] -rotate-45' : ''}`} />
        </button>
      </div>

      {/* Mobile Menu */}
      {mobileOpen && (
        <div id="nav-mobile-menu" className="md:hidden border-t border-[#E5E9F0] bg-white px-6 py-4 anim-fade-up">
          <nav className="flex flex-col gap-1 mb-4">
            {NAV_LINKS.map((l) => (
              <a
                key={l.href}
                href={l.href}
                onClick={() => setMobileOpen(false)}
                className="text-[15px] font-medium text-[#6B7280] hover:text-[#161C2D] hover:bg-[#F4F6F8] px-3 py-2.5 rounded-lg transition-all"
              >
                {l.label}
              </a>
            ))}
          </nav>
          <div className="flex gap-3">
            <a href="/login" className="flex-1 text-center text-sm font-semibold border border-[#E5E9F0] hover:border-[#0056D6] text-[#161C2D] hover:text-[#0056D6] py-2.5 rounded-full transition-all">
              Kirish
            </a>
            <a href="/register" className="flex-1 text-center text-sm font-semibold text-white bg-[#0056D6] py-2.5 rounded-full shadow-[0_4px_12px_rgba(0,86,214,0.25)] transition-all">
              Ro'yxatdan o'tish
            </a>
          </div>
        </div>
      )}
    </header>
  );
}
