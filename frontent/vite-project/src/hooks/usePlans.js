import { useState, useEffect, useCallback } from 'react';
import { billingApi } from '../services/api';

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
      setPlans(data);
    } catch (err) {
      console.warn('Backend unavailable, using mock plans data.', err.message);
      // Mock data — remove once backend is running
      setPlans([
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
          price: '299000',
          currency: 'UZS',
          billing_period: 'monthly',
          description: 'Mentorlar va faol talabalar uchun',
          features: [
            'Cheksiz simulyatsiyalar',
            'Barcha kurslar',
            'Guruh boshqaruvi',
            'Kengaytirilgan AI tahlil',
            "Ustuvor qo'llab-quvvatlash",
            'API kirish imkoniyati',
          ],
          is_popular: true,
          cta_label: "Hozir Boshlash",
        },
        {
          id: 3,
          name: 'Korporativ',
          slug: 'enterprise',
          price: null,
          currency: 'UZS',
          billing_period: 'yearly',
          description: 'Yirik muassasalar uchun maxsus yechim',
          features: [
            'Cheksiz guruhlar',
            'Maxsus AI modellari',
            'LMS integratsiya',
            'Analitika paneli',
            'Shaxsiy menejer',
            "SLA kafolati",
          ],
          is_popular: false,
          cta_label: "Bog'lanish",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPlans();
  }, [fetchPlans]);

  return { plans, loading, error, refetch: fetchPlans };
}
