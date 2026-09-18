const STATS = [
  { value: '15 son', label: "Simulyatsiya vaqti" },
  { value: '98%', label: "Talabalar qoniqishi" },
  { value: '500+', label: "Faol o'qituvchilar" },
  { value: '12K+', label: "Bajarilgan simulyatsiyalar" },
];

const DEMO_ROLES = [
  { label: 'Prokuror', color: 'text-red-500', emoji: '⚖️' },
  { label: 'Advokat', color: 'text-emerald-500', emoji: '🛡️' },
  { label: 'Sudya', color: 'text-[#0056D6]', emoji: '🔨' },
];

const AVATARS = [
  { bg: 'bg-[#0056D6]', letter: 'U' },
  { bg: 'bg-emerald-500', letter: 'M' },
  { bg: 'bg-amber-500', letter: 'A' },
  { bg: 'bg-violet-500', letter: 'S' },
  { bg: 'bg-red-500', letter: '99+' },
];

export default function Hero() {
  return (
    <section id="hero" className="relative min-h-screen flex flex-col pt-[68px] overflow-hidden bg-white">
      {/* Decorative background */}
      <div className="pointer-events-none absolute inset-0" aria-hidden="true">
        {/* Grid */}
        <div
          className="absolute inset-0 opacity-[0.035]"
          style={{
            backgroundImage:
              'linear-gradient(#0056D6 1px,transparent 1px),linear-gradient(90deg,#0056D6 1px,transparent 1px)',
            backgroundSize: '52px 52px',
            maskImage: 'radial-gradient(ellipse 75% 75% at 50% 40%, black, transparent)',
          }}
        />
        {/* Blobs */}
        <div className="absolute -top-28 -right-28 w-[520px] h-[520px] rounded-full bg-[#0056D6] opacity-[0.055] blur-[90px]" />
        <div className="absolute bottom-32 -left-20 w-[360px] h-[360px] rounded-full bg-[#0056D6] opacity-[0.04] blur-[70px]" />
      </div>

      {/* ── Main grid ── */}
      <div className="relative flex-1 max-w-[1200px] mx-auto w-full px-8 grid lg:grid-cols-2 gap-16 items-center py-20">
        {/* ── LEFT: Content ── */}
        <div className="flex flex-col gap-7 lg:items-start items-center text-center lg:text-left">

          {/* Eyebrow badge */}
          <div
            id="hero-badge"
            className="anim-fade-up inline-flex items-center gap-2 px-4 py-2 rounded-full text-[13px] font-medium border border-[#0056D6]/20 bg-[#0056D6]/[0.06] text-[#6B7280]"
          >
            <span className="w-2 h-2 rounded-full bg-[#0056D6] anim-pulse-glow shrink-0" />
            Eksklyuziv Ta'lim Texnologiyasi
            <span className="text-[#E5E9F0]" aria-hidden="true">•</span>
            <span className="text-[#0056D6] font-semibold">Matndan Sarguzashtgacha</span>
          </div>

          {/* Heading */}
          <h1 className="anim-fade-up delay-100 font-display font-black text-[#161C2D] leading-[1.07] tracking-[-2px] text-[clamp(36px,5vw,62px)]">
            Quruq dars matnini{' '}
            <span className="gradient-text">
              jonli AI detektiv kvest
            </span>
            ga aylantiring
          </h1>

          {/* Subtitle */}
          <p className="anim-fade-up delay-200 text-[17px] leading-[1.75] text-[#6B7280] max-w-[520px]">
            O'qituvchi bitta konspekt kiritadi — sun'iy intellekt uni{' '}
            <strong className="text-[#161C2D] font-semibold">15 soniyada</strong> kinoxit syujeti,
            fotorealistik illyustratsiya va o'quvchini darsga mixlab qo'yuvchi interaktiv
            kvest-testga aylantirib beradi.
          </p>

          {/* CTAs */}
          <div className="anim-fade-up delay-300 flex flex-wrap gap-4 items-center">
            <a
              href="/register"
              id="hero-cta-start"
              className="inline-flex items-center gap-2.5 px-8 py-4 rounded-full text-[15px] font-semibold text-white bg-[#0056D6] hover:bg-[#0047b3] shadow-[0_8px_28px_rgba(0,86,214,0.30)] hover:shadow-[0_12px_36px_rgba(0,86,214,0.42)] transition-all duration-300 hover:-translate-y-0.5 active:translate-y-0"
            >
              AI Sarguzashtni Boshlash
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="M5 12h14M12 5l7 7-7 7" />
              </svg>
            </a>
            <button
              id="hero-cta-demo"
              onClick={() => document.getElementById('simulator')?.scrollIntoView({ behavior: 'smooth' })}
              className="inline-flex items-center gap-3 px-7 py-4 rounded-full text-[15px] font-semibold text-[#161C2D] border border-[#E5E9F0] hover:border-[#0056D6] hover:text-[#0056D6] hover:bg-[#EBF2FF] transition-all duration-200"
            >
              <span className="w-7 h-7 rounded-full bg-[#0056D6]/10 flex items-center justify-center text-[#0056D6] shrink-0">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z" /></svg>
              </span>
              Konsepsiya qanday ishlaydi?
            </button>
          </div>

          {/* Social proof */}
          <div className="anim-fade-up delay-400 flex items-center gap-3">
            <div className="flex items-center">
              {AVATARS.map((a, i) => (
                <div
                  key={i}
                  className={`w-8 h-8 rounded-full ${a.bg} border-2 border-white flex items-center justify-center text-white text-[10px] font-bold shadow-sm ${i > 0 ? '-ml-2' : ''}`}
                  aria-hidden="true"
                >
                  {a.letter}
                </div>
              ))}
            </div>
            <p className="text-sm text-[#6B7280]">
              <span className="font-bold text-[#161C2D]">500+</span> o'qituvchi platformada
            </p>
          </div>
        </div>

        {/* ── RIGHT: Demo Card ── */}
        <div className="relative anim-fade-up delay-300">
          {/* Floating badges */}
          <div
            aria-hidden="true"
            className="absolute -top-4 right-8 z-10 flex items-center gap-2 bg-white border border-[#E5E9F0] rounded-full px-4 py-2 text-[13px] font-semibold shadow-md anim-float"
          >
            🎯 <span>AI Tahlil</span>
          </div>
          <div
            aria-hidden="true"
            className="absolute -bottom-4 -left-4 z-10 flex items-center gap-2 bg-white border border-[#E5E9F0] rounded-full px-4 py-2 text-[13px] font-semibold shadow-md anim-float [animation-delay:1.2s]"
          >
            🔥 <span>98% aniqlik</span>
          </div>

          {/* Card */}
          <div
            id="hero-demo-card"
            className="bg-white border border-[#E5E9F0] rounded-2xl shadow-[0_24px_64px_rgba(0,0,0,0.10)] overflow-hidden hover:-translate-y-2 hover:shadow-[0_32px_80px_rgba(0,0,0,0.13)] transition-all duration-500 anim-float [animation-delay:0.5s]"
          >
            {/* Card header */}
            <div className="flex items-center gap-2.5 px-5 py-3.5 bg-[#F4F6F8] border-b border-[#E5E9F0]">
              <div className="flex gap-1.5">
                {['#FF5F57','#FEBC2E','#28C840'].map((c) => (
                  <span key={c} className="w-3 h-3 rounded-full" style={{ background: c }} />
                ))}
              </div>
              <span className="flex-1 text-center text-[12px] font-semibold text-[#6B7280]">
                ChronosAI — Jonli Demo
              </span>
              <span className="flex items-center gap-1.5 text-[11px] font-bold text-emerald-500">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 anim-pulse-glow" />
                Jonli
              </span>
            </div>

            {/* Card body */}
            <div className="p-6 flex flex-col gap-4">
              {/* Input */}
              <div className="bg-[#F4F6F8] rounded-xl p-4">
                <div className="text-[11px] font-bold uppercase tracking-wide text-[#6B7280] mb-2">
                  Siz kiritgan konspekt:
                </div>
                <p className="text-sm text-[#161C2D]">
                  <span className="text-[#0056D6] animate-pulse">|</span>
                  <em className="text-[#6B7280] not-italic"> O'zbekiston Respublikasi Jinoyat Kodeksi, 164-modda — Firibgarlik...</em>
                </p>
              </div>

              {/* Arrow */}
              <div className="flex items-center justify-center gap-2 text-[12px] font-semibold text-[#0056D6]">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#0056D6" strokeWidth="2.5"><path d="M12 5v14M5 12l7 7 7-7"/></svg>
                AI qayta ishlayapti...
              </div>

              {/* Output */}
              <div className="bg-gradient-to-br from-[#0056D6]/[0.04] to-[#0056D6]/[0.02] border border-[#0056D6]/15 rounded-xl p-4 flex flex-col gap-3">
                {/* Scene */}
                <div className="flex items-center gap-3">
                  <span className="text-2xl">🏛️</span>
                  <div className="flex-1">
                    <div className="text-[14px] font-bold text-[#161C2D]">Sud Zali — 2024, Toshkent</div>
                    <div className="text-[12px] text-[#6B7280]">Detektiv kvest generatsiya qilindi</div>
                  </div>
                  <span className="text-[11px] font-bold text-emerald-600 bg-emerald-50 px-3 py-1 rounded-full">
                    ✓ Tayyor
                  </span>
                </div>

                {/* Roles */}
                <div className="flex gap-2 flex-wrap">
                  {DEMO_ROLES.map(({ label, color, emoji }) => (
                    <div
                      key={label}
                      className={`flex items-center gap-1.5 text-[13px] font-semibold ${color} bg-white px-3 py-1.5 rounded-full border border-[#E5E9F0] shadow-sm`}
                    >
                      <span>{emoji}</span>
                      <span>{label}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Footer */}
              <div className="flex justify-between items-center border-t border-[#F0F2F5] pt-3">
                <span className="text-[12px] font-semibold text-[#0056D6]">⚡ 12.4 soniyada yaratildi</span>
                <span className="text-[11px] text-[#6B7280]">Powered by Gemini 2.0</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Stats Bar ── */}
      <div id="hero-stats" className="relative bg-[#F4F6F8] border-t border-[#E5E9F0]">
        <div className="max-w-[1200px] mx-auto px-8 py-8 grid grid-cols-2 md:grid-cols-4 gap-6">
          {STATS.map(({ value, label }, i) => (
            <div key={i} className="text-center">
              <div className="font-display font-extrabold text-[28px] tracking-tight text-[#161C2D] leading-tight">{value}</div>
              <div className="text-[13px] text-[#6B7280] mt-1">{label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
