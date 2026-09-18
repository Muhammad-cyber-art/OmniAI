"""
OmniLab AI - Curriculum App Tests
Verifies domain, course, and lesson CRUD, RBAC,
and validates that querysets avoid N+1 queries.
"""
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.curriculum.models import Domain, Course, Lesson

User = get_user_model()


class CurriculumTests(APITestCase):
    def setUp(self):
        self.instructor = User.objects.create_user(
            email="instructor@omnilab.uz",
            username="instructor_user",
            password="StrongPassword123!",
            role="INSTRUCTOR",
            first_name="Prof",
            last_name="Einstein",
        )
        self.student = User.objects.create_user(
            email="student_curr@omnilab.uz",
            username="student_curr",
            password="StrongPassword123!",
            role="STUDENT",
        )
        self.domain = Domain.objects.create(
            name="Medicine",
            slug="medicine",
            description="Medical clinical reasoning and diagnostic simulations",
        )

        # Create multiple courses
        self.courses = []
        for i in range(5):
            c = Course.objects.create(
                domain=self.domain,
                instructor=self.instructor,
                title=f"Clinical Cardiology {i}",
                slug=f"cardiology-{i}",
                description="Heart diagnosis course",
                difficulty="INTERMEDIATE",
                is_published=True,
            )
            self.courses.append(c)

        # Create lessons for the first course
        for j in range(4):
            Lesson.objects.create(
                course=self.courses[0],
                title=f"Lesson {j}: ECG Interpretation",
                slug=f"ecg-{j}",
                content="Full text content of ECG reading...",
                summary="ECG basics",
                sort_order=j,
                is_published=True,
            )

    def test_domain_list(self):
        """GET /api/v1/curriculum/domains/ lists active domains."""
        self.client.force_authenticate(user=self.student)
        url = reverse("curriculum:domain_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        items = response.data["results"] if "results" in response.data else response.data
        self.assertGreaterEqual(len(items), 1)
        slugs = [d["slug"] for d in items]
        self.assertIn("medicine", slugs)

    def test_course_list_no_n_plus_one(self):
        """
        GET /api/v1/curriculum/courses/ uses select_related('domain', 'instructor').
        Query count must be constant (2 queries: 1 count + 1 select) regardless of course count.
        """
        self.client.force_authenticate(user=self.student)
        url = reverse("curriculum:course_list")

        with self.assertNumQueries(2):
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data["results"]), 5)
            # Verify serialized data contains joined fields
            self.assertEqual(response.data["results"][0]["domain_name"], "Medicine")
            self.assertEqual(response.data["results"][0]["instructor_name"], "Prof Einstein")

    def test_lesson_list_no_n_plus_one(self):
        """
        GET /api/v1/curriculum/courses/<course_slug>/lessons/
        Query count must be constant (2 queries: 1 count + 1 select).
        """
        self.client.force_authenticate(user=self.student)
        url = reverse("curriculum:lesson_list", kwargs={"course_slug": "cardiology-0"})

        with self.assertNumQueries(2):
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data["results"]), 4)

    def test_student_cannot_create_course(self):
        """Students cannot create courses (HTTP 403 Forbidden)."""
        self.client.force_authenticate(user=self.student)
        url = reverse("curriculum:course_list")
        payload = {
            "domain": self.domain.id,
            "title": "Unauthorized Course",
            "slug": "unauthorized-course",
            "description": "Test",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_instructor_can_create_course(self):
        """Instructors can create courses."""
        self.client.force_authenticate(user=self.instructor)
        url = reverse("curriculum:course_list")
        payload = {
            "domain": self.domain.id,
            "title": "Neurology Basics",
            "slug": "neurology-basics",
            "description": "Brain anatomy and reflex testing",
            "difficulty": "BEGINNER",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Course.objects.filter(slug="neurology-basics").exists())


class QuizTests(APITestCase):
    def setUp(self):
        self.instructor = User.objects.create_user(
            email="quiz_prof@omnilab.uz",
            username="quiz_prof",
            password="StrongPassword123!",
            role="INSTRUCTOR",
        )
        self.student = User.objects.create_user(
            email="quiz_student@omnilab.uz",
            username="quiz_student",
            password="StrongPassword123!",
            role="STUDENT",
        )
        self.domain = Domain.objects.create(name="Huquq", slug="huquq-quiz")
        self.course = Course.objects.create(
            domain=self.domain,
            instructor=self.instructor,
            title="Jinoyat Moddalari",
            slug="jinoyat-moddalari",
            is_published=True,
        )
        self.lesson = Lesson.objects.create(
            course=self.course,
            title="1-Dars: Zaruriy Mudofaa",
            slug="zaruriy-mudofaa",
            content="Zaruriy mudofaa chegarasi buzilmagan taqdirda javobgarlik bo'lmaydi.",
            is_published=True,
        )

    def test_mentor_create_quiz_and_student_submit(self):
        # 1. Mentor creates quiz
        self.client.force_authenticate(user=self.instructor)
        quiz_payload = {
            "title": "Zaruriy mudofaa bo'yicha test",
            "description": "Bilimlarni sinash",
            "time_limit_minutes": 10,
            "passing_score": 50,
        }
        res = self.client.post(f"/api/v1/curriculum/lessons/{self.lesson.id}/quizzes/", quiz_payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        quiz_id = res.data["data"]["id"]

        # 2. Mentor adds question with options
        q_payload = {
            "text": "JK 37-moddasiga ko'ra zaruriy mudofaa holatida yetkazilgan zarar qilmish deb topiladimi?",
            "explanation": "Zaruriy mudofaa holatida qilingan harakat jinoyat deb topilmaydi.",
            "points": 10,
            "options": [
                {"text": "Yo'q, jinoyat deb topilmaydi", "is_correct": True},
                {"text": "Ha, doimo jinoyat hisoblanadi", "is_correct": False},
            ],
        }
        res = self.client.post(f"/api/v1/curriculum/quizzes/{quiz_id}/questions/", q_payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        q_id = res.data["data"]["id"]
        correct_option_id = [opt["id"] for opt in res.data["data"]["options"] if opt.get("is_correct")][0]

        # 3. Student submits correct answer
        self.client.force_authenticate(user=self.student)
        submit_payload = {
            "answers": {
                str(q_id): str(correct_option_id),
            }
        }
        res = self.client.post(f"/api/v1/curriculum/quizzes/{quiz_id}/submit/", submit_payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["data"]["score"], 100.0)
        self.assertTrue(res.data["data"]["is_passed"])

