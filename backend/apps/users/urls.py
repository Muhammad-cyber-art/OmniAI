"""OmniLab AI - Users URL Configuration"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenBlacklistView

from .views import (
    AuthIndexView,
    CustomTokenObtainPairView,
    UserRegistrationView,
    MeView,
    ChangePasswordView,
    PublicStudentListView,
    PublicStudentDetailView,
    UserListView,
)

app_name = "users"

urlpatterns = [
    # Auth root index
    path("", AuthIndexView.as_view(), name="index"),

    # Auth endpoints
    path("register/", UserRegistrationView.as_view(), name="register"),
    path("login/", CustomTokenObtainPairView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("logout/", TokenBlacklistView.as_view(), name="logout"),

    # Profile
    path("me/", MeView.as_view(), name="me"),
    path("change-password/", ChangePasswordView.as_view(), name="change_password"),

    # Admin
    path("users/", UserListView.as_view(), name="user_list"),

    # Portfolio (Recruiter)
    path("students/public/", PublicStudentListView.as_view(), name="public_students"),
    path("students/<uuid:pk>/portfolio/", PublicStudentDetailView.as_view(), name="student_portfolio"),
]
