"""
OmniLab AI - Users & Auth App Tests
Tests authentication endpoints, registration, profile retrieval,
and verifies no N+1 queries on user listings.
"""
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class AuthAndUserTests(APITestCase):
    def setUp(self):
        # Create test users
        self.student = User.objects.create_user(
            email="student@omnilab.uz",
            username="student_user",
            password="StrongPassword123!",
            role="STUDENT",
            first_name="Test",
            last_name="Student",
            is_portfolio_public=True,
        )
        self.recruiter = User.objects.create_user(
            email="recruiter@omnilab.uz",
            username="recruiter_user",
            password="StrongPassword123!",
            role="RECRUITER",
        )
        self.admin = User.objects.create_superuser(
            email="admin@omnilab.uz",
            username="admin_user",
            password="StrongPassword123!",
        )

    def test_auth_index_get(self):
        """GET /api/v1/auth/ should return 200 with service directory."""
        url = reverse("users:index")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertIn("endpoints", response.data)

    def test_login_get_guide(self):
        """GET /api/v1/auth/login/ should return 200 with guidance, not 405 error."""
        url = reverse("users:login")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertIn("request_body_example", response.data)

    def test_register_get_guide(self):
        """GET /api/v1/auth/register/ should return 200 with schema, not 405 error."""
        url = reverse("users:register")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertIn("request_body_example", response.data)

    def test_user_registration_success(self):
        """POST /api/v1/auth/register/ should create user, wallet, quota, and profile."""
        url = reverse("users:register")
        payload = {
            "email": "newbie@omnilab.uz",
            "username": "newbie",
            "password": "Password123!",
            "password_confirm": "Password123!",
            "role": "STUDENT",
            "first_name": "New",
            "last_name": "Student",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])

        # Check DB entities
        new_user = User.objects.get(email="newbie@omnilab.uz")
        self.assertTrue(hasattr(new_user, "profile"))
        self.assertTrue(hasattr(new_user, "wallet"))
        self.assertTrue(hasattr(new_user, "quota_usage"))
        self.assertEqual(new_user.wallet.balance, 50)  # Free plan default welcome coins

    def test_login_jwt_success(self):
        """POST /api/v1/auth/login/ returns valid JWT access and refresh tokens."""
        url = reverse("users:login")
        payload = {
            "email": "student@omnilab.uz",
            "password": "StrongPassword123!",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_me_view(self):
        """GET /api/v1/auth/me/ returns authenticated user with nested profile."""
        self.client.force_authenticate(user=self.student)
        url = reverse("users:me")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "student@omnilab.uz")
        self.assertIn("profile", response.data)

    def test_user_list_admin_query_optimization(self):
        """Admin user listing uses select_related to prevent N+1 queries."""
        self.client.force_authenticate(user=self.admin)
        url = reverse("users:user_list")

        # Running query check: 1 count query + 1 select query joining profile
        with self.assertNumQueries(2):
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data["results"]), 3)

    def test_public_students_recruiter_query_optimization(self):
        """Recruiter portfolio list uses select_related to prevent N+1 queries."""
        self.client.force_authenticate(user=self.recruiter)
        url = reverse("users:public_students")

        with self.assertNumQueries(2):  # count + select with profile JOIN
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data["results"]), 1)


class GoogleAuthTests(APITestCase):
    def setUp(self):
        self.mentor = User.objects.create_user(
            email="mentor_test@omnilab.uz",
            username="mentor_test",
            password="StrongPassword123!",
            role="INSTRUCTOR",
        )
        from apps.groups.models import Group
        from apps.groups.services import GroupService
        self.group = Group.objects.create(name="Sud Jarayoni Guruh", mentor=self.mentor)
        self.invitation = GroupService.generate_invite(group=self.group, creator=self.mentor)

    def test_google_auth_new_user_login(self):
        payload = {"id_token": "mock_alibek"}
        res = self.client.post("/api/v1/auth/google/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data["success"])
        self.assertIn("tokens", res.data)
        self.assertEqual(res.data["user"]["email"], "alibek@gmail.com")

        # Verify user exists in DB and has student role
        user = User.objects.get(email="alibek@gmail.com")
        self.assertEqual(user.role, "STUDENT")

    def test_google_auth_with_invite_token_auto_joins_group(self):
        payload = {
            "id_token": "mock_karima",
            "invite_token": self.invitation.token,
        }
        res = self.client.post("/api/v1/auth/google/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(res.data["joined_group"])
        self.assertEqual(res.data["joined_group"]["group_id"], str(self.group.id))

        # Check membership in DB
        from apps.groups.models import GroupMembership
        user = User.objects.get(email="karima@gmail.com")
        self.assertTrue(GroupMembership.objects.filter(group=self.group, student=user).exists())

    def test_google_auth_with_cookie_auto_joins_and_clears_cookie(self):
        self.client.cookies["pending_invite_token"] = self.invitation.token
        payload = {"id_token": "mock_jasur"}
        res = self.client.post("/api/v1/auth/google/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(res.data["joined_group"])

        # Check cookie deleted
        self.assertEqual(res.cookies["pending_invite_token"].value, "")
