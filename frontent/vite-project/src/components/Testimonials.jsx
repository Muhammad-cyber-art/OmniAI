const TESTIMONIALS = [
  {
    name: "Dilnoza Yusupova",
    role: "Huquq fani o'qituvchisi, ToshDYuI",
    avatar: "DY",
    color: "bg-[#0056D6]",
    text: "ChronosAI mening darslarimni butunlay o'zgartirdi. Talabalarim endi qonunni nafaqat o'qiydi — ular uni jonli vaziyatlarda qo'llaydi. Natijalar ajoyib.",
    rating: 5,
  },
  {
    name: "Jasur Toshmatov",
    role: "Mentor, Online Huquq Akademiyasi",
    avatar: "JT",
    color: "bg-emerald-500",
    text: "Guruh boshqaruvi va invite tizimi juda qulay. 50 ta talabani bir platformada boshqaraman, hamma narsa avtomatik. Vaqtim ikki barobarga oshdi.",
    rating: 5,
  },
  {
    name: "Malika Rahimova",
    role: "3-kurs talabasi, Toshkent Huquq universiteti",
    avatar: "MR",
    color: "bg-violet-500",
    text: "Birinchi simulyatsiyada 'Advokat' rolini o'ynaganimda qo'llarim titradi — xuddi real sudday his etdim. Keyinchalik imtihonga xotirjam kirdim.",
    rating: 5,
  },
];

const STARS = (count) =>
  Array.from({ length: count }).map((_, i) => (
    <svg key={i} className="w-4 h-4 text-amber-400" viewBox="0 0 20 20" fill="currentColor">
      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
    </svg>
  ));

export default function Testimonials() {
  return (
    <section id="testimonials" className="py-24 bg-[#F4F6F8]">
      <div className="max-w-[1200px] mx-auto px-8">
        {/* Header */}
        <div className="text-center mb-16">
          <div className="inline-block text-[11px] font-bold uppercase tracking-[1.5px] text-[#0056D6] bg-[#EBF2FF] border border-[#0056D6]/20 px-4 py-2 rounded-full mb-4">
            Fikrlar
          </div>
          <h2 className="font-display font-extrabold text-[#161C2D] text-[clamp(30px,4vw,46px)] tracking-tight leading-tight mb-4">
            Foydalanuvchilar nima <span className="gradient-text">deydi?</span>
          </h2>
        </div>

        {/* Cards */}
        <div className="grid md:grid-cols-3 gap-6">
          {TESTIMONIALS.map(({ name, role, avatar, color, text, rating }, i) => (
            <div
              key={i}
              className="bg-white border border-[#E5E9F0] rounded-2xl p-7 flex flex-col gap-5 hover:shadow-[0_12px_40px_rgba(0,0,0,0.08)] hover:-translate-y-1 transition-all duration-300"
            >
              {/* Stars */}
              <div className="flex gap-0.5">{STARS(rating)}</div>

              {/* Quote */}
              <p className="text-[15px] text-[#6B7280] leading-relaxed flex-1">
                "{text}"
              </p>

              {/* Author */}
              <div className="flex items-center gap-3 pt-4 border-t border-[#F0F2F5]">
                <div className={`w-10 h-10 rounded-full ${color} flex items-center justify-center text-white text-[13px] font-bold shrink-0`}>
                  {avatar}
                </div>
                <div>
                  <div className="font-semibold text-[14px] text-[#161C2D]">{name}</div>
                  <div className="text-[12px] text-[#6B7280]">{role}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
