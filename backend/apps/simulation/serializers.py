"""
OmniLab AI - Simulation Serializers
"""
from rest_framework import serializers

from .models import SimulationCase, SimulationSession, SimulationStepLog, InstructorReview


class SimulationCaseListSerializer(serializers.ModelSerializer):
    domain_name = serializers.CharField(source="course.domain.name", read_only=True)
    course_title = serializers.CharField(source="course.title", read_only=True)

    class Meta:
        model = SimulationCase
        fields = [
            "id",
            "title",
            "slug",
            "domain_name",
            "course_title",
            "difficulty",
            "coin_reward",
            "max_steps",
            "passing_score",
            "expected_duration_minutes",
            "is_published",
        ]


class SimulationCaseDetailSerializer(SimulationCaseListSerializer):
    class Meta(SimulationCaseListSerializer.Meta):
        fields = SimulationCaseListSerializer.Meta.fields + [
            "description",
            "role_context",
            "grading_rubric",
            "hint_text",
            "created_at",
            "updated_at",
        ]


class SimulationCaseWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = SimulationCase
        fields = [
            "course",
            "lesson",
            "title",
            "slug",
            "description",
            "role_context",
            "difficulty",
            "coin_reward",
            "max_steps",
            "passing_score",
            "hint_text",
            "is_published",
            "expected_duration_minutes",
            "grading_rubric",
        ]


class SimulationStepLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SimulationStepLog
        fields = [
            "id",
            "step_number",
            "student_input",
            "step_score",
            "feedback_text",
            "next_scenario_text",
            "is_final_step",
            "prompt_tokens",
            "completion_tokens",
            "created_at",
        ]
        read_only_fields = fields


class SimulationStepLogDetailSerializer(SimulationStepLogSerializer):
    """Includes raw AI response and RAG context — admin/instructor only."""
    class Meta(SimulationStepLogSerializer.Meta):
        fields = SimulationStepLogSerializer.Meta.fields + [
            "ai_response_raw",
            "rag_context_chunks",
        ]


class SimulationSessionListSerializer(serializers.ModelSerializer):
    case_title = serializers.CharField(source="case.title", read_only=True)
    case_domain = serializers.CharField(source="case.course.domain.name", read_only=True)
    progress_pct = serializers.FloatField(read_only=True)

    class Meta:
        model = SimulationSession
        fields = [
            "id",
            "case_title",
            "case_domain",
            "status",
            "total_score",
            "steps_taken",
            "progress_pct",
            "started_at",
            "completed_at",
            "last_activity_at",
        ]
        read_only_fields = fields


class SimulationSessionDetailSerializer(SimulationSessionListSerializer):
    step_logs = SimulationStepLogSerializer(many=True, read_only=True)
    instructor_review = serializers.SerializerMethodField()

    class Meta(SimulationSessionListSerializer.Meta):
        fields = SimulationSessionListSerializer.Meta.fields + [
            "error_analysis",
            "strengths_summary",
            "weaknesses_summary",
            "step_logs",
            "instructor_review",
        ]

    def get_instructor_review(self, obj):
        try:
            review = obj.instructor_review
            return InstructorReviewSerializer(review).data
        except InstructorReview.DoesNotExist:
            return None


class StartSimulationSerializer(serializers.Serializer):
    case_id = serializers.UUIDField()


class TurnInputSerializer(serializers.Serializer):
    student_input = serializers.CharField(
        min_length=1,
        max_length=5000,
        trim_whitespace=True,
    )


class InstructorReviewSerializer(serializers.ModelSerializer):
    reviewer_email = serializers.EmailField(source="reviewer.email", read_only=True)

    class Meta:
        model = InstructorReview
        fields = [
            "id",
            "reviewer_email",
            "original_ai_score",
            "override_score",
            "override_reason",
            "instructor_feedback",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "reviewer_email", "original_ai_score", "created_at", "updated_at"]


class InstructorReviewWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstructorReview
        fields = ["override_score", "override_reason", "instructor_feedback"]

    def validate_override_score(self, value):
        if not (0.0 <= value <= 100.0):
            raise serializers.ValidationError("Score must be between 0 and 100.")
        return value

    def validate_override_reason(self, value):
        if len(value.strip()) < 20:
            raise serializers.ValidationError(
                "Override reason must be at least 20 characters. Please provide a meaningful explanation."
            )
        return value
