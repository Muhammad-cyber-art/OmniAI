"""
OmniLab AI - Simulation App Tests
Verifies simulation session lifecycle, query optimization (N+1 prevention),
instructor review override, and quota enforcement.
"""
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.curriculum.models import Domain, Course, Lesson
from apps.simulation.models import SimulationCase, SimulationSession, InstructorReview

User = get_user_model()


class SimulationTests(APITestCase):
    def setUp(self):
        self.instructor = User.objects.create_user(
            email="prof_sim@omnilab.uz",
            username="prof_sim",
            password="StrongPassword123!",
            role="INSTRUCTOR",
        )
        self.student = User.objects.create_user(
            email="student_sim@omnilab.uz",
            username="student_sim",
            password="StrongPassword123!",
            role="STUDENT",
        )
        self.domain = Domain.objects.create(
            name="Physics",
            slug="physics",
            description="Virtual mechanics and thermodynamics lab",
        )
        self.course = Course.objects.create(
            domain=self.domain,
            instructor=self.instructor,
            title="Newtonian Mechanics",
            slug="newtonian-mechanics",
            difficulty="BEGINNER",
            is_published=True,
        )
        self.lesson = Lesson.objects.create(
            course=self.course,
            title="Conservation of Momentum",
            slug="momentum",
            content="Momentum before collision equals momentum after collision.",
            is_published=True,
        )

        # Create multiple simulation cases
        self.cases = []
        for i in range(4):
            case = SimulationCase.objects.create(
                course=self.course,
                lesson=self.lesson,
                created_by=self.instructor,
                title=f"Collision Lab {i}",
                slug=f"collision-lab-{i}",
                description="Simulate elastic collision between two carts",
                role_context="You are a laboratory physicist analyzing cart velocities.",
                difficulty="BEGINNER",
                coin_reward=30,
                max_steps=5,
                passing_score=70.0,
                is_published=True,
                is_active=True,
            )
            self.cases.append(case)

    def test_simulation_case_list_no_n_plus_one(self):
        """
        GET /api/v1/simulations/cases/ uses select_related('course__domain').
        Must execute constant queries regardless of case count.
        """
        self.client.force_authenticate(user=self.student)
        url = reverse("simulation:case_list")

        with self.assertNumQueries(2):  # 1 count + 1 select with course & domain JOIN
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data["results"]), 4)
            self.assertEqual(response.data["results"][0]["domain_name"], "Physics")

    def test_start_simulation_session(self):
        """Student starts a simulation session."""
        self.client.force_authenticate(user=self.student)
        url = reverse("simulation:start_simulation")
        payload = {"case_id": str(self.cases[0].id)}
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        self.assertIn("session_id", response.data["data"])

        # Check session state in DB
        session = SimulationSession.objects.get(id=response.data["data"]["session_id"])
        self.assertEqual(session.status, SimulationSession.Status.ACTIVE)
        self.assertEqual(session.student, self.student)

    def test_my_sessions_list_no_n_plus_one(self):
        """
        GET /api/v1/simulations/my-sessions/ uses select_related('case__course__domain', 'case__lesson').
        No N+1 queries.
        """
        # Create multiple sessions for student
        for case in self.cases:
            SimulationSession.objects.create(
                student=self.student,
                case=case,
                status=SimulationSession.Status.ACTIVE,
            )

        self.client.force_authenticate(user=self.student)
        url = reverse("simulation:my_sessions")

        with self.assertNumQueries(2):  # count + select with joins
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data["results"]), 4)

    def test_instructor_review_override(self):
        """Instructor can override score for completed session."""
        session = SimulationSession.objects.create(
            student=self.student,
            case=self.cases[0],
            status=SimulationSession.Status.COMPLETED,
            total_score=60.0,
        )

        self.client.force_authenticate(user=self.instructor)
        url = reverse("simulation:instructor_review", kwargs={"session_id": str(session.id)})
        payload = {
            "override_score": 85.0,
            "override_reason": "Student showed excellent grasp of momentum formulas.",
            "instructor_feedback": "Great experimental technique!",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])

        # Verify session score was updated to override score
        session.refresh_from_db()
        self.assertEqual(session.total_score, 85.0)

        # Verify InstructorReview record
        review = InstructorReview.objects.get(session=session)
        self.assertEqual(review.original_ai_score, 60.0)
        self.assertEqual(review.override_score, 85.0)
        self.assertEqual(review.reviewer, self.instructor)


class SimulationScenarioTests(APITestCase):
    def setUp(self):
        self.mentor = User.objects.create_user(
            email="law_prof@omnilab.uz",
            username="law_prof",
            password="StrongPassword123!",
            role="INSTRUCTOR",
        )
        self.student = User.objects.create_user(
            email="law_student@omnilab.uz",
            username="law_student",
            password="StrongPassword123!",
            role="STUDENT",
        )
        self.domain = Domain.objects.create(name="Huquqshunoslik", slug="huquqshunoslik")
        self.course = Course.objects.create(
            domain=self.domain,
            instructor=self.mentor,
            title="Kriminalistika va Sud Jarayoni",
            slug="kriminalistika",
            is_published=True,
        )

    def test_mentor_can_create_scenario(self):
        self.client.force_authenticate(user=self.mentor)
        payload = {
            "course": str(self.course.id),
            "title": "Tungi do'konda o'g'rilik ishi",
            "accused_name": "Valiyev Bobur",
            "crime_details": "2026-yil 12-fevral kuni soat 23:30 da do'konga bostirib kirgan...",
            "victim_details": "Do'kon sotuvchisi Qodirov...",
            "roles_available": ["ADVOKAT", "TERGOVCHI", "PROKUROR"],
            "prompt_template": "AI talabaning vajlarini Jinoyat kodeksining 169-moddasi bo'yicha tahlil qiladi.",
            "evidence_items": ["Kuzatuv kamerasi videoyozuvi", "Barmog' izlari"],
            "laws_referenced": ["JK 169-modda", "JPK 87-modda"],
        }
        res = self.client.post("/api/v1/simulations/scenarios/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res.data["success"])
        self.assertEqual(res.data["data"]["accused_name"], "Valiyev Bobur")

    def test_student_cannot_create_scenario(self):
        self.client.force_authenticate(user=self.student)
        payload = {
            "course": str(self.course.id),
            "title": "Talaba stsenariysi",
            "accused_name": "Test",
            "crime_details": "Details",
        }
        res = self.client.post("/api/v1/simulations/scenarios/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

