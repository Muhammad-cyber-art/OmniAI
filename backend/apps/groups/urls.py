"""
OmniLab AI - Groups URL Configuration
"""
from django.urls import path
from .views import (
    GroupListCreateView,
    GroupDetailView,
    GenerateInviteView,
    JoinGroupView,
    GroupMembersListView,
)

app_name = "groups"

urlpatterns = [
    # ── Group Management ───────────────────────────────────────────────────────
    path("", GroupListCreateView.as_view(), name="group_list_create"),
    path("<uuid:pk>/", GroupDetailView.as_view(), name="group_detail"),

    # ── Invite & Join Flow ────────────────────────────────────────────────────
    path("<uuid:pk>/generate-invite/", GenerateInviteView.as_view(), name="generate_invite"),
    path("join/<str:token>/", JoinGroupView.as_view(), name="join_group"),

    # ── Members ───────────────────────────────────────────────────────────────
    path("<uuid:pk>/members/", GroupMembersListView.as_view(), name="group_members"),
    path("<uuid:pk>/members/<uuid:student_id>/", GroupMembersListView.as_view(), name="remove_group_member"),
]
