import { useState, useEffect, useCallback } from 'react';
import { billingApi } from '../services/api';

const MOCK_PLANS = [
  {
    id: 1,
    name: "Boshlang'ich",
    slug: 'starter',
    price: '0',
    currency: 'UZS',
    billing_period: 'monthly',
    description: "O'rganish uchun bepul tarif",
    features: [
      '5 ta simulyatsiya/oy',
      '2 ta kurs',
      'Asosiy AI yordamchi',
      'Email qo\'llab-quvvatlash',
    ],
    is_popular: false,
    cta_label: "Bepul Boshlash",
  },
  {
    id: 2,
    name: 'Professional',
    slug: 'professional',
    price: '199000',
    currency: 'UZS',
    billing_period: 'monthly',
    description: 'Mentorlar va faol talabalar uchun',
    features: [
      '25 ta simulyatsiya/oy',
      '50 ta kunlik AI suhbat',
      '15 ta bepul maslahat (hint)',
      'Barcha kurslar va guruh boshqaruvi',
      'Kengaytirilgan AI tahlil',
      "Ustuvor qo'llab-quvvatlash",
    ],
    is_popular: true,
    cta_label: "Hozir Boshlash",
  },
  {
    id: 3,
    name: 'Premium',
    slug: 'premium',
    price: '399000',
    currency: 'UZS',
    billing_period: 'monthly',
    description: 'Yirik muassasalar va professional jamoalar uchun',
    features: [
      '100 ta simulyatsiya/oy',
      '200 ta kunlik AI suhbat',
      '50 ta bepul maslahat (hint)',
      'Cheksiz guruhlar va maxsus AI modellari',
      'LMS integratsiya va to\'liq analitika',
      'Shaxsiy kurator va 24/7 yordam',
    ],
    is_popular: false,
    cta_label: "Tanlash",
  },
];

function mapBackendPlan(plan) {
  const isFree = plan.tier === 'FREE' || Number(plan.price_uzs) === 0;
  const isStandard = plan.tier === 'STANDARD';
  const isPremium = plan.tier === 'PREMIUM';

  const defaultFeatures = isFree
    ? [
        `${plan.monthly_simulations || 5} ta simulyatsiya/oy`,
        `${plan.daily_ai_turns || 10} ta kunlik AI suhbat`,
        `${plan.free_hints || 3} ta bepul maslahat (hint)`,
        'Asosiy kurslar va sinovlar',
        'Email qo\'llab-quvvatlash',
      ]
    : isStandard
    ? [
        `${plan.monthly_simulations || 25} ta simulyatsiya/oy`,
        `${plan.daily_ai_turns || 50} ta kunlik AI suhbat`,
        `${plan.free_hints || 15} ta bepul maslahat`,
        'Barcha kurslar va guruh boshqaruvi',
        'Kengaytirilgan AI tahlil',
        "Ustuvor qo'llab-quvvatlash",
      ]
    : [
        `${plan.monthly_simulations || 100} ta simulyatsiya/oy`,
        `${plan.daily_ai_turns || 200} ta kunlik AI suhbat`,
        `${plan.free_hints || 50} ta bepul maslahat`,
        'Cheksiz guruhlar va maxsus modellar',
        'LMS integratsiya va analitika paneli',
        'Shaxsiy kurator va 24/7 yordam',
      ];

  return {
    id: plan.id,
    name: plan.name || (isFree ? "Boshlang'ich" : isStandard ? "Professional" : "Premium"),
    slug: plan.tier ? plan.tier.toLowerCase() : (plan.slug || 'plan'),
    tier: plan.tier,
    price: plan.price_uzs !== undefined ? String(plan.price_uzs) : (plan.price !== undefined ? String(plan.price) : '0'),
    currency: 'UZS',
    billing_period: 'monthly',
    description: plan.description || (isFree ? "O'rganish uchun bepul tarif" : isStandard ? "Mentorlar va faol talabalar uchun" : "Yirik muassasalar va jamoalar uchun"),
    features: (Array.isArray(plan.features) && plan.features.length > 0) ? plan.features : defaultFeatures,
    is_popular: isStandard || Boolean(plan.is_popular),
    cta_label: isFree ? "Bepul Boshlash" : isStandard ? "Hozir Boshlash" : "Tanlash",
  };
}

/**
 * Hook to fetch billing plans from the backend.
 * Falls back to static mock data if the API is unavailable.
 */
export function usePlans() {
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchPlans = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await billingApi.getPlans();
      const rawList = Array.isArray(data) ? data : (data?.results || []);
      if (rawList.length > 0) {
        setPlans(rawList.map(mapBackendPlan));
      } else {
        setPlans(MOCK_PLANS);
      }
    } catch (err) {
      console.warn('Backend unavailable, using mock plans data.', err.message);
      setPlans(MOCK_PLANS);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPlans();
  }, [fetchPlans]);

  return { plans, loading, error, refetch: fetchPlans };
}
