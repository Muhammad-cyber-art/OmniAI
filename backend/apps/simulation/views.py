"""
OmniLab AI - Simulation Views
Case browsing, session management, turn processing, instructor review.
"""
import logging
from rest_framework import generics, views, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.users.permissions import IsStudent, IsInstructorOrAdmin, IsAdminUser, HasActiveQuota
from .models import SimulationCase, SimulationSession, InstructorReview, SimulationScenario
from .serializers import (
    SimulationCaseListSerializer,
    SimulationCaseDetailSerializer,
    SimulationCaseWriteSerializer,
    SimulationSessionListSerializer,
    SimulationSessionDetailSerializer,
    StartSimulationSerializer,
    TurnInputSerializer,
    InstructorReviewSerializer,
    InstructorReviewWriteSerializer,
    SimulationScenarioSerializer,
    SimulationScenarioWriteSerializer,
)
from .services import SimulationEngineService

logger = logging.getLogger(__name__)


# ── Simulation Cases ───────────────────────────────────────────────────────────

class SimulationCaseListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/v1/simulations/cases/       → browse available cases
    POST /api/v1/simulations/cases/       → create case (instructor/admin)
    """
    filterset_fields = ["course__domain__slug", "difficulty", "is_published"]
    search_fields = ["title", "description"]
    ordering_fields = ["difficulty", "coin_reward", "created_at"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return SimulationCaseWriteSerializer
        return SimulationCaseListSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsInstructorOrAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = SimulationCase.objects.select_related("course__domain", "course__instructor")
        if self.request.user.role in ("STUDENT", "RECRUITER"):
            qs = qs.filter(is_published=True, is_active=True)
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            {"success": True, "data": serializer.data},
            status=status.HTTP_201_CREATED,
        )


class SimulationCaseDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/v1/simulations/cases/<slug>/
    PATCH  /api/v1/simulations/cases/<slug>/  (instructor/admin)
    DELETE /api/v1/simulations/cases/<slug>/  (admin)
    """
    lookup_field = "slug"

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return SimulationCaseWriteSerializer
        return SimulationCaseDetailSerializer

    def get_permissions(self):
        if self.request.method in ("PUT", "PATCH", "DELETE"):
            return [IsInstructorOrAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = SimulationCase.objects.select_related("course__domain", "course__instructor", "lesson")
        if self.request.user.role in ("STUDENT", "RECRUITER"):
            qs = qs.filter(is_published=True, is_active=True)
        return qs


# ── Session Management ─────────────────────────────────────────────────────────

class StartSimulationView(views.APIView):
    """
    POST /api/v1/simulations/start/
    Student starts a new simulation session.
    Quota, subscription, and session-limit checks applied.
    """
    permission_classes = [IsStudent, HasActiveQuota]

    def post(self, request, *args, **kwargs):
        serializer = StartSimulationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            session = SimulationEngineService.start_session(
                student=request.user,
                case_id=str(serializer.validated_data["case_id"]),
            )
        except ValueError as e:
            return Response(
                {"success": False, "error": {"code": "NOT_FOUND", "message": str(e)}},
                status=status.HTTP_404_NOT_FOUND,
            )
        except PermissionError as e:
            return Response(
                {"success": False, "error": {"code": "QUOTA_EXCEEDED", "message": str(e)}},
                status=status.HTTP_403_FORBIDDEN,
            )

        step_logs = [
            {
                "step_number": log.step_number,
                "student_input": log.student_input,
                "step_score": log.step_score,
                "feedback": log.feedback_text,
                "next_scenario": log.next_scenario_text,
                "is_final": log.is_final_step,
                "strengths": log.ai_response_raw.get("strengths", []) if isinstance(log.ai_response_raw, dict) else [],
                "error_flags": log.ai_response_raw.get("error_flags", []) if isinstance(log.ai_response_raw, dict) else [],
                "running_total_score": session.total_score,
            }
            for log in session.step_logs.order_by("step_number")
        ]

        return Response(
            {
                "success": True,
                "message": "Simulation started! Good luck.",
                "data": {
                    "session_id": str(session.id),
                    "case_title": session.case.title,
                    "role_context": session.case.role_context,
                    "description": session.case.description,
                    "max_steps": session.case.max_steps,
                    "passing_score": session.case.passing_score,
                    "status": session.status,
                    "step_logs": step_logs,
                },
            },
            status=status.HTTP_201_CREATED,
        )


class SimulationTurnView(views.APIView):
    """
    POST /api/v1/simulations/<uuid:session_id>/turn/
    Student submits one action/response in the simulation.
    Returns AI feedback, score, next prompt.
    """
    permission_classes = [IsStudent]

    def post(self, request, session_id, *args, **kwargs):
        serializer = TurnInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = SimulationEngineService.process_turn(
                session_id=str(session_id),
                student=request.user,
                student_input=serializer.validated_data["student_input"],
            )
        except ValueError as e:
            return Response(
                {"success": False, "error": {"code": "NOT_FOUND", "message": str(e)}},
                status=status.HTTP_404_NOT_FOUND,
            )
        except PermissionError as e:
            return Response(
                {"success": False, "error": {"code": "QUOTA_EXCEEDED", "message": str(e)}},
                status=status.HTTP_403_FORBIDDEN,
            )
        except Exception as e:
            logger.exception("Unexpected error in process_turn: %s", e)
            return Response(
                {"success": False, "error": {"code": "AI_ERROR", "message": "AI evaluation failed. Please try again."}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response({"success": True, "data": result})


class AbandonSessionView(views.APIView):
    """
    POST /api/v1/simulations/<uuid:session_id>/abandon/
    Marks an active session as ABANDONED and frees quota slot.
    """
    permission_classes = [IsStudent]

    def post(self, request, session_id, *args, **kwargs):
        try:
            SimulationEngineService.abandon_session(
                session_id=str(session_id),
                student=request.user,
            )
        except SimulationSession.DoesNotExist:
            return Response(
                {"success": False, "error": {"code": "NOT_FOUND", "message": "Active session not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response({"success": True, "message": "Session abandoned."})


class MySessionListView(generics.ListAPIView):
    """
    GET /api/v1/simulations/my-sessions/
    Returns the authenticated student's simulation history.
    """
    serializer_class = SimulationSessionListSerializer
    permission_classes = [IsStudent]
    filterset_fields = ["status", "case__course__domain__slug"]
    ordering_fields = ["created_at", "total_score"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return (
            SimulationSession.objects
            .filter(student=self.request.user)
            .select_related("case__course__domain", "case__lesson")
            .order_by("-created_at")
        )


class MySessionDetailView(generics.RetrieveAPIView):
    """
    GET /api/v1/simulations/my-sessions/<uuid:pk>/
    Full detail of one session including step logs and review.
    """
    serializer_class = SimulationSessionDetailSerializer
    permission_classes = [IsStudent]

    def get_queryset(self):
        return (
            SimulationSession.objects
            .filter(student=self.request.user)
            .select_related(
                "case__course__domain",
                "case__lesson",
                "instructor_review__reviewer",
            )
            .prefetch_related("step_logs")
        )


# ── Instructor Views ───────────────────────────────────────────────────────────

class InstructorSessionListView(generics.ListAPIView):
    """
    GET /api/v1/simulations/instructor/sessions/
    Instructor sees all sessions for their courses.
    """
    serializer_class = SimulationSessionListSerializer
    permission_classes = [IsInstructorOrAdmin]
    filterset_fields = ["status", "case__course__domain__slug", "case"]
    ordering = ["-created_at"]

    def get_queryset(self):
        base_qs = SimulationSession.objects.select_related(
            "student", "student__profile", "case__course__domain", "case__lesson"
        ).order_by("-created_at")
        if self.request.user.role == "ADMIN":
            return base_qs.all()
        return base_qs.filter(case__course__instructor=self.request.user)


class InstructorSessionDetailView(generics.RetrieveAPIView):
    """
    GET /api/v1/simulations/instructor/sessions/<uuid:pk>/
    Full session detail for instructor (includes RAG context).
    """
    serializer_class = SimulationSessionDetailSerializer
    permission_classes = [IsInstructorOrAdmin]

    def get_queryset(self):
        base_qs = (
            SimulationSession.objects
            .select_related(
                "student",
                "student__profile",
                "case__course__domain",
                "case__lesson",
                "instructor_review__reviewer",
            )
            .prefetch_related("step_logs")
        )
        if self.request.user.role == "ADMIN":
            return base_qs.all()
        return base_qs.filter(case__course__instructor=self.request.user)


class InstructorReviewView(views.APIView):
    """
    POST /api/v1/simulations/<uuid:session_id>/review/
    Instructor creates or updates a score override for a session.
    """
    permission_classes = [IsInstructorOrAdmin]

    def post(self, request, session_id, *args, **kwargs):
        # Load session
        try:
            session = SimulationSession.objects.select_related("case__course").get(
                id=session_id,
                status__in=[
                    SimulationSession.Status.COMPLETED,
                    SimulationSession.Status.FAILED,
                ],
            )
        except SimulationSession.DoesNotExist:
            return Response(
                {"success": False, "error": {"code": "NOT_FOUND", "message": "Completed/failed session not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )

        # RBAC: instructors can only review their own courses
        if (
            request.user.role == "INSTRUCTOR"
            and session.case.course.instructor != request.user
        ):
            return Response(
                {"success": False, "error": {"code": "PERMISSION_DENIED", "message": "Not your course."}},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Create or update review
        serializer = InstructorReviewWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        review, created = InstructorReview.objects.update_or_create(
            session=session,
            defaults={
                "reviewer": request.user,
                "original_ai_score": session.total_score,
                **serializer.validated_data,
            },
        )

        # Update session total_score with override
        session.total_score = serializer.validated_data["override_score"]
        session.save(update_fields=["total_score"])

        logger.info(
            "Instructor review %s: session=%s ai_score=%.1f override=%.1f by=%s",
            "created" if created else "updated",
            session_id,
            review.original_ai_score,
            review.override_score,
            request.user.email,
        )

        return Response(
            {
                "success": True,
                "message": f"Review {'submitted' if created else 'updated'} successfully.",
                "data": InstructorReviewSerializer(review).data,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


# ── Laboratory Simulation Scenarios (Mentor Stories) ──────────────────────────

class SimulationScenarioListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/v1/simulations/scenarios/
         Browse laboratory crime/case scenarios.
    POST /api/v1/simulations/scenarios/
         Mentors create new case stories with accused details, roles, evidence, and prompts.
    """
    filterset_fields = ["course", "lesson", "is_active"]
    search_fields = ["title", "accused_name", "crime_details"]
    ordering_fields = ["created_at", "title"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return SimulationScenarioWriteSerializer
        return SimulationScenarioSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsInstructorOrAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = SimulationScenario.objects.select_related("course__domain", "lesson", "created_by", "case")
        if self.request.user.role in ("STUDENT", "RECRUITER"):
            qs = qs.filter(is_active=True)
        elif self.request.user.role == "INSTRUCTOR":
            qs = qs.filter(created_by=self.request.user) | qs.filter(is_active=True)
        return qs.distinct()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            {
                "success": True,
                "message": "Laboratoriya stsenariysi muvaffaqiyatli yaratildi.",
                "data": SimulationScenarioSerializer(serializer.instance).data,
            },
            status=status.HTTP_201_CREATED,
        )


class SimulationScenarioDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/v1/simulations/scenarios/<uuid:pk>/
    PATCH  /api/v1/simulations/scenarios/<uuid:pk>/ (Mentor / Admin)
    DELETE /api/v1/simulations/scenarios/<uuid:pk>/ (Mentor / Admin)
    """
    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return SimulationScenarioWriteSerializer
        return SimulationScenarioSerializer

    def get_permissions(self):
        if self.request.method in ("PUT", "PATCH", "DELETE"):
            return [IsInstructorOrAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        return SimulationScenario.objects.select_related("course__domain", "lesson", "created_by", "case")

    def perform_destroy(self, instance):
        instance.delete()
