import { useState } from 'react';
import { usePlans } from '../hooks/usePlans';

const CHECK_ICON = (
  <svg className="w-4 h-4 text-[#0056D6] shrink-0 mt-0.5" viewBox="0 0 20 20" fill="currentColor">
    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
  </svg>
);

function formatPrice(price, currency) {
  if (!price || price === '0') return 'Bepul';
  const num = Number(price);
  if (isNaN(num)) return price;
  return num.toLocaleString('uz-UZ') + (currency === 'UZS' ? " so'm" : ` ${currency}`);
}

export default function Pricing() {
  const { plans, loading } = usePlans();
  const [yearly, setYearly] = useState(false);

  return (
    <section id="pricing" className="py-24 bg-[#F4F6F8]">
      <div className="max-w-[1200px] mx-auto px-8">
        {/* Header */}
        <div className="text-center mb-14">
          <div className="inline-block text-[11px] font-bold uppercase tracking-[1.5px] text-[#0056D6] bg-[#EBF2FF] border border-[#0056D6]/20 px-4 py-2 rounded-full mb-4">
            Tariflar
          </div>
          <h2 className="font-display font-extrabold text-[#161C2D] text-[clamp(30px,4vw,46px)] tracking-tight leading-tight mb-4">
            O'zingizga mos <span className="gradient-text">tarifni tanlang</span>
          </h2>
          <p className="text-[17px] text-[#6B7280] max-w-[500px] mx-auto leading-relaxed mb-8">
            Barcha tariflar 14 kunlik bepul sinov muddati bilan keladi.
          </p>

          {/* Billing toggle */}
          <div className="inline-flex items-center gap-3 bg-white border border-[#E5E9F0] rounded-full p-1.5 shadow-sm">
            <button
              onClick={() => setYearly(false)}
              className={`px-5 py-2 rounded-full text-sm font-semibold transition-all duration-200 ${
                !yearly ? 'bg-[#161C2D] text-white shadow-sm' : 'text-[#6B7280] hover:text-[#161C2D]'
              }`}
            >
              Oylik
            </button>
            <button
              onClick={() => setYearly(true)}
              className={`px-5 py-2 rounded-full text-sm font-semibold transition-all duration-200 flex items-center gap-2 ${
                yearly ? 'bg-[#161C2D] text-white shadow-sm' : 'text-[#6B7280] hover:text-[#161C2D]'
              }`}
            >
              Yillik
              <span className="text-[10px] font-bold text-emerald-500 bg-emerald-50 px-2 py-0.5 rounded-full">
                -20%
              </span>
            </button>
          </div>
        </div>

        {/* Plans grid */}
        {loading ? (
          <div className="grid md:grid-cols-3 gap-6">
            {[0, 1, 2].map((i) => (
              <div key={i} className="h-[480px] bg-white rounded-2xl animate-pulse border border-[#E5E9F0]" />
            ))}
          </div>
        ) : (
          <div className="grid md:grid-cols-3 gap-6 items-stretch">
            {plans.map((plan) => {
              const isPopular = plan.is_popular;
              const isFree = !plan.price || plan.price === '0';
              const isEnterprise = plan.price === null;

              return (
                <div
                  key={plan.id}
                  id={`plan-${plan.slug}`}
                  className={`relative flex flex-col rounded-2xl transition-all duration-300 hover:-translate-y-1 ${
                    isPopular
                      ? 'bg-[#161C2D] text-white shadow-[0_24px_64px_rgba(22,28,45,0.28)] border border-[#161C2D] scale-[1.03]'
                      : 'bg-white border border-[#E5E9F0] hover:shadow-[0_16px_48px_rgba(0,0,0,0.10)] hover:border-[#0056D6]/25'
                  }`}
                >
                  {/* Popular badge */}
                  {isPopular && (
                    <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-gradient-to-r from-[#0056D6] to-[#3B9EFF] text-white text-[11px] font-bold uppercase tracking-widest px-5 py-1.5 rounded-full shadow-[0_4px_16px_rgba(0,86,214,0.40)]">
                      ⭐ Eng mashhur
                    </div>
                  )}

                  <div className="p-8 flex flex-col flex-1">
                    {/* Plan name */}
                    <div className="mb-6">
                      <h3 className={`font-display font-bold text-[20px] mb-1 ${isPopular ? 'text-white' : 'text-[#161C2D]'}`}>
                        {plan.name}
                      </h3>
                      <p className={`text-[14px] ${isPopular ? 'text-white/60' : 'text-[#6B7280]'}`}>
                        {plan.description}
                      </p>
                    </div>

                    {/* Price */}
                    <div className="mb-8 pb-6 border-b border-current/10">
                      {isEnterprise ? (
                        <div>
                          <div className={`font-display font-black text-[38px] tracking-tight ${isPopular ? 'text-white' : 'text-[#161C2D]'}`}>
                            Maxsus
                          </div>
                          <div className={`text-[13px] ${isPopular ? 'text-white/50' : 'text-[#6B7280]'}`}>
                            Narx muzokarasi asosida
                          </div>
                        </div>
                      ) : isFree ? (
                        <div>
                          <div className={`font-display font-black text-[44px] tracking-tight ${isPopular ? 'text-white' : 'text-[#161C2D]'}`}>
                            Bepul
                          </div>
                          <div className={`text-[13px] ${isPopular ? 'text-white/50' : 'text-[#6B7280]'}`}>
                            Hech qanday karta kerak emas
                          </div>
                        </div>
                      ) : (
                        <div>
                          <div className="flex items-end gap-2">
                            <span className={`font-display font-black text-[40px] tracking-tight leading-none ${isPopular ? 'text-white' : 'text-[#161C2D]'}`}>
                              {yearly
                                ? Math.round(Number(plan.price) * 0.8).toLocaleString('uz-UZ')
                                : Number(plan.price).toLocaleString('uz-UZ')}
                            </span>
                            <span className={`text-[14px] font-medium mb-1.5 ${isPopular ? 'text-white/60' : 'text-[#6B7280]'}`}>
                              so'm/oy
                            </span>
                          </div>
                          {yearly && (
                            <div className={`text-[12px] line-through ${isPopular ? 'text-white/40' : 'text-[#6B7280]/60'}`}>
                              {Number(plan.price).toLocaleString('uz-UZ')} so'm/oy
                            </div>
                          )}
                        </div>
                      )}
                    </div>

                    {/* Features */}
                    <ul className="flex flex-col gap-3 mb-8 flex-1">
                      {plan.features?.map((feature, fi) => (
                        <li key={fi} className="flex items-start gap-2.5 text-[14px]">
                          <span className={isPopular ? 'text-[#3B9EFF]' : ''}>
                            {isPopular ? (
                              <svg className="w-4 h-4 shrink-0 mt-0.5" viewBox="0 0 20 20" fill="currentColor">
                                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                              </svg>
                            ) : CHECK_ICON}
                          </span>
                          <span className={isPopular ? 'text-white/80' : 'text-[#6B7280]'}>{feature}</span>
                        </li>
                      ))}
                    </ul>

                    {/* CTA */}
                    <a
                      href={isEnterprise ? '/contact' : '/register'}
                      id={`plan-cta-${plan.slug}`}
                      className={`w-full text-center py-3.5 rounded-full text-[15px] font-semibold transition-all duration-200 ${
                        isPopular
                          ? 'bg-[#0056D6] text-white hover:bg-[#0047b3] shadow-[0_6px_20px_rgba(0,86,214,0.35)] hover:shadow-[0_10px_28px_rgba(0,86,214,0.50)] hover:-translate-y-0.5'
                          : 'bg-[#161C2D] text-white hover:bg-[#0056D6] hover:-translate-y-0.5'
                      }`}
                    >
                      {plan.cta_label || "Boshlash"}
                    </a>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Footer note */}
        <p className="text-center text-[13px] text-[#6B7280] mt-10">
          Barcha narxlar QQS bilan. Istalgan vaqt bekor qilish mumkin. 
          <a href="/contact" className="text-[#0056D6] font-semibold hover:underline ml-1">Savollaringiz bormi?</a>
        </p>
      </div>
    </section>
  );
}
