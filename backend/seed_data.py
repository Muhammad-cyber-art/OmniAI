import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.users.models import User
from apps.curriculum.models import Domain, Course, Lesson, DifficultyLevel
from apps.curriculum.services import CurriculumService
from apps.simulation.models import SimulationCase
from apps.billing.models import SubscriptionPlan, UserSubscription, UserQuotaUsage

def seed_database():
    print("=== 1. Ensuring Subscription Plans & User Quotas ===")
    free_plan, _ = SubscriptionPlan.objects.get_or_create(
        tier="FREE",
        defaults={
            "name": "Boshlang'ich (Bepul)",
            "description": "Talabalar uchun boshlang'ich simulyatsiyalar",
            "price_uzs": 0,
            "duration_days": 365,
            "monthly_simulations": 50,
            "max_active_sessions": 3,
            "daily_ai_turns": 100,
            "welcome_coins": 50,
            "is_active": True,
        }
    )

    from django.utils import timezone
    from datetime import timedelta

    # Ensure all users have active subscription & quota
    for u in User.objects.all():
        now = timezone.now()
        sub, created = UserSubscription.objects.get_or_create(
            user=u,
            is_active=True,
            defaults={
                "plan": free_plan,
                "payment_method": "FREE_TIER",
                "started_at": now,
                "expires_at": now + timedelta(days=365),
            }
        )
        quota, q_created = UserQuotaUsage.objects.get_or_create(
            user=u,
            defaults={"plan": free_plan}
        )
        print(f"User {u.email}: Subscription {'created' if created else 'already active'}, Quota ready.")

    admin_user = User.objects.filter(role="ADMIN").first() or User.objects.first()

    print("\n=== 2. Creating Domains & Courses ===")
    # Domain 1: Cyber & Tech
    d_tech, _ = Domain.objects.get_or_create(
        slug="cybersecurity",
        defaults={
            "name": "Kiberxavfsizlik va Dasturlash",
            "description": "Axborot xavfsizligi, web himoya va xavfsiz kod yozish laboratoriyasi",
            "icon_url": "https://img.icons8.com/color/96/shield.png",
            "sort_order": 1,
        }
    )

    c_tech, _ = Course.objects.get_or_create(
        slug="web-security-lab",
        defaults={
            "domain": d_tech,
            "instructor": admin_user,
            "title": "Web Xavfsizlik va Incident Response",
            "description": "SQL Injection, XSS, autentifikatsiya zaifliklarini aniqlash va bartaraf etish bo'yicha amaliy simulyatsiyalar.",
            "difficulty": DifficultyLevel.INTERMEDIATE,
            "is_published": True,
        }
    )

    l_tech, _ = Lesson.objects.get_or_create(
        course=c_tech,
        slug="sql-injection-prevention",
        defaults={
            "title": "SQL Injection tahlili va Prepared Statements himoyasi",
            "summary": "SQL Injection xurujlari mexanizmi va ulardan himoyalanish strategiyalari.",
            "content": """SQL Injection (SQLi) — tajovuzkor tomonidan foydalanuvchi kiritadigan ma'lumotlar maydoniga zararli SQL kodlarini kiritish orqali ma'lumotlar bazasini nazoratga olish yoki ruxsatsiz ma'lumotlarni o'qish hujumi.

Asosiy belgilari:
- Kirish formasida yoki URL parametrida kutilmagan belgilar: qo'shtirnoq ('), semikolon (;), izoh belgilari (--).
- Loglarda 'OR 1=1', 'UNION SELECT' kabi SQL operatorlarining paydo bo'lishi.
- Ma'lumotlar bazasi xatolarining to'g'ridan-to'g'ri foydalanuvchi ekranida aks etishi (Error-based SQLi).

Himoyalanish choralari:
1. Parametrlashtirilgan so'rovlar (Prepared Statements / Parameterized Queries): Foydalanuvchi kiritgan ma'lumot hech qachon to'g'ridan-to'g'ri SQL so'rov matniga qo'shilmaydi, faqat parametr sifatida uzatiladi.
2. ORM (Object-Relational Mapping): Django ORM, SQLAlchemy kabi zamonaviy freymvorklardan to'g'ri foydalanish.
3. Kiritilgan ma'lumotlarni qat'iy tekshirish va filtratsiya (Input Validation & Sanitization).
4. Eng kam vakolat prinsipi (Principle of Least Privilege): Ma'lumotlar bazasi foydalanuvchisiga faqat zarur bo'lgan minimal huquqlarni berish (masalan, DROP yoki ALTER huquqlarini cheklash).""",
            "sort_order": 1,
            "is_published": True,
        }
    )

    # Embed lesson text with Gemini
    chunks_count = CurriculumService.chunk_and_embed_lesson(l_tech, re_embed=True)
    print(f"Lesson 1 embedded: {chunks_count} chunks created with Gemini embeddings.")

    # Simulation Case 1
    case1, _ = SimulationCase.objects.get_or_create(
        slug="sqli-incident-response",
        defaults={
            "course": c_tech,
            "lesson": l_tech,
            "created_by": admin_user,
            "title": "Fintech Bank Tizimida SQL Injection Hujumi Tahlili",
            "description": "Kompaniya xavfsizlik monitorida bank o'tkazmalari sahifasida shubhali SQL so'rovlar va 'OR 1=1' belgilari aniqlandi. Siz navbatchi SOC Analyst mutaxassisisiz. Hujumni tahlil qiling va bartaraf etish choralarini bayon eting.",
            "role_context": "Kiberxavfsizlik Tahlilchisi (SOC Security Analyst)",
            "grading_rubric": {
                "criteria": [
                    "Hujum vektorini to'g'ri aniqlash (SQL Injection)",
                    "Himoya va bartaraf etish choralarini ko'rsatish (Prepared Statements, ORM)",
                    "Minimal huquqlar (Least Privilege) va input sanitization tavsiyasi"
                ],
                "max_score": 100
            },
            "difficulty": "MEDIUM",
            "max_steps": 4,
            "passing_score": 70,
            "coin_reward": 25,
            "is_published": True,
            "is_active": True,
        }
    )
    print(f"Simulation Case 1 created: {case1.title}")

    # Domain 2: Law
    d_law, _ = Domain.objects.get_or_create(
        slug="law",
        defaults={
            "name": "Huquqshunoslik va Sud Amaliyoti",
            "description": "Fuqarolik, jinoyat va tijorat huquqi bo'yicha interaktiv sud ishlari simulyatsiyasi",
            "icon_url": "https://img.icons8.com/color/96/scales.png",
            "sort_order": 2,
        }
    )

    c_law, _ = Course.objects.get_or_create(
        slug="contract-law-litigation",
        defaults={
            "domain": d_law,
            "instructor": admin_user,
            "title": "Tijoriy Shartnomalar va Sud Nizolari",
            "description": "Shartnoma buzilishi, yetkazilgan zararni undirish va sud zalida himoya nutqi tayyorlash amaliyoti.",
            "difficulty": DifficultyLevel.BEGINNER,
            "is_published": True,
        }
    )

    l_law, _ = Lesson.objects.get_or_create(
        course=c_law,
        slug="breach-of-contract-remedies",
        defaults={
            "title": "Shartnomaviy majburiyatlarni bajarmaslik oqibatlari",
            "summary": "Moddiy zarar, boy berilgan foyda va penya undirish qoidalari.",
            "content": """O'zbekiston Respublikasi Fuqarolik Kodeksiga muvofiq, majburiyatni buzgan taraf ikkinchi tarafga yetkazilgan zararni to'liq qoplashi shart.

Zarar tushunchasi ikkita asosiy qismdan iborat:
1. Haqiqiy zarar (Real zarar) — huquqi buzilgan shaxsning buzilgan huquqini tiklash uchun qilgan yoki qilishi lozim bo'lgan xarajatlari, uning mol-mulki yo'qolishi yoki shikastlanishi.
2. Boy berilgan foyda (Lucrum cessans) — agar uning huquqlari buzilmaganida shaxs odatdagi fuqarolik muomalasi sharoitida olishi mumkin bo'lgan, lekin ololmay qolgan daromadlari.

Shuningdek, shartnomada ko'rsatilgan hollarda neustoyka (jarima yoki penya) undirilishi mumkin. Penya majburiyat ijrosi kechiktirilgan har bir kun uchun hisoblanadi.

Sudga da'vo arizasi bilan murojaat qilishda da'vogar shartnomaning mavjudligini, javobgar majburiyatni bajarmaganligini va aniq yetkazilgan zararning miqdorini hujjatli dalillar bilan isbotlashi shart.""",
            "sort_order": 1,
            "is_published": True,
        }
    )

    chunks_count2 = CurriculumService.chunk_and_embed_lesson(l_law, re_embed=True)
    print(f"Lesson 2 embedded: {chunks_count2} chunks created with Gemini embeddings.")

    case2, _ = SimulationCase.objects.get_or_create(
        slug="commercial-contract-breach",
        defaults={
            "course": c_law,
            "lesson": l_law,
            "created_by": admin_user,
            "title": "Tijoriy Yetkazib Berish Shartnomasi Bo'yicha Sud Ishi",
            "description": "'Texno-Savdo' MChJ ikkinchi tomon 'Smart-Invest' MChJ ga 100 mln so'mlik uskunalarni yetkazib bermadi. Da'vogar advokati sifatida sudda ishtirok eting va da'vo talablaringizni asoslang.",
            "role_context": "Da'vogar Vakili (Advokat / Huquqshunos)",
            "grading_rubric": {
                "criteria": [
                    "Haqiqiy zarar va boy berilgan foydani to'g'ri farqlash va asoslash",
                    "Shartnoma va qonun talablariga tayanish",
                    "Hujjatli dalillarni taqdim etish zaruratini ko'rsatish"
                ],
                "max_score": 100
            },
            "difficulty": "EASY",
            "max_steps": 3,
            "passing_score": 75,
            "coin_reward": 30,
            "is_published": True,
            "is_active": True,
        }
    )
    print(f"Simulation Case 2 created: {case2.title}")

    print("\nDatabase Seeding Completed Successfully!")

if __name__ == "__main__":
    seed_database()
