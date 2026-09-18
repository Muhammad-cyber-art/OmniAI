"""
OmniLab AI - Simulation WebSocket Consumer Tests
Tests WebSocket authentication, connection lifecycle, and student turns.
"""
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.test import TransactionTestCase
from rest_framework_simplejwt.tokens import RefreshToken

from config.asgi import application
from apps.curriculum.models import Domain, Course, Lesson
from apps.simulation.models import SimulationCase, SimulationSession

User = get_user_model()


class SimulationWebSocketTests(TransactionTestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            email="ws_student@omnilab.uz",
            username="ws_student",
            password="StrongPassword123!",
            role="STUDENT",
        )
        self.other_student = User.objects.create_user(
            email="ws_other@omnilab.uz",
            username="ws_other",
            password="StrongPassword123!",
            role="STUDENT",
        )
        self.domain = Domain.objects.create(name="Biology", slug="biology")
        self.course = Course.objects.create(
            domain=self.domain,
            title="Genetics",
            slug="genetics",
            is_published=True,
        )
        self.case = SimulationCase.objects.create(
            course=self.course,
            title="Mendelian Genetics Lab",
            slug="mendel-lab",
            difficulty="BEGINNER",
            max_steps=5,
            is_published=True,
            is_active=True,
        )
        self.session = SimulationSession.objects.create(
            student=self.student,
            case=self.case,
            status=SimulationSession.Status.ACTIVE,
        )

        # Generate JWT tokens
        refresh = RefreshToken.for_user(self.student)
        self.access_token = str(refresh.access_token)

        other_refresh = RefreshToken.for_user(self.other_student)
        self.other_token = str(other_refresh.access_token)

    async def test_unauthenticated_connection_rejected(self):
        """Connecting without token is rejected with 4001."""
        path = f"/ws/simulations/{self.session.id}/"
        communicator = WebsocketCommunicator(application, path)
        connected, close_code = await communicator.connect()
        self.assertFalse(connected)
        self.assertEqual(close_code, 4001)

    async def test_authenticated_connection_success(self):
        """Connecting with valid token succeeds and receives connection_established event."""
        path = f"/ws/simulations/{self.session.id}/?token={self.access_token}"
        communicator = WebsocketCommunicator(application, path)
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # First message sent by consumer
        response = await communicator.receive_json_from()
        self.assertEqual(response["type"], "connection_established")
        self.assertEqual(response["session_id"], str(self.session.id))
        self.assertEqual(response["case_title"], "Mendelian Genetics Lab")

        # Test heartbeat ping
        await communicator.send_json_to({"type": "ping", "timestamp": 123456789})
        pong = await communicator.receive_json_from()
        self.assertEqual(pong["type"], "pong")
        self.assertEqual(pong["timestamp"], 123456789)

        await communicator.disconnect()

    async def test_other_student_cannot_access_session(self):
        """A student cannot access another student's session (code 4003)."""
        path = f"/ws/simulations/{self.session.id}/?token={self.other_token}"
        communicator = WebsocketCommunicator(application, path)
        connected, close_code = await communicator.connect()
        self.assertFalse(connected)
        self.assertEqual(close_code, 4003)
