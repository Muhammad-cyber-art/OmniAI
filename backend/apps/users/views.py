"""
OmniLab AI - Users Views
Authentication, profile management, and portfolio endpoints.
"""
import logging
from django.contrib.auth import get_user_model
from rest_framework import generics, status, views
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import UserProfile
from .permissions import IsRecruiter, IsAdminUser
from .serializers import (
    CustomTokenObtainPairSerializer,
    UserRegistrationSerializer,
    UserDetailSerializer,
    UserUpdateSerializer,
    ChangePasswordSerializer,
    PublicStudentPortfolioSerializer,
)

logger = logging.getLogger(__name__)
User = get_user_model()


class AuthIndexView(views.APIView):
    """
    GET /api/v1/auth/
    Returns directory of available authentication and profile endpoints.
    """
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        return Response(
            {
                "success": True,
                "message": "OmniLab AI Authentication Service",
                "endpoints": {
                    "register": {
                        "method": "POST",
                        "url": "/api/v1/auth/register/",
                        "description": "Register a new student or recruiter account",
                    },
                    "login": {
                        "method": "POST",
                        "url": "/api/v1/auth/login/",
                        "description": "Authenticate with email and password to receive JWT tokens",
                    },
                    "token_refresh": {
                        "method": "POST",
                        "url": "/api/v1/auth/token/refresh/",
                        "description": "Refresh expired access token using refresh token",
                    },
                    "token_verify": {
                        "method": "POST",
                        "url": "/api/v1/auth/token/verify/",
                        "description": "Verify access token validity",
                    },
                    "logout": {
                        "method": "POST",
                        "url": "/api/v1/auth/logout/",
                        "description": "Blacklist refresh token on sign out",
                    },
                    "me": {
                        "method": "GET, PUT, PATCH",
                        "url": "/api/v1/auth/me/",
                        "description": "Retrieve or update current user's profile and learning statistics",
                    },
                    "change_password": {
                        "method": "POST",
                        "url": "/api/v1/auth/change-password/",
                        "description": "Change password (requires old password)",
                    },
                    "public_students": {
                        "method": "GET",
                        "url": "/api/v1/auth/students/public/",
                        "description": "List top students with public portfolios (Recruiter only)",
                    },
                },
            },
            status=status.HTTP_200_OK,
        )


class CustomTokenObtainPairView(TokenObtainPairView):
    """JWT login endpoint that embeds role/email into the token."""
    serializer_class = CustomTokenObtainPairSerializer

    def get(self, request, *args, **kwargs):
        """Friendly guide when visiting /api/v1/auth/login/ via GET."""
        return Response(
            {
                "success": True,
                "message": "To log in, send an HTTP POST request with your email and password.",
                "endpoint": "POST /api/v1/auth/login/",
                "request_body_example": {
                    "email": "user@example.com",
                    "password": "YourPassword123!",
                },
                "documentation": "Returns JWT access and refresh tokens.",
            },
            status=status.HTTP_200_OK,
        )


class UserRegistrationView(generics.CreateAPIView):
    """
    POST /api/v1/auth/register/
    Open endpoint - creates a new user account.
    Wallet & quota are provisioned via post_save signal.
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        """Friendly guide when visiting /api/v1/auth/register/ via GET."""
        return Response(
            {
                "success": True,
                "message": "To register, send an HTTP POST request with the required user fields.",
                "endpoint": "POST /api/v1/auth/register/",
                "request_body_example": {
                    "email": "user@example.com",
                    "username": "unique_username",
                    "password": "Password123!",
                    "password_confirm": "Password123!",
                    "role": "STUDENT",
                    "first_name": "Ali",
                    "last_name": "Valiyev",
                },
                "allowed_roles": ["STUDENT", "RECRUITER"],
            },
            status=status.HTTP_200_OK,
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        logger.info("New user registered: %s (role=%s)", user.email, user.role)
        return Response(
            {
                "success": True,
                "message": "Registration successful. Please verify your email.",
                "data": {"id": str(user.id), "email": user.email, "role": user.role},
            },
            status=status.HTTP_201_CREATED,
        )


class MeView(generics.RetrieveUpdateAPIView):
    """
    GET  /api/v1/auth/me/  → full profile detail
    PATCH/PUT /api/v1/auth/me/ → update safe fields + nested profile
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return UserUpdateSerializer
        return UserDetailSerializer

    def get_object(self):
        return User.objects.select_related("profile").get(id=self.request.user.id)


class ChangePasswordView(views.APIView):
    """
    POST /api/v1/auth/change-password/
    Requires old password verification before setting new one.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save(update_fields=["password"])
        logger.info("Password changed for user: %s", request.user.email)
        return Response(
            {"success": True, "message": "Password changed successfully."},
            status=status.HTTP_200_OK,
        )


class PublicStudentListView(generics.ListAPIView):
    """
    GET /api/v1/auth/students/public/
    Only RECRUITERs can see the list of students with public portfolios.
    """
    serializer_class = PublicStudentPortfolioSerializer
    permission_classes = [IsRecruiter]

    def get_queryset(self):
        return (
            User.objects.filter(role="STUDENT", is_portfolio_public=True, is_active=True)
            .select_related("profile")
            .order_by("-profile__total_simulations_completed")
        )


class PublicStudentDetailView(generics.RetrieveAPIView):
    """
    GET /api/v1/auth/students/<uuid:pk>/portfolio/
    Recruiter can fetch one student's public portfolio.
    """
    serializer_class = PublicStudentPortfolioSerializer
    permission_classes = [IsRecruiter]

    def get_queryset(self):
        return User.objects.filter(role="STUDENT", is_portfolio_public=True, is_active=True).select_related("profile")


class UserListView(generics.ListAPIView):
    """
    GET /api/v1/auth/users/
    Admin-only: full user list with filtering.
    """
    serializer_class = UserDetailSerializer
    permission_classes = [IsAdminUser]
    filterset_fields = ["role", "is_active", "is_email_verified"]
    search_fields = ["email", "username", "first_name", "last_name"]
    ordering_fields = ["date_joined", "email"]

    def get_queryset(self):
        return User.objects.select_related("profile").all()
