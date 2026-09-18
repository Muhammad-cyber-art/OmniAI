"""
OmniLab AI - Curriculum Views
Domain, Course, Lesson CRUD + DocumentChunk RAG management.
"""
import logging
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.permissions import IsInstructorOrAdmin, IsAdminUser
from .models import Domain, Course, Lesson, DocumentChunk, Quiz, Question, QuestionOption, QuizAttempt
from .serializers import (
    DomainSerializer,
    CourseListSerializer,
    CourseDetailSerializer,
    CourseWriteSerializer,
    LessonListSerializer,
    LessonDetailSerializer,
    LessonWriteSerializer,
    DocumentChunkAdminSerializer,
    QuizListSerializer,
    QuizDetailSerializer,
    QuizWriteSerializer,
    QuestionSerializer,
    QuestionWriteSerializer,
    QuizSubmitSerializer,
    QuizAttemptResultSerializer,
)
from .services import CurriculumService

logger = logging.getLogger(__name__)


# ── Domain ────────────────────────────────────────────────────────────────────

class DomainListView(generics.ListAPIView):
    """GET /api/v1/curriculum/domains/"""
    serializer_class = DomainSerializer
    permission_classes = [IsAuthenticated]
    queryset = Domain.objects.filter(is_active=True)


# ── Courses ───────────────────────────────────────────────────────────────────

class CourseListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/v1/curriculum/courses/          → list (students see published only)
    POST /api/v1/curriculum/courses/          → create (instructor/admin)
    """
    filterset_fields = ["domain__slug", "difficulty", "is_published"]
    search_fields = ["title", "description"]
    ordering_fields = ["sort_order", "created_at"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CourseWriteSerializer
        return CourseListSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsInstructorOrAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = Course.objects.select_related("domain", "instructor").all()
        user = self.request.user
        if user.role in ("STUDENT", "RECRUITER"):
            qs = qs.filter(is_published=True)
        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Assign current instructor as owner
        if request.user.role == "INSTRUCTOR":
            serializer.save(instructor=request.user)
        else:
            serializer.save()
        return Response(
            {"success": True, "data": serializer.data},
            status=status.HTTP_201_CREATED,
        )


class CourseDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/v1/curriculum/courses/<slug>/
    PATCH  /api/v1/curriculum/courses/<slug>/  (instructor/admin)
    DELETE /api/v1/curriculum/courses/<slug>/  (admin)
    """
    lookup_field = "slug"

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return CourseWriteSerializer
        return CourseDetailSerializer

    def get_permissions(self):
        if self.request.method in ("PUT", "PATCH", "DELETE"):
            return [IsInstructorOrAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = Course.objects.select_related("domain", "instructor").prefetch_related("lessons")
        user = self.request.user
        if user.role in ("STUDENT", "RECRUITER"):
            qs = qs.filter(is_published=True)
        return qs


# ── Lessons ───────────────────────────────────────────────────────────────────

class LessonListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/v1/curriculum/courses/<course_slug>/lessons/
    POST /api/v1/curriculum/courses/<course_slug>/lessons/   (instructor/admin)
    """

    def get_serializer_class(self):
        if self.request.method == "POST":
            return LessonWriteSerializer
        return LessonListSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsInstructorOrAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = Lesson.objects.filter(
            course__slug=self.kwargs["course_slug"]
        ).select_related("course", "course__domain")
        if self.request.user.role in ("STUDENT", "RECRUITER"):
            qs = qs.filter(is_published=True)
        return qs.order_by("sort_order")

    def perform_create(self, serializer):
        instance = serializer.save()
        # Async chunking and embedding (production: Celery task)
        try:
            CurriculumService.chunk_and_embed_lesson(instance)
        except Exception as e:
            logger.error("Failed to embed lesson %s: %s", instance.id, e)


class LessonDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/v1/curriculum/lessons/<uuid:pk>/
    PATCH  /api/v1/curriculum/lessons/<uuid:pk>/
    DELETE /api/v1/curriculum/lessons/<uuid:pk>/
    """

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return LessonWriteSerializer
        return LessonDetailSerializer

    def get_permissions(self):
        if self.request.method in ("PUT", "PATCH", "DELETE"):
            return [IsInstructorOrAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = Lesson.objects.select_related("course")
        if self.request.user.role in ("STUDENT", "RECRUITER"):
            qs = qs.filter(is_published=True)
        return qs

    def perform_update(self, serializer):
        instance = serializer.save()
        # Re-embed on content change
        if "content" in self.request.data:
            try:
                CurriculumService.chunk_and_embed_lesson(instance, re_embed=True)
            except Exception as e:
                logger.error("Re-embedding failed for lesson %s: %s", instance.id, e)


# ── DocumentChunks (Admin / RAG Management) ───────────────────────────────────

class DocumentChunkListView(generics.ListAPIView):
    """
    GET /api/v1/curriculum/lessons/<uuid:lesson_id>/chunks/
    Admin can inspect RAG knowledge base for a lesson.
    """
    serializer_class = DocumentChunkAdminSerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return (
            DocumentChunk.objects
            .filter(lesson_id=self.kwargs["lesson_id"])
            .select_related("lesson", "lesson__course")
            .order_by("chunk_index")
        )


class RebuildEmbeddingsView(APIView):
    """
    POST /api/v1/curriculum/lessons/<uuid:pk>/rebuild-embeddings/
    Admin triggers full re-embedding of a lesson's document chunks.
    """
    permission_classes = [IsAdminUser]

    def post(self, request, pk, *args, **kwargs):
        try:
            lesson = Lesson.objects.get(pk=pk)
        except Lesson.DoesNotExist:
            return Response(
                {"success": False, "error": {"code": "NOT_FOUND", "message": "Lesson not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        count = CurriculumService.chunk_and_embed_lesson(lesson, re_embed=True)
        return Response(
            {
                "success": True,
                "message": f"Re-embedding complete. {count} chunks created.",
                "chunks_count": count,
            }
        )


# ── Quiz & Assessment Views ───────────────────────────────────────────────────

class LessonQuizListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/v1/curriculum/lessons/<uuid:lesson_id>/quizzes/
    POST /api/v1/curriculum/lessons/<uuid:lesson_id>/quizzes/ (Mentor/Admin)
    """
    def get_serializer_class(self):
        if self.request.method == "POST":
            return QuizWriteSerializer
        return QuizListSerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsInstructorOrAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = Quiz.objects.filter(lesson_id=self.kwargs["lesson_id"]).select_related("lesson")
        if self.request.user.role in ("STUDENT", "RECRUITER"):
            qs = qs.filter(is_published=True)
        return qs

    def perform_create(self, serializer):
        lesson = Lesson.objects.get(pk=self.kwargs["lesson_id"])
        serializer.save(lesson=lesson, created_by=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            {"success": True, "message": "Test muvaffaqiyatli yaratildi.", "data": QuizDetailSerializer(serializer.instance).data},
            status=status.HTTP_201_CREATED,
        )


class QuizDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/v1/curriculum/quizzes/<uuid:pk>/
    PATCH  /api/v1/curriculum/quizzes/<uuid:pk>/ (Mentor/Admin)
    DELETE /api/v1/curriculum/quizzes/<uuid:pk>/ (Mentor/Admin)
    """
    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return QuizWriteSerializer
        return QuizDetailSerializer

    def get_permissions(self):
        if self.request.method in ("PUT", "PATCH", "DELETE"):
            return [IsInstructorOrAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        return Quiz.objects.select_related("lesson", "created_by").prefetch_related("questions__options")


class QuizQuestionCreateView(generics.CreateAPIView):
    """
    POST /api/v1/curriculum/quizzes/<uuid:quiz_id>/questions/
    Mentor adds a new question with options to a Quiz.
    """
    serializer_class = QuestionWriteSerializer
    permission_classes = [IsInstructorOrAdmin]

    def create(self, request, quiz_id, *args, **kwargs):
        try:
            quiz = Quiz.objects.get(pk=quiz_id)
        except Quiz.DoesNotExist:
            return Response(
                {"success": False, "error": {"code": "NOT_FOUND", "message": "Test topilmadi."}},
                status=status.HTTP_404_NOT_FOUND,
            )

        data = request.data.copy()
        data["quiz"] = quiz.id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        question = serializer.save(quiz=quiz)
        return Response(
            {"success": True, "message": "Savol qo'shildi.", "data": QuestionSerializer(question, context={"request": request}).data},
            status=status.HTTP_201_CREATED,
        )


class QuizSubmitView(APIView):
    """
    POST /api/v1/curriculum/quizzes/<uuid:quiz_id>/submit/
    Student submits answers to a Quiz. Automatically calculates score and awards status.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, quiz_id, *args, **kwargs):
        try:
            quiz = Quiz.objects.prefetch_related("questions__options").get(pk=quiz_id, is_published=True)
        except Quiz.DoesNotExist:
            return Response(
                {"success": False, "error": {"code": "NOT_FOUND", "message": "Test topilmadi yoki nofaol."}},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = QuizSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        student_answers = serializer.validated_data["answers"]

        questions = quiz.questions.all()
        if not questions.exists():
            return Response(
                {"success": False, "error": {"code": "EMPTY_QUIZ", "message": "Ushbu testda hali savollar yo'q."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        total_points = 0
        earned_points = 0
        feedback_details = []

        for q in questions:
            total_points += q.points
            selected_option_id = str(student_answers.get(str(q.id)) or "")
            correct_option = q.options.filter(is_correct=True).first()

            is_correct = bool(correct_option and str(correct_option.id) == selected_option_id)
            if is_correct:
                earned_points += q.points

            feedback_details.append({
                "question_id": str(q.id),
                "question_text": q.text,
                "is_correct": is_correct,
                "selected_option_id": selected_option_id,
                "correct_option_id": str(correct_option.id) if correct_option else None,
                "explanation": q.explanation,
            })

        score = (earned_points / total_points * 100) if total_points > 0 else 0.0
        is_passed = score >= quiz.passing_score

        attempt = QuizAttempt.objects.create(
            quiz=quiz,
            student=request.user,
            score=round(score, 2),
            is_passed=is_passed,
            answers={str(k): str(v) for k, v in student_answers.items()},
        )

        return Response({
            "success": True,
            "message": "Test muvaffaqiyatli topshirildi!" if is_passed else "Test yakunlandi. O'tish bali to'planmadi.",
            "data": {
                "attempt_id": str(attempt.id),
                "quiz_title": quiz.title,
                "score": round(score, 1),
                "passing_score": quiz.passing_score,
                "is_passed": is_passed,
                "earned_points": earned_points,
                "total_points": total_points,
                "details": feedback_details,
            },
        })
