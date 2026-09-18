"""
OmniLab AI - Simulation Admin Configuration
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import (
    SimulationCase,
    SimulationSession,
    SimulationStepLog,
    InstructorReview,
    SimulationScenario,
)


class SimulationStepLogInline(admin.TabularInline):
    model = SimulationStepLog
    extra = 0
    fields = ("step_number", "student_input_preview", "step_score", "is_final_step", "prompt_tokens", "completion_tokens")
    readonly_fields = ("step_number", "student_input_preview", "step_score", "is_final_step", "prompt_tokens", "completion_tokens")
    can_delete = False
    show_change_link = True

    @admin.display(description="Student Input")
    def student_input_preview(self, obj):
        return obj.student_input[:80] + "..." if len(obj.student_input) > 80 else obj.student_input


class InstructorReviewInline(admin.StackedInline):
    model = InstructorReview
    extra = 0
    fields = ("reviewer", "original_ai_score", "override_score", "override_reason", "instructor_feedback")
    readonly_fields = ("original_ai_score",)
    can_delete = False


@admin.register(SimulationCase)
class SimulationCaseAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "course",
        "difficulty_badge",
        "coin_reward",
        "max_steps",
        "passing_score",
        "is_published",
        "sessions_count",
        "created_by",
    )
    list_filter = ("course__domain", "difficulty", "is_published", "is_active")
    search_fields = ("title", "description", "course__title")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("id", "created_at", "updated_at")
    list_editable = ("is_published",)

    fieldsets = (
        ("Basic Info", {"fields": ("id", "course", "lesson", "created_by", "title", "slug", "description")}),
        ("Simulation Config", {
            "fields": (
                "role_context",
                "difficulty",
                "max_steps",
                "passing_score",
                "expected_duration_minutes",
                "grading_rubric",
                "hint_text",
            )
        }),
        ("Economy", {"fields": ("coin_reward",)}),
        ("Status", {"fields": ("is_published", "is_active")}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    @admin.display(description="Difficulty")
    def difficulty_badge(self, obj):
        colors = {
            "EASY": "#10B981",
            "MEDIUM": "#F59E0B",
            "HARD": "#EF4444",
            "EXPERT": "#7C3AED",
        }
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:4px;font-size:11px;">{}</span>',
            colors.get(obj.difficulty, "#6B7280"),
            obj.get_difficulty_display(),
        )

    @admin.display(description="Sessions")
    def sessions_count(self, obj):
        return obj.sessions.count()


@admin.register(SimulationSession)
class SimulationSessionAdmin(admin.ModelAdmin):
    inlines = [SimulationStepLogInline, InstructorReviewInline]

    list_display = (
        "id_short",
        "student",
        "case",
        "status_badge",
        "total_score_display",
        "steps_taken",
        "started_at",
        "completed_at",
    )
    list_filter = ("status", "case__course__domain", "started_at")
    search_fields = ("student__email", "case__title", "id")
    readonly_fields = (
        "id",
        "student",
        "case",
        "status",
        "current_step",
        "steps_taken",
        "total_score",
        "error_analysis",
        "started_at",
        "completed_at",
        "last_activity_at",
        "created_at",
    )
    date_hierarchy = "started_at"
    ordering = ("-started_at",)

    @admin.display(description="ID")
    def id_short(self, obj):
        return str(obj.id)[:8] + "..."

    @admin.display(description="Status")
    def status_badge(self, obj):
        colors = {
            "PENDING": "#6B7280",
            "ACTIVE": "#3B82F6",
            "COMPLETED": "#10B981",
            "FAILED": "#EF4444",
            "ABANDONED": "#F59E0B",
        }
        color = colors.get(obj.status, "#6B7280")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:4px;">{}</span>',
            color, obj.get_status_display(),
        )

    @admin.display(description="Score")
    def total_score_display(self, obj):
        score = obj.total_score
        passing = obj.case.passing_score
        color = "#10B981" if score >= passing else "#EF4444"
        return format_html(
            '<strong style="color:{};">{:.1f}%</strong>', color, score
        )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(SimulationStepLog)
class SimulationStepLogAdmin(admin.ModelAdmin):
    list_display = (
        "session",
        "step_number",
        "step_score",
        "is_final_step",
        "prompt_tokens",
        "completion_tokens",
        "created_at",
    )
    list_filter = ("is_final_step", "created_at")
    search_fields = ("session__student__email", "student_input", "feedback_text")
    readonly_fields = (
        "id",
        "session",
        "step_number",
        "student_input",
        "ai_response_raw",
        "step_score",
        "feedback_text",
        "next_scenario_text",
        "is_final_step",
        "rag_context_chunks",
        "prompt_tokens",
        "completion_tokens",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(InstructorReview)
class InstructorReviewAdmin(admin.ModelAdmin):
    list_display = (
        "session",
        "reviewer",
        "original_ai_score",
        "override_score",
        "score_delta",
        "created_at",
    )
    list_filter = ("created_at",)
    search_fields = ("session__student__email", "reviewer__email", "override_reason")
    readonly_fields = ("id", "original_ai_score", "created_at", "updated_at")

    @admin.display(description="Δ Score")
    def score_delta(self, obj):
        delta = obj.override_score - obj.original_ai_score
        color = "#10B981" if delta >= 0 else "#EF4444"
        sign = "+" if delta >= 0 else ""
        return format_html(
            '<span style="color:{};">{}{:.1f}</span>', color, sign, delta
        )


@admin.register(SimulationScenario)
class SimulationScenarioAdmin(admin.ModelAdmin):
    list_display = ("title", "accused_name", "course", "lesson", "created_by", "is_active", "created_at")
    list_filter = ("is_active", "course__domain", "course")
    search_fields = ("title", "accused_name", "crime_details", "created_by__email")
    readonly_fields = ("id", "created_at", "updated_at")
