"""
OmniLab AI - Simulation Real-Time WebSocket Consumer
Provides real-time student-AI interaction, streaming step evaluation,
live score updates, and instructor live-monitoring.
"""
import logging
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


class SimulationConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for live interactive simulations.
    Endpoint: ws://<host>/ws/simulations/<uuid:session_id>/?token=<jwt_access_token>
    """

    async def connect(self):
        self.session_id = str(self.scope["url_route"]["kwargs"]["session_id"])
        self.room_group_name = f"simulation_{self.session_id}"
        self.user = self.scope.get("user")

        # 1. Authentication check
        if not self.user or not self.user.is_authenticated:
            logger.warning("WebSocket connect rejected: unauthenticated for session %s", self.session_id)
            await self.close(code=4001)
            return

        # 2. Permission and session validity check
        session_info = await self.get_and_validate_session(self.session_id, self.user)
        if not session_info:
            logger.warning("WebSocket connect rejected: permission denied for user %s on session %s", self.user.email, self.session_id)
            await self.close(code=4003)
            return

        # 3. Join group room for this simulation session
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )

        await self.accept()

        # 4. Send initial connection success state
        await self.send_json({
            "type": "connection_established",
            "session_id": self.session_id,
            "status": session_info["status"],
            "case_title": session_info["case_title"],
            "current_step": session_info["current_step"],
            "total_score": session_info["total_score"],
            "steps_taken": session_info["steps_taken"],
            "max_steps": session_info["max_steps"],
            "user_role": self.user.role,
        })
        logger.info("WebSocket connected: user %s to simulation %s", self.user.email, self.session_id)

    async def disconnect(self, close_code):
        # Leave room group
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name,
            )
        logger.info("WebSocket disconnected: %s from %s (code=%s)", getattr(self, "user", "anonymous"), getattr(self, "session_id", "none"), close_code)

    async def receive_json(self, content, **kwargs):
        """
        Handle incoming messages from client.
        Supported message types:
        - student_turn: { "type": "student_turn", "input": "..." }
        - request_hint: { "type": "request_hint" }
        - abandon:      { "type": "abandon" }
        - ping:         { "type": "ping" }
        """
        msg_type = content.get("type")

        # Heartbeat ping
        if msg_type == "ping":
            await self.send_json({"type": "pong", "timestamp": content.get("timestamp")})
            return

        # Student turn evaluation
        if msg_type == "student_turn":
            await self.handle_student_turn(content)
            return

        # Hint consumption
        if msg_type == "request_hint":
            await self.handle_request_hint()
            return

        # Abandon simulation session
        if msg_type == "abandon":
            await self.handle_abandon_session()
            return

        await self.send_json({
            "type": "error",
            "code": "UNKNOWN_ACTION",
            "message": f"Unsupported message type: '{msg_type}'",
        })

    async def handle_student_turn(self, content):
        student_input = content.get("input", "").strip()
        if not student_input:
            await self.send_json({
                "type": "error",
                "code": "INVALID_INPUT",
                "message": "Student input cannot be empty.",
            })
            return

        # Notify room that evaluation has begun (typing/processing indicator)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "simulation_broadcast",
                "data": {
                    "type": "evaluating",
                    "message": "AI is analyzing student action...",
                },
            },
        )

        try:
            result = await self.process_turn_async(self.session_id, self.user, student_input)

            # Broadcast turn completion to everyone in the room (student + any watching instructors)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "simulation_broadcast",
                    "data": {
                        "type": "turn_result",
                        "data": result,
                    },
                },
            )
        except PermissionError as e:
            await self.send_json({
                "type": "error",
                "code": "QUOTA_EXCEEDED",
                "message": str(e),
            })
        except ValueError as e:
            await self.send_json({
                "type": "error",
                "code": "INVALID_STATE",
                "message": str(e),
            })
        except Exception as e:
            logger.exception("WS simulation evaluation error: %s", e)
            await self.send_json({
                "type": "error",
                "code": "AI_EVALUATION_FAILED",
                "message": "AI evaluation failed. Please try again.",
            })

    async def handle_request_hint(self):
        try:
            hint_data = await self.consume_hint_async(self.session_id, self.user)
            await self.send_json({
                "type": "hint_result",
                "data": hint_data,
            })
        except Exception as e:
            await self.send_json({
                "type": "error",
                "code": "HINT_FAILED",
                "message": str(e),
            })

    async def handle_abandon_session(self):
        try:
            await self.abandon_session_async(self.session_id, self.user)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "simulation_broadcast",
                    "data": {
                        "type": "session_abandoned",
                        "message": "This simulation session has been abandoned.",
                    },
                },
            )
        except Exception as e:
            await self.send_json({
                "type": "error",
                "code": "ABANDON_FAILED",
                "message": str(e),
            })

    # Group message handler: sends payload to WebSocket client
    async def simulation_broadcast(self, event):
        await self.send_json(event["data"])

    # ── Database Sync Helpers ──────────────────────────────────────────────────

    @database_sync_to_async
    def get_and_validate_session(self, session_id: str, user):
        from apps.simulation.models import SimulationSession

        try:
            session = (
                SimulationSession.objects
                .select_related("case", "student")
                .get(id=session_id)
            )
            # Permission check: student owner or instructor/admin
            if session.student != user and user.role not in ("INSTRUCTOR", "ADMIN"):
                return None

            return {
                "id": str(session.id),
                "status": session.status,
                "case_title": session.case.title,
                "current_step": session.current_step,
                "total_score": session.total_score,
                "steps_taken": session.steps_taken,
                "max_steps": session.case.max_steps,
            }
        except (SimulationSession.DoesNotExist, Exception):
            return None

    @database_sync_to_async
    def process_turn_async(self, session_id: str, user, student_input: str):
        from apps.simulation.services import SimulationEngineService
        return SimulationEngineService.process_turn(session_id, user, student_input)

    @database_sync_to_async
    def consume_hint_async(self, session_id: str, user):
        from apps.simulation.models import SimulationSession
        from apps.billing.services import BillingService

        session = SimulationSession.objects.select_related("case").get(id=session_id)
        success, message, coins_spent = BillingService.consume_hint(user, session)
        if not success:
            raise ValueError(message)
        return {
            "success": True,
            "message": message,
            "coins_spent": coins_spent,
            "hint": session.case.hint_text or "No specific hint provided for this case.",
        }

    @database_sync_to_async
    def abandon_session_async(self, session_id: str, user):
        from apps.simulation.services import SimulationEngineService
        return SimulationEngineService.abandon_session(session_id, user)
