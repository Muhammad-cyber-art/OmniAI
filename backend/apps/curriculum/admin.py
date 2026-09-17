"""
OmniLab AI - Curriculum Admin Configuration
"""
from django.contrib import admin
from django.utils.html import format_html

from .models import Domain, Course, Lesson, DocumentChunk


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active", "sort_order", "courses_count")
    list_editable = ("is_active", "sort_order")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("sort_order", "name")

    @admin.display(description="Courses")
    def courses_count(self, obj):
        count = obj.courses.count()
        return format_html('<strong>{}</strong>', count)


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0
    fields = ("title", "slug", "sort_order", "is_published", "reading_time_minutes")
    prepopulated_fields = {"slug": ("title",)}
    show_change_link = True


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    inlines = [LessonInline]
    list_display = (
        "title",
        "domain",
        "instructor",
        "difficulty_badge",
        "is_published",
        "lessons_count",
        "created_at",
    )
    list_filter = ("domain", "difficulty", "is_published")
    search_fields = ("title", "description", "instructor__email")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("id", "created_at", "updated_at")
    list_editable = ("is_published",)

    fieldsets = (
        ("Basic Info", {"fields": ("id", "domain", "instructor", "title", "slug", "description", "cover_image_url")}),
        ("Settings", {"fields": ("difficulty", "is_published", "sort_order")}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    @admin.display(description="Difficulty")
    def difficulty_badge(self, obj):
        colors = {
            "BEGINNER": "#10B981",
            "INTERMEDIATE": "#F59E0B",
            "ADVANCED": "#EF4444",
            "EXPERT": "#7C3AED",
        }
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:4px;font-size:11px;">{}</span>',
            colors.get(obj.difficulty, "#6B7280"),
            obj.get_difficulty_display(),
        )

    @admin.display(description="Lessons")
    def lessons_count(self, obj):
        total = obj.lessons.count()
        published = obj.lessons.filter(is_published=True).count()
        return f"{published}/{total}"


class DocumentChunkInline(admin.TabularInline):
    model = DocumentChunk
    extra = 0
    fields = ("chunk_index", "source_section", "token_count", "has_embedding")
    readonly_fields = ("chunk_index", "source_section", "token_count", "has_embedding")
    can_delete = True
    show_change_link = False
    max_num = 0  # read-only display

    @admin.display(description="Embedded?", boolean=True)
    def has_embedding(self, obj):
        return bool(obj.embedding)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    inlines = [DocumentChunkInline]
    list_display = (
        "title",
        "course",
        "sort_order",
        "is_published",
        "reading_time_minutes",
        "chunks_count",
        "updated_at",
    )
    list_filter = ("course__domain", "is_published", "course")
    search_fields = ("title", "content", "course__title")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("id", "created_at", "updated_at")
    list_editable = ("is_published", "sort_order")

    @admin.display(description="RAG Chunks")
    def chunks_count(self, obj):
        count = obj.chunks.count()
        embedded = obj.chunks.exclude(embedding=None).count()
        color = "#10B981" if embedded == count and count > 0 else "#F59E0B"
        return format_html(
            '<span style="color:{};">{}/{}</span>', color, embedded, count
        )


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ("lesson", "chunk_index", "source_section", "token_count", "has_embedding", "created_at")
    list_filter = ("lesson__course__domain",)
    search_fields = ("lesson__title", "text", "source_section")
    readonly_fields = ("id", "lesson", "chunk_index", "text", "token_count", "embedding", "created_at")

    @admin.display(description="Embedded?", boolean=True)
    def has_embedding(self, obj):
        return bool(obj.embedding)

    def has_add_permission(self, request):
        return False  # Chunks are always auto-generated
