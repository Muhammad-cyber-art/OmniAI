"""
OmniLab AI - Users Views
Authentication, profile management, and portfolio endpoints.
"""
import json
import logging
import urllib.request
import uuid
from django.contrib.auth import get_user_model
from rest_framework import generics, status, views
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import UserProfile, UserRole
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

        # Deferred Auto-Join: check invite token from body or cookie
        invite_token = request.data.get("invite_token") or request.COOKIES.get("pending_invite_token")
        joined_group_data = None
        if invite_token:
            try:
                from apps.groups.services import GroupService
                success, msg, group = GroupService.join_group_with_token(user, invite_token)
                if success and group:
                    joined_group_data = {
                        "group_id": str(group.id),
                        "group_name": group.name,
                        "message": msg,
                    }
            except Exception as exc:
                logger.warning("Auto-join failed during registration: %s", exc)

        resp_data = {
            "success": True,
            "message": "Registration successful. Please verify your email.",
            "data": {
                "id": str(user.id),
                "email": user.email,
                "role": user.role,
                "joined_group": joined_group_data,
            },
        }
        response = Response(resp_data, status=status.HTTP_201_CREATED)
        if "pending_invite_token" in request.COOKIES:
            response.delete_cookie("pending_invite_token")
        return response


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


class GoogleAuthView(views.APIView):
    """
    POST /api/v1/auth/google/
    Body: { "id_token": "...", "invite_token": "..." (optional) }
    Authenticates or auto-registers user via Google OAuth.
    If 'pending_invite_token' cookie or 'invite_token' in body is present,
    automatically enrolls the new student into the mentor's group.
    """
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        id_token = request.data.get("id_token")
        email = request.data.get("email")
        first_name = request.data.get("first_name", "")
        last_name = request.data.get("last_name", "")

        # 1. Verify Google token if provided
        google_info = None
        if id_token:
            google_info = self._verify_google_token(id_token)

        if google_info:
            email = google_info.get("email") or email
            first_name = google_info.get("given_name") or first_name or google_info.get("name", "")
            last_name = google_info.get("family_name") or last_name

        if not email:
            return Response(
                {"success": False, "error": {"code": "INVALID_TOKEN", "message": "Google avtorizatsiyasi amalga oshmadi. Email topilmadi."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 2. Get or create user
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": email.split("@")[0] + "_" + str(uuid.uuid4())[:6],
                "first_name": first_name,
                "last_name": last_name,
                "role": UserRole.STUDENT,
                "is_email_verified": True,
            },
        )

        if created:
            logger.info("New user created via Google OAuth: %s", user.email)

        # 3. Check for invite token (body or cookie)
        invite_token = request.data.get("invite_token") or request.COOKIES.get("pending_invite_token")
        joined_group_data = None
        if invite_token:
            try:
                from apps.groups.services import GroupService
                success, msg, group = GroupService.join_group_with_token(user, invite_token)
                if success and group:
                    joined_group_data = {
                        "group_id": str(group.id),
                        "group_name": group.name,
                        "message": msg,
                    }
            except Exception as exc:
                logger.warning("Deferred auto-join failed in GoogleAuth: %s", exc)

        # 4. Generate JWT tokens
        refresh = CustomTokenObtainPairSerializer.get_token(user)
        resp_data = {
            "success": True,
            "message": "Google orqali tizimga muvaffaqiyatli kirildi.",
            "tokens": {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            "user": {
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "full_name": user.full_name,
                "role": user.role,
            },
            "joined_group": joined_group_data,
        }

        response = Response(resp_data, status=status.HTTP_200_OK)
        # Clear cookie
        if "pending_invite_token" in request.COOKIES:
            response.delete_cookie("pending_invite_token")
        return response

    def _verify_google_token(self, id_token: str):
        # Development / test tokens
        if id_token.startswith("mock_") or id_token.startswith("test_"):
            return {
                "email": f"{id_token.replace('mock_', '').replace('test_', '')}@gmail.com",
                "name": "Google Test User",
                "given_name": "Google",
                "family_name": "Tester",
            }

        try:
            url = f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())
                return data
        except Exception as e:
            logger.warning("Google tokeninfo check failed: %s", e)
            return None
