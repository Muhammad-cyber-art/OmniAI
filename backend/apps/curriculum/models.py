"""
OmniLab AI - Curriculum App Models
Domain, Course, Lesson, DocumentChunk (with pgvector embedding)
"""
import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


class DifficultyLevel(models.TextChoices):
    BEGINNER = "BEGINNER", _("Beginner")
    INTERMEDIATE = "INTERMEDIATE", _("Intermediate")
    ADVANCED = "ADVANCED", _("Advanced")
    EXPERT = "EXPERT", _("Expert")


# ─── DOMAIN ───────────────────────────────────────────────────────────────────

class Domain(models.Model):
    """
    Top-level subject area: Law, Medicine, Chemistry, Physics, etc.
    Slugs are used in URLs and as stable identifiers.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, db_index=True)
    description = models.TextField(blank=True)
    icon_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "curriculum_domain"
        verbose_name = _("Domain")
        verbose_name_plural = _("Domains")
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name


# ─── COURSE ───────────────────────────────────────────────────────────────────

class Course(models.Model):
    """
    A structured course within a domain.
    Instructors own courses; admins can manage all.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    domain = models.ForeignKey(
        Domain,
        on_delete=models.PROTECT,
        related_name="courses",
        db_index=True,
    )
    instructor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="courses",
        limit_choices_to={"role__in": ["INSTRUCTOR", "ADMIN"]},
    )
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    description = models.TextField(blank=True)
    cover_image_url = models.URLField(blank=True)
    difficulty = models.CharField(
        max_length=20,
        choices=DifficultyLevel.choices,
        default=DifficultyLevel.BEGINNER,
        db_index=True,
    )
    is_published = models.BooleanField(default=False, db_index=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "curriculum_course"
        verbose_name = _("Course")
        verbose_name_plural = _("Courses")
        ordering = ["domain", "sort_order", "title"]
        indexes = [
            models.Index(fields=["domain", "is_published"], name="idx_course_domain_pub"),
            models.Index(fields=["difficulty", "is_published"], name="idx_course_diff_pub"),
        ]

    def __str__(self) -> str:
        return f"[{self.domain.name}] {self.title}"


# ─── LESSON ───────────────────────────────────────────────────────────────────

class Lesson(models.Model):
    """
    A module/lesson within a course.
    Content can be rich text (Markdown/HTML) uploaded by instructors (no-code).
    DocumentChunks are derived from lesson content for RAG.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="lessons",
        db_index=True,
    )
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, db_index=True)
    content = models.TextField(
        help_text=_("Lesson content in Markdown or HTML. Used as RAG knowledge base."),
    )
    summary = models.TextField(
        blank=True,
        help_text=_("Brief summary for search and previews."),
    )
    sort_order = models.PositiveSmallIntegerField(default=0)
    is_published = models.BooleanField(default=False)
    reading_time_minutes = models.PositiveSmallIntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(120)],
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "curriculum_lesson"
        verbose_name = _("Lesson")
        verbose_name_plural = _("Lessons")
        ordering = ["course", "sort_order"]
        unique_together = [("course", "slug")]
        indexes = [
            models.Index(fields=["course", "sort_order"], name="idx_lesson_course_order"),
        ]

    def __str__(self) -> str:
        return f"{self.course.title} / {self.title}"


# ─── DOCUMENT CHUNK (pgvector) ────────────────────────────────────────────────

class DocumentChunk(models.Model):
    """
    Chunked text segments derived from Lesson content.
    Stores vector embeddings for semantic (RAG) search.

    pgvector field is represented as ArrayField of floats.
    In production, replace with pgvector.django.VectorField for native HNSW indexing.

    Schema:
        ALTER TABLE curriculum_document_chunk
        ADD COLUMN embedding vector(1536);
        CREATE INDEX ON curriculum_document_chunk
        USING hnsw (embedding vector_cosine_ops);
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name="chunks",
        db_index=True,
    )
    chunk_index = models.PositiveSmallIntegerField(
        help_text=_("Position of this chunk within the lesson."),
    )
    text = models.TextField(
        help_text=_("Raw text content of this chunk (used in prompts)."),
    )
    token_count = models.PositiveIntegerField(
        default=0,
        help_text=_("Approximate token count of this chunk."),
    )

    # pgvector embedding stored as JSON array of floats
    # In production: use pgvector.django.VectorField(dimensions=1536)
    embedding = models.JSONField(
        null=True,
        blank=True,
        help_text=_("1536-dim float embedding vector from OpenAI text-embedding-3-small."),
    )

    # Metadata for filtering during RAG retrieval
    source_section = models.CharField(
        max_length=255,
        blank=True,
        help_text=_("Section heading this chunk belongs to."),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "curriculum_document_chunk"
        verbose_name = _("Document Chunk")
        verbose_name_plural = _("Document Chunks")
        ordering = ["lesson", "chunk_index"]
        unique_together = [("lesson", "chunk_index")]
        indexes = [
            models.Index(fields=["lesson", "chunk_index"], name="idx_chunk_lesson_order"),
        ]

    def __str__(self) -> str:
        return f"Chunk[{self.chunk_index}] of {self.lesson.title}"


# ─── QUIZ & ASSESSMENT MODELS ─────────────────────────────────────────────────

class Quiz(models.Model):
    """
    Assessment test linked to a Lesson. Created by Mentors / Instructors.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name="quizzes",
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_quizzes",
        limit_choices_to={"role__in": ["INSTRUCTOR", "ADMIN"]},
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    time_limit_minutes = models.PositiveSmallIntegerField(default=15)
    passing_score = models.PositiveSmallIntegerField(
        default=70,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_("Minimum percentage score required to pass."),
    )
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "curriculum_quiz"
        verbose_name = _("Quiz")
        verbose_name_plural = _("Quizzes")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Quiz: {self.title} ({self.lesson.title})"

    @property
    def total_questions(self) -> int:
        return self.questions.count()


class Question(models.Model):
    """
    A single question within a Quiz.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    text = models.TextField(help_text=_("Question prompt/text."))
    explanation = models.TextField(
        blank=True,
        help_text=_("Explanation referencing the textbook or legal article."),
    )
    points = models.PositiveSmallIntegerField(default=1)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "curriculum_question"
        verbose_name = _("Question")
        verbose_name_plural = _("Questions")
        ordering = ["sort_order", "id"]

    def __str__(self) -> str:
        return f"Q: {self.text[:50]}..."


class QuestionOption(models.Model):
    """
    Answer option for a Question.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="options",
    )
    text = models.CharField(max_length=512)
    is_correct = models.BooleanField(default=False)

    class Meta:
        db_table = "curriculum_question_option"
        verbose_name = _("Question Option")
        verbose_name_plural = _("Question Options")

    def __str__(self) -> str:
        status_label = " (To'g'ri)" if self.is_correct else ""
        return f"{self.text[:40]}{status_label}"


class QuizAttempt(models.Model):
    """
    Records a student's attempt and auto-calculated score.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="attempts",
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="quiz_attempts",
    )
    score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
    )
    is_passed = models.BooleanField(default=False)
    answers = models.JSONField(
        default=dict,
        help_text=_("Map of question_id -> selected_option_id"),
    )
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "curriculum_quiz_attempt"
        verbose_name = _("Quiz Attempt")
        verbose_name_plural = _("Quiz Attempts")
        ordering = ["-completed_at"]

    def __str__(self) -> str:
        result = "PASSED" if self.is_passed else "FAILED"
        return f"{self.student.email} → {self.quiz.title}: {self.score}% [{result}]"

