"""
OmniLab AI - Simulation App Models
SimulationCase, SimulationSession (State Machine), SimulationStepLog, InstructorReview
"""
import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.db.models import CheckConstraint, Q

from apps.curriculum.models import Course, Lesson
from apps.users.models import UserRole

User = get_user_model()


# ─── SIMULATION CASE ──────────────────────────────────────────────────────────

class DifficultyLevel(models.TextChoices):
    EASY = "EASY", _("Easy")
    MEDIUM = "MEDIUM", _("Medium")
    HARD = "HARD", _("Hard")
    EXPERT = "EXPERT", _("Expert")


class SimulationCase(models.Model):
    """
    A simulation scenario ("case") that students engage with.
    Defined by instructors, tied to a course/lesson for RAG grounding.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="simulation_cases",
        db_index=True,
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="simulation_cases",
        help_text=_("Primary lesson whose DocumentChunks are used for RAG grounding."),
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_cases",
        limit_choices_to={"role__in": [UserRole.INSTRUCTOR, UserRole.ADMIN]},
    )

    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    description = models.TextField(
        help_text=_("Detailed description of the scenario presented to the student."),
    )
    role_context = models.TextField(
        help_text=_(
            "The role the student assumes (e.g., 'You are a junior attorney...'). "
            "Injected as system prompt context."
        ),
    )
    difficulty = models.CharField(
        max_length=10,
        choices=DifficultyLevel.choices,
        default=DifficultyLevel.MEDIUM,
        db_index=True,
    )

    # Reward & Progression
    coin_reward = models.PositiveIntegerField(
        default=50,
        validators=[MinValueValidator(1), MaxValueValidator(10000)],
        help_text=_("Base coins awarded on successful completion (before multiplier)."),
    )
    max_steps = models.PositiveSmallIntegerField(
        default=10,
        validators=[MinValueValidator(2), MaxValueValidator(50)],
        help_text=_("Maximum number of student steps allowed per session."),
    )
    passing_score = models.PositiveSmallIntegerField(
        default=70,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_("Minimum percentage score required to complete successfully."),
    )

    # Hint content (instructor-written)
    hint_text = models.TextField(
        blank=True,
        help_text=_("Optional hint text revealed when student requests a hint."),
    )

    # Metadata
    is_published = models.BooleanField(default=False, db_index=True)
    is_active = models.BooleanField(default=True)
    expected_duration_minutes = models.PositiveSmallIntegerField(default=30)

    # Grading rubric (JSON): {criterion: weight, ...}
    grading_rubric = models.JSONField(
        default=dict,
        blank=True,
        help_text=_(
            "JSON grading rubric. Example: "
            '{"legal_reasoning": 40, "factual_accuracy": 30, "communication": 30}'
        ),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "simulation_case"
        verbose_name = _("Simulation Case")
        verbose_name_plural = _("Simulation Cases")
        ordering = ["course", "difficulty", "title"]
        indexes = [
            models.Index(fields=["course", "is_published"], name="idx_case_course_pub"),
            models.Index(fields=["difficulty", "is_published"], name="idx_case_diff_pub"),
        ]

    def __str__(self) -> str:
        return f"[{self.course.domain.name}] {self.title} ({self.difficulty})"


# ─── SIMULATION SESSION (State Machine) ───────────────────────────────────────

class SimulationSession(models.Model):
    """
    Tracks a student's single attempt at a SimulationCase.
    State machine transitions:
        PENDING → ACTIVE → COMPLETED
                         ↘ FAILED
                         ↘ ABANDONED
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", _("Pending")        # Created, not yet started
        ACTIVE = "ACTIVE", _("Active")            # Student is working on it
        COMPLETED = "COMPLETED", _("Completed")  # Passed (score >= passing_score)
        FAILED = "FAILED", _("Failed")            # Finished but score < passing_score
        ABANDONED = "ABANDONED", _("Abandoned")  # Timed out or manually abandoned

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="simulation_sessions",
        db_index=True,
        limit_choices_to={"role": UserRole.STUDENT},
    )
    case = models.ForeignKey(
        SimulationCase,
        on_delete=models.PROTECT,
        related_name="sessions",
        db_index=True,
    )

    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    # Progress tracking
    current_step = models.PositiveSmallIntegerField(default=0)
    total_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text=_("Running weighted score (0–100)."),
    )
    steps_taken = models.PositiveSmallIntegerField(default=0)

    # AI-generated metadata (updated after each step)
    error_analysis = models.JSONField(
        default=dict,
        blank=True,
        help_text=_(
            "Structured error categories and counts. "
            'Example: {"logical_errors": 2, "factual_errors": 1}'
        ),
    )
    strengths_summary = models.TextField(blank=True)
    weaknesses_summary = models.TextField(blank=True)

    # Timestamps
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_activity_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "simulation_session"
        verbose_name = _("Simulation Session")
        verbose_name_plural = _("Simulation Sessions")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["student", "status"], name="idx_session_student_status"),
            models.Index(fields=["case", "status"], name="idx_session_case_status"),
            models.Index(fields=["student", "case", "-created_at"], name="idx_session_student_case"),
        ]
        constraints = [
            CheckConstraint(
                condition=Q(total_score__gte=0) & Q(total_score__lte=100),
                name="session_score_range",
            ),
            CheckConstraint(
                condition=Q(steps_taken__gte=0),
                name="session_steps_gte_zero",
            ),
        ]

    def __str__(self) -> str:
        return f"Session[{self.status}] {self.student.email} → {self.case.title}"

    @property
    def is_passed(self) -> bool:
        return (
            self.status == self.Status.COMPLETED
            and self.total_score >= self.case.passing_score
        )

    @property
    def progress_pct(self) -> float:
        if self.case.max_steps == 0:
            return 0.0
        return min(100.0, (self.steps_taken / self.case.max_steps) * 100)


# ─── SIMULATION STEP LOG ──────────────────────────────────────────────────────

class SimulationStepLog(models.Model):
    """
    Immutable log of every student action and AI response within a session.
    The AI always returns a strict JSON structure (enforced by SimulationEngineService).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        SimulationSession,
        on_delete=models.CASCADE,
        related_name="step_logs",
        db_index=True,
    )
    step_number = models.PositiveSmallIntegerField(
        help_text=_("1-indexed position of this step in the session."),
    )

    # Student input
    student_input = models.TextField(
        help_text=_("Raw text submitted by the student for this step."),
    )

    # AI response (structured JSON)
    ai_response_raw = models.JSONField(
        help_text=_(
            "Full structured JSON response from AI. Schema: "
            "{ feedback: str, score: float, next_scenario: str, "
            "is_final: bool, error_flags: [...], strengths: [...] }"
        ),
    )

    # Extracted fields for quick querying
    step_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text=_("Score for this individual step (0–100)."),
    )
    feedback_text = models.TextField(
        blank=True,
        help_text=_("AI feedback text extracted from ai_response_raw.feedback."),
    )
    next_scenario_text = models.TextField(
        blank=True,
        help_text=_("Next scenario/prompt presented to student."),
    )
    is_final_step = models.BooleanField(
        default=False,
        help_text=_("True if this step concluded the session."),
    )

    # RAG context used (for transparency/audit)
    rag_context_chunks = models.JSONField(
        default=list,
        blank=True,
        help_text=_("List of document chunk excerpts used as context for this step."),
    )

    # Token usage (for cost tracking)
    prompt_tokens = models.PositiveIntegerField(default=0)
    completion_tokens = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "simulation_step_log"
        verbose_name = _("Simulation Step Log")
        verbose_name_plural = _("Simulation Step Logs")
        ordering = ["session", "step_number"]
        unique_together = [("session", "step_number")]
        indexes = [
            models.Index(fields=["session", "step_number"], name="idx_step_session_num"),
        ]
        constraints = [
            CheckConstraint(
                condition=Q(step_score__gte=0) & Q(step_score__lte=100),
                name="step_score_range",
            ),
        ]

    def __str__(self) -> str:
        return f"Step {self.step_number} of {self.session_id}"


# ─── INSTRUCTOR REVIEW ────────────────────────────────────────────────────────

class InstructorReview(models.Model):
    """
    Allows instructors to override AI-assigned scores and leave feedback.
    Records original AI score vs instructor-assigned score for audit.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.OneToOneField(
        SimulationSession,
        on_delete=models.CASCADE,
        related_name="instructor_review",
    )
    reviewer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="reviews_given",
        limit_choices_to={"role__in": [UserRole.INSTRUCTOR, UserRole.ADMIN]},
    )

    original_ai_score = models.FloatField(
        help_text=_("AI-assigned score at time of review."),
    )
    override_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text=_("Instructor's final score (0–100)."),
    )
    override_reason = models.TextField(
        help_text=_("Mandatory explanation for the score override."),
    )
    instructor_feedback = models.TextField(
        blank=True,
        help_text=_("Additional feedback for the student."),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "simulation_instructor_review"
        verbose_name = _("Instructor Review")
        verbose_name_plural = _("Instructor Reviews")
        ordering = ["-created_at"]
        constraints = [
            CheckConstraint(
                condition=Q(override_score__gte=0) & Q(override_score__lte=100),
                name="review_score_range",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"Review by {self.reviewer.email if self.reviewer else 'N/A'} "
            f"for session {self.session_id}"
        )
