"""
OmniLab AI - Curriculum Serializers
"""
from rest_framework import serializers

from .models import Domain, Course, Lesson, DocumentChunk, Quiz, Question, QuestionOption, QuizAttempt


class DomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = ["id", "name", "slug", "description", "icon_url", "sort_order"]


class CourseListSerializer(serializers.ModelSerializer):
    domain_name = serializers.CharField(source="domain.name", read_only=True)
    instructor_name = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "slug",
            "domain_name",
            "instructor_name",
            "description",
            "cover_image_url",
            "difficulty",
            "is_published",
        ]

    def get_instructor_name(self, obj):
        return obj.instructor.full_name if obj.instructor else None


class CourseDetailSerializer(CourseListSerializer):
    lessons_count = serializers.SerializerMethodField()

    class Meta(CourseListSerializer.Meta):
        fields = CourseListSerializer.Meta.fields + ["lessons_count", "created_at", "updated_at"]

    def get_lessons_count(self, obj):
        if hasattr(obj, "published_lessons_count"):
            return obj.published_lessons_count
        if hasattr(obj, "_prefetched_objects_cache") and "lessons" in obj._prefetched_objects_cache:
            return sum(1 for l in obj.lessons.all() if l.is_published)
        return obj.lessons.filter(is_published=True).count()


class CourseWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = [
            "domain",
            "title",
            "slug",
            "description",
            "cover_image_url",
            "difficulty",
            "is_published",
            "sort_order",
        ]


class LessonListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = [
            "id",
            "title",
            "slug",
            "summary",
            "sort_order",
            "is_published",
            "reading_time_minutes",
        ]


class LessonDetailSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source="course.title", read_only=True)

    class Meta:
        model = Lesson
        fields = [
            "id",
            "course_title",
            "title",
            "slug",
            "content",
            "summary",
            "sort_order",
            "is_published",
            "reading_time_minutes",
            "created_at",
            "updated_at",
        ]


class LessonWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = [
            "course",
            "title",
            "slug",
            "content",
            "summary",
            "sort_order",
            "is_published",
            "reading_time_minutes",
        ]


class DocumentChunkAdminSerializer(serializers.ModelSerializer):
    """Admin-only serializer; embedding is excluded from normal responses."""

    class Meta:
        model = DocumentChunk
        fields = [
            "id",
            "lesson",
            "chunk_index",
            "text",
            "token_count",
            "source_section",
            "created_at",
        ]
        read_only_fields = ["id", "token_count", "created_at"]


# ─── QUIZ SERIALIZERS ─────────────────────────────────────────────────────────

class QuestionOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionOption
        fields = ["id", "text", "is_correct"]


class QuestionOptionStudentSerializer(serializers.ModelSerializer):
    """Excludes is_correct when student is taking the quiz."""
    class Meta:
        model = QuestionOption
        fields = ["id", "text"]


class QuestionSerializer(serializers.ModelSerializer):
    options = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = ["id", "text", "explanation", "points", "sort_order", "options"]

    def get_options(self, obj):
        request = self.context.get("request")
        # Hide correct answers for students before submission
        if request and request.user and request.user.role in ("INSTRUCTOR", "ADMIN"):
            return QuestionOptionSerializer(obj.options.all(), many=True).data
        return QuestionOptionStudentSerializer(obj.options.all(), many=True).data


class QuestionWriteSerializer(serializers.ModelSerializer):
    options = QuestionOptionSerializer(many=True, required=False)

    class Meta:
        model = Question
        fields = ["id", "quiz", "text", "explanation", "points", "sort_order", "options"]
        read_only_fields = ["id", "quiz"]

    def create(self, validated_data):
        options_data = validated_data.pop("options", [])
        question = Question.objects.create(**validated_data)
        for opt in options_data:
            QuestionOption.objects.create(question=question, **opt)
        return question


class QuizListSerializer(serializers.ModelSerializer):
    lesson_title = serializers.CharField(source="lesson.title", read_only=True)
    total_questions = serializers.IntegerField(read_only=True)

    class Meta:
        model = Quiz
        fields = [
            "id",
            "lesson",
            "lesson_title",
            "title",
            "description",
            "time_limit_minutes",
            "passing_score",
            "total_questions",
            "is_published",
            "created_at",
        ]


class QuizDetailSerializer(QuizListSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta(QuizListSerializer.Meta):
        fields = QuizListSerializer.Meta.fields + ["questions"]


class QuizWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = [
            "id",
            "lesson",
            "title",
            "description",
            "time_limit_minutes",
            "passing_score",
            "is_published",
        ]
        read_only_fields = ["id", "lesson"]


class QuizSubmitSerializer(serializers.Serializer):
    answers = serializers.DictField(
        child=serializers.UUIDField(),
        help_text="Map of question_id -> selected_option_id",
    )


class QuizAttemptResultSerializer(serializers.ModelSerializer):
    quiz_title = serializers.CharField(source="quiz.title", read_only=True)

    class Meta:
        model = QuizAttempt
        fields = [
            "id",
            "quiz",
            "quiz_title",
            "score",
            "is_passed",
            "completed_at",
        ]
