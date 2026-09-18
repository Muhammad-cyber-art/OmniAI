const STEPS = [
  {
    step: '01',
    icon: '📝',
    title: 'Konspektni kiriting',
    desc: "O'qituvchi oddiy dars mavzusini yoki qisqa konspektni tizimga yuklaydi — hech qanday maxsus format talab etilmaydi.",
    color: 'from-blue-50 to-blue-100/50',
    accent: 'text-[#0056D6] bg-[#EBF2FF]',
  },
  {
    step: '02',
    icon: '🤖',
    title: "AI ssenariy yaratadi",
    desc: 'Gemini 2.0 modeli 15 soniyadan kam vaqtda jonli kinoxit syujeti, rollar va savollar to\'plamini generatsiya qiladi.',
    color: 'from-violet-50 to-violet-100/50',
    accent: 'text-violet-600 bg-violet-50',
  },
  {
    step: '03',
    icon: '🎮',
    title: "Talabalar o'ynaydi",
    desc: "Talabalar detektiv, advokat yoki sudya rolida real vaqtda AI bilan muloqot qilib, bilimlarini sinab ko'radi.",
    color: 'from-emerald-50 to-emerald-100/50',
    accent: 'text-emerald-600 bg-emerald-50',
  },
  {
    step: '04',
    icon: '📊',
    title: 'Natijalar tahlili',
    desc: "Mentor har bir talabaning ko'rsatkichlarini, javoblarini va rivojlanish dinamikasini batafsil analitika panelida ko'radi.",
    color: 'from-amber-50 to-amber-100/50',
    accent: 'text-amber-600 bg-amber-50',
  },
];

export default function HowItWorks() {
  return (
    <section id="how-it-works" className="py-24 bg-white">
      <div className="max-w-[1200px] mx-auto px-8">
        {/* Header */}
        <div className="text-center mb-16">
          <div className="inline-block text-[11px] font-bold uppercase tracking-[1.5px] text-[#0056D6] bg-[#EBF2FF] border border-[#0056D6]/20 px-4 py-2 rounded-full mb-4">
            Jarayon
          </div>
          <h2 className="font-display font-extrabold text-[#161C2D] text-[clamp(30px,4vw,46px)] tracking-tight leading-tight mb-4">
            4 qadamda — darsdan{' '}
            <span className="gradient-text">jonli simulyatsiyagacha</span>
          </h2>
          <p className="text-[17px] text-[#6B7280] max-w-[540px] mx-auto leading-relaxed">
            Texnik bilim shart emas. Faqat mavzu kiriting, qolganini AI hal qiladi.
          </p>
        </div>

        {/* Steps grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {STEPS.map(({ step, icon, title, desc, color, accent }, i) => (
            <div
              key={i}
              className={`relative p-6 rounded-2xl bg-gradient-to-br ${color} border border-white hover:shadow-[0_12px_40px_rgba(0,0,0,0.10)] hover:-translate-y-1 transition-all duration-300 group`}
            >
              {/* Step number */}
              <div className="absolute top-4 right-4 text-[11px] font-black text-[#161C2D]/10 group-hover:text-[#161C2D]/15 transition-colors font-display tracking-wide">
                {step}
              </div>

              {/* Icon */}
              <div className={`w-12 h-12 rounded-xl ${accent} text-2xl flex items-center justify-center mb-4 shadow-sm`}>
                {icon}
              </div>

              {/* Connector line (desktop) */}
              {i < STEPS.length - 1 && (
                <div className="hidden lg:block absolute top-10 -right-3 w-6 h-[2px] bg-[#E5E9F0] z-10" />
              )}

              <h3 className="font-display font-bold text-[#161C2D] text-[17px] mb-2 leading-snug">
                {title}
              </h3>
              <p className="text-[14px] text-[#6B7280] leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
