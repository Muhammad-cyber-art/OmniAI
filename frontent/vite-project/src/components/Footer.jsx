const LINKS = {
  Platforma: ['Qanday ishlaydi', 'Jonli Simulyator', "Raqobatchilar tahlili", 'Maktablar uchun'],
  Kompaniya: ["Biz haqimizda", "Blog", "Hamkorlar", "Ish o'rinlari"],
  Yordam: ["Hujjatlar", "API ma'lumotnomasi", "Qo'llab-quvvatlash", "Holat sahifasi"],
};

export default function Footer() {
  return (
    <footer className="bg-[#161C2D] text-white">
      {/* Main footer */}
      <div className="max-w-[1200px] mx-auto px-8 py-16">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-12">
          {/* Brand */}
          <div className="lg:col-span-2">
            <a href="/" className="flex items-center gap-2.5 mb-5 group">
              <div className="w-9 h-9 rounded-[10px] bg-gradient-to-br from-[#0056D6] to-[#0041A8] flex items-center justify-center shadow-[0_4px_12px_rgba(0,86,214,0.5)] transition-transform group-hover:scale-105">
                <svg width="18" height="18" viewBox="0 0 20 20" fill="none">
                  <circle cx="10" cy="10" r="4" fill="white" opacity="0.95" />
                  <circle cx="10" cy="10" r="8" stroke="white" strokeWidth="1.5" opacity="0.35" />
                </svg>
              </div>
              <span className="font-display font-bold text-[19px] text-white tracking-tight">ChronosAI</span>
            </a>
            <p className="text-white/50 text-[14px] leading-relaxed mb-6 max-w-[280px]">
              Sun'iy intellekt yordamida ta'limni interaktiv va samarali qiluvchi innovatsion platforma.
            </p>
            {/* Social icons */}
            <div className="flex gap-3">
              {[
                { label: 'Telegram', path: 'M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.562 8.248l-2.037 9.599c-.154.677-.551.843-1.115.523l-3.09-2.275-1.49 1.433c-.165.164-.303.302-.62.302l.222-3.152 5.73-5.175c.249-.222-.054-.346-.386-.124l-7.083 4.46-3.051-.953c-.663-.208-.676-.663.138-.982l11.91-4.59c.553-.203 1.037.12.872.934z' },
                { label: 'LinkedIn', path: 'M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z' },
              ].map(({ label, path }) => (
                <a
                  key={label}
                  href="#"
                  aria-label={label}
                  className="w-9 h-9 rounded-lg bg-white/10 hover:bg-[#0056D6] flex items-center justify-center transition-all duration-200 hover:scale-105"
                >
                  <svg className="w-4 h-4 fill-white" viewBox="0 0 24 24"><path d={path} /></svg>
                </a>
              ))}
            </div>
          </div>

          {/* Links */}
          {Object.entries(LINKS).map(([category, links]) => (
            <div key={category}>
              <h4 className="font-semibold text-[13px] uppercase tracking-widest text-white/40 mb-4">
                {category}
              </h4>
              <ul className="flex flex-col gap-2.5">
                {links.map((l) => (
                  <li key={l}>
                    <a
                      href="#"
                      className="text-[14px] text-white/60 hover:text-white transition-colors duration-150"
                    >
                      {l}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>

      {/* Bottom bar */}
      <div className="border-t border-white/10">
        <div className="max-w-[1200px] mx-auto px-8 py-5 flex flex-col sm:flex-row items-center justify-between gap-3 text-[13px] text-white/40">
          <p>© 2024 ChronosAI. Barcha huquqlar himoyalangan.</p>
          <div className="flex gap-5">
            <a href="#" className="hover:text-white/70 transition-colors">Maxfiylik siyosati</a>
            <a href="#" className="hover:text-white/70 transition-colors">Foydalanish shartlari</a>
          </div>
        </div>
      </div>
    </footer>
  );
}
