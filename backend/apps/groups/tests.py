"""
OmniLab AI - Groups & Mentorship App Tests
Tests Group CRUD, Invite Link generation, Token verification, and Student enrollment.
"""
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.curriculum.models import Domain, Course
from apps.groups.models import Group, GroupInvitation, GroupMembership
from apps.groups.services import GroupService

User = get_user_model()


class GroupTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Users
        self.mentor = User.objects.create_user(
            email="mentor@omnilab.uz",
            username="mentor1",
            password="StrongPassword123!",
            role="INSTRUCTOR",
        )
        self.other_mentor = User.objects.create_user(
            email="other_mentor@omnilab.uz",
            username="mentor2",
            password="StrongPassword123!",
            role="INSTRUCTOR",
        )
        self.student = User.objects.create_user(
            email="student@omnilab.uz",
            username="student1",
            password="StrongPassword123!",
            role="STUDENT",
        )

        # Course
        self.domain = Domain.objects.create(name="Huquq", slug="huquq")
        self.course = Course.objects.create(
            domain=self.domain,
            instructor=self.mentor,
            title="Jinoyat Huquqi",
            slug="jinoyat-huquqi",
            is_published=True,
        )

    def test_mentor_can_create_group(self):
        self.client.force_authenticate(user=self.mentor)
        payload = {
            "name": "Yurisprudensiya 101",
            "description": "1-kurs talabalari uchun guruh",
            "course_ids": [str(self.course.id)],
        }
        res = self.client.post("/api/v1/groups/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["data"]["name"], "Yurisprudensiya 101")
        self.assertEqual(Group.objects.count(), 1)
        group = Group.objects.first()
        self.assertEqual(group.mentor, self.mentor)
        self.assertIn(self.course, group.courses.all())

    def test_student_cannot_create_group(self):
        self.client.force_authenticate(user=self.student)
        payload = {"name": "Talaba guruhi"}
        res = self.client.post("/api/v1/groups/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_generate_invite_link(self):
        group = Group.objects.create(name="Huquq Guruhi", mentor=self.mentor)
        self.client.force_authenticate(user=self.mentor)

        payload = {"expires_in_days": 10, "max_uses": 25}
        res = self.client.post(f"/api/v1/groups/{group.id}/generate-invite/", payload, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res.data["success"])
        token = res.data["data"]["token"]
        self.assertTrue(token)
        self.assertEqual(GroupInvitation.objects.filter(token=token).count(), 1)

    def test_other_mentor_cannot_generate_invite(self):
        group = Group.objects.create(name="Mentor Guruhi", mentor=self.mentor)
        self.client.force_authenticate(user=self.other_mentor)

        res = self.client.post(f"/api/v1/groups/{group.id}/generate-invite/", {}, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_user_invite_preview_sets_cookie(self):
        group = Group.objects.create(name="Ochiq Guruh", mentor=self.mentor)
        invitation = GroupService.generate_invite(group=group, creator=self.mentor)

        res = self.client.get(f"/api/v1/groups/join/{invitation.token}/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["data"]["group_name"], "Ochiq Guruh")
        # Check that pending_invite_token cookie is set
        self.assertIn("pending_invite_token", res.cookies)
        self.assertEqual(res.cookies["pending_invite_token"].value, invitation.token)

    def test_authenticated_student_can_join_group(self):
        group = Group.objects.create(name="Huquqiy Amaliyot", mentor=self.mentor)
        invitation = GroupService.generate_invite(group=group, creator=self.mentor)

        self.client.force_authenticate(user=self.student)
        res = self.client.post(f"/api/v1/groups/join/{invitation.token}/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data["success"])

        # Check membership
        self.assertTrue(GroupMembership.objects.filter(group=group, student=self.student).exists())

        # Check invitation usage count
        invitation.refresh_from_db()
        self.assertEqual(invitation.times_used, 1)

    def test_expired_invite_token_rejected(self):
        group = Group.objects.create(name="Eski Guruh", mentor=self.mentor)
        invitation = GroupInvitation.objects.create(
            group=group,
            token="expired_token_123",
            created_by=self.mentor,
            expires_at=timezone.now() - timedelta(days=1),
            is_active=True,
        )

        self.client.force_authenticate(user=self.student)
        res = self.client.post(f"/api/v1/groups/join/{invitation.token}/")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(res.data["success"])
