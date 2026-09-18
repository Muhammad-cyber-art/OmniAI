import AppleSticker from './AppleSticker';

const FEATURES = [
  {
    icon: '⚡',
    title: '15 soniyada tayyor',
    desc: "Konspekt kiritasiz — AI 15 soniya ichida to'liq simulyatsiya ssenariyini yaratib beradi.",
    color: 'bg-amber-50 text-amber-600',
  },
  {
    icon: '🎭',
    title: 'Ko\'p rollik simulyatsiya',
    desc: "Prokuror, Advokat, Sudya — har bir talaba real sud jarayonini o'z rolidagi pozitsiyasidan boshdan kechiradi.",
    color: 'bg-violet-50 text-violet-600',
  },
  {
    icon: '📊',
    title: 'Chuqur analitika',
    desc: "Har bir talabaning ko'rsatkichlari, javob aniqligi va bilim rivojlanishi real vaqtda kuzatiladi.",
    color: 'bg-emerald-50 text-emerald-600',
  },
  {
    icon: '🔗',
    title: 'Guruhlar va invite',
    desc: "Mentor bir marta havola yaratadi — talabalar shu orqali guruhga avtomatik qo'shiladi.",
    color: 'bg-blue-50 text-blue-600',
  },
  {
    icon: '🤖',
    title: 'Gemini 2.0 kuchi',
    desc: "Google Gemini 2.0 modeli yordamida hayotiy va pedagogik jihatdan to'g'ri ssenariylar yaratiladi.",
    color: 'bg-rose-50 text-rose-600',
  },
  {
    icon: '🏆',
    title: 'Quiz va baholash',
    desc: "Simulyatsiya oxirida avtomatik quiz, ball hisobi va sertifikat — hamma narsa bir tizimda.",
    color: 'bg-teal-50 text-teal-600',
  },
];

export default function Features() {
  return (
    <section id="features" className="py-24 bg-white">
      <div className="max-w-[1200px] mx-auto px-8">
        {/* Header */}
        <div className="text-center mb-16">
          <div className="inline-block text-[11px] font-bold uppercase tracking-[1.5px] text-[#0056D6] bg-[#EBF2FF] border border-[#0056D6]/20 px-4 py-2 rounded-full mb-4">
            Imkoniyatlar
          </div>
          <h2 className="font-display font-extrabold text-[#161C2D] text-[clamp(30px,4vw,46px)] tracking-tight leading-tight mb-4">
            Nima uchun <span className="gradient-text">ChronosAI?</span>
          </h2>
          <p className="text-[17px] text-[#6B7280] max-w-[520px] mx-auto leading-relaxed">
            An'anaviy ta'lim platformalaridan farqli ravishda, biz faqat o'qitmayiz — biz tajriba bertiramiz.
          </p>
        </div>

        {/* Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {FEATURES.map(({ icon, title, desc, color }, i) => (
            <div
              key={i}
              className="group p-6 rounded-2xl border border-[#E5E9F0] bg-white hover:border-[#0056D6]/25 hover:shadow-[0_12px_40px_rgba(0,0,0,0.08)] hover:-translate-y-1 transition-all duration-300"
            >
              {/* Icon */}
              <div className={`w-12 h-12 rounded-xl ${color} flex items-center justify-center mb-5 shadow-sm group-hover:scale-110 transition-transform duration-300`}>
                <AppleSticker symbol={icon} size={28} />
              </div>

              <h3 className="font-display font-bold text-[#161C2D] text-[17px] mb-2">
                {title}
              </h3>
              <p className="text-[14px] text-[#6B7280] leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>

        {/* CTA Banner */}
        <div className="mt-16 rounded-2xl bg-gradient-to-r from-[#0056D6] to-[#0081FF] p-10 flex flex-col md:flex-row items-center justify-between gap-6 shadow-[0_20px_60px_rgba(0,86,214,0.25)]">
          <div className="text-white text-center md:text-left">
            <h3 className="font-display font-extrabold text-[26px] tracking-tight mb-2">
              Bugun sinab ko'ring — bepul!
            </h3>
            <p className="text-white/70 text-[16px]">
              14 kunlik trial davomida barcha Pro imkoniyatlar ochiq.
            </p>
          </div>
          <div className="flex gap-3 shrink-0">
            <a
              href="/register"
              id="features-cta-start"
              className="inline-flex items-center gap-2 px-7 py-3.5 rounded-full text-[15px] font-semibold bg-white text-[#0056D6] hover:bg-[#EBF2FF] shadow-lg hover:shadow-xl transition-all duration-200 hover:-translate-y-0.5"
            >
              Bepul boshlash
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
