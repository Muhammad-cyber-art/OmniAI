"""
OmniLab AI - Curriculum Serializers
"""
from rest_framework import serializers

from .models import Domain, Course, Lesson, DocumentChunk


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
