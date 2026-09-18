"""OmniLab AI - Simulation URL Configuration"""
from django.urls import path

from .views import (
    SimulationCaseListCreateView,
    SimulationCaseDetailView,
    StartSimulationView,
    SimulationTurnView,
    AbandonSessionView,
    MySessionListView,
    MySessionDetailView,
    InstructorSessionListView,
    InstructorSessionDetailView,
    InstructorReviewView,
    SimulationScenarioListCreateView,
    SimulationScenarioDetailView,
)

app_name = "simulation"

urlpatterns = [
    # ── Cases ──────────────────────────────────────────────────────────────────
    path("cases/", SimulationCaseListCreateView.as_view(), name="case_list"),
    path("cases/<slug:slug>/", SimulationCaseDetailView.as_view(), name="case_detail"),

    # ── Laboratory Scenarios (Mentor Stories) ──────────────────────────────────
    path("scenarios/", SimulationScenarioListCreateView.as_view(), name="scenario_list_create"),
    path("scenarios/<uuid:pk>/", SimulationScenarioDetailView.as_view(), name="scenario_detail"),

    # ── Student Session Management ──────────────────────────────────────────────
    path("start/", StartSimulationView.as_view(), name="start_simulation"),
    path("<uuid:session_id>/turn/", SimulationTurnView.as_view(), name="simulation_turn"),
    path("<uuid:session_id>/abandon/", AbandonSessionView.as_view(), name="abandon_session"),

    # ── Student History ────────────────────────────────────────────────────────
    path("my-sessions/", MySessionListView.as_view(), name="my_sessions"),
    path("my-sessions/<uuid:pk>/", MySessionDetailView.as_view(), name="my_session_detail"),

    # ── Instructor Dashboard ────────────────────────────────────────────────────
    path("instructor/sessions/", InstructorSessionListView.as_view(), name="instructor_sessions"),
    path("instructor/sessions/<uuid:pk>/", InstructorSessionDetailView.as_view(), name="instructor_session_detail"),
    path("<uuid:session_id>/review/", InstructorReviewView.as_view(), name="instructor_review"),
]
