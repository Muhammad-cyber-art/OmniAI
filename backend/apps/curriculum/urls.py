"""OmniLab AI - Curriculum URL Configuration"""
from django.urls import path

from .views import (
    DomainListView,
    CourseListCreateView,
    CourseDetailView,
    LessonListCreateView,
    LessonDetailView,
    DocumentChunkListView,
    RebuildEmbeddingsView,
)

app_name = "curriculum"

urlpatterns = [
    path("domains/", DomainListView.as_view(), name="domain_list"),

    path("courses/", CourseListCreateView.as_view(), name="course_list"),
    path("courses/<slug:slug>/", CourseDetailView.as_view(), name="course_detail"),
    path("courses/<slug:course_slug>/lessons/", LessonListCreateView.as_view(), name="lesson_list"),

    path("lessons/<uuid:pk>/", LessonDetailView.as_view(), name="lesson_detail"),
    path("lessons/<uuid:lesson_id>/chunks/", DocumentChunkListView.as_view(), name="chunk_list"),
    path("lessons/<uuid:pk>/rebuild-embeddings/", RebuildEmbeddingsView.as_view(), name="rebuild_embeddings"),
]
