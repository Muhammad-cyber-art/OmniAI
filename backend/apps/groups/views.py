"""
OmniLab AI - Groups Views
Group management, invitation link generation, token verification, and enrollment.
"""
import logging
from django.db.models import Count, Q, Prefetch
from rest_framework import generics, status, views
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from apps.curriculum.models import Course
from apps.users.permissions import IsStudent
from .models import Group, GroupMembership, GroupInvitation
from .permissions import IsMentor, IsGroupMentorOrAdmin
from .serializers import (
    GroupListSerializer,
    GroupDetailSerializer,
    GroupWriteSerializer,
    GroupInvitationSerializer,
    GenerateInviteSerializer,
    GroupMembershipSerializer,
)
from .services import GroupService

logger = logging.getLogger(__name__)


class GroupListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/v1/groups/
         - Mentors: see groups they manage.
         - Students: see groups they are enrolled in.
         - Admins: see all groups.
    POST /api/v1/groups/
         - Mentors and Admins create a new cohort group.
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return GroupWriteSerializer
        return GroupListSerializer

    def get_queryset(self):
        user = self.request.user
        base_qs = (
            Group.objects.select_related("mentor")
            .prefetch_related("courses")
            .annotate(
                _annotated_student_count=Count(
                    "memberships",
                    filter=Q(memberships__status="ACTIVE"),
                    distinct=True,
                ),
                _annotated_courses_count=Count("courses", distinct=True),
            )
            .order_by("-created_at")
        )
        if user.role == "ADMIN":
            return base_qs.all()
        if user.role == "INSTRUCTOR":
            return base_qs.filter(mentor=user)
        # Students see groups they belong to
        return base_qs.filter(memberships__student=user, memberships__status="ACTIVE")

    def perform_create(self, serializer):
        serializer.save(mentor=self.request.user)

    def create(self, request, *args, **kwargs):
        if request.user.role not in ("INSTRUCTOR", "ADMIN"):
            return Response(
                {"success": False, "error": {"code": "PERMISSION_DENIED", "message": "Faqat mentorlar guruh yarata oladi."}},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            {"success": True, "message": "Guruh muvaffaqiyatli yaratildi.", "data": serializer.data},
            status=status.HTTP_201_CREATED,
        )


class GroupDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/v1/groups/<uuid:pk>/
    PATCH  /api/v1/groups/<uuid:pk>/ (Mentor / Admin)
    DELETE /api/v1/groups/<uuid:pk>/ (Mentor / Admin)
    """
    permission_classes = [IsAuthenticated, IsGroupMentorOrAdmin]

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return GroupWriteSerializer
        return GroupDetailSerializer

    def get_queryset(self):
        return (
            Group.objects.select_related("mentor")
            .prefetch_related(
                Prefetch(
                    "courses",
                    queryset=Course.objects.select_related("domain", "instructor"),
                ),
                Prefetch(
                    "memberships",
                    queryset=GroupMembership.objects.filter(status="ACTIVE").select_related("student"),
                    to_attr="active_memberships",
                ),
            )
            .annotate(
                _annotated_student_count=Count(
                    "memberships",
                    filter=Q(memberships__status="ACTIVE"),
                    distinct=True,
                ),
                _annotated_courses_count=Count("courses", distinct=True),
            )
        )


class GenerateInviteView(views.APIView):
    """
    POST /api/v1/groups/<uuid:pk>/generate-invite/
    Mentor generates a unique cryptographically secure invitation link.
    """
    permission_classes = [IsAuthenticated, IsMentor]

    def post(self, request, pk, *args, **kwargs):
        try:
            group = Group.objects.get(pk=pk)
        except Group.DoesNotExist:
            return Response(
                {"success": False, "error": {"code": "NOT_FOUND", "message": "Guruh topilmadi."}},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check ownership
        if request.user.role != "ADMIN" and group.mentor != request.user:
            return Response(
                {"success": False, "error": {"code": "PERMISSION_DENIED", "message": "Siz ushbu guruh mentori emassiz."}},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = GenerateInviteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        invitation = GroupService.generate_invite(
            group=group,
            creator=request.user,
            expires_in_days=serializer.validated_data["expires_in_days"],
            max_uses=serializer.validated_data["max_uses"],
        )

        inv_serializer = GroupInvitationSerializer(invitation, context={"request": request})
        return Response(
            {
                "success": True,
                "message": "Taklif havolasi muvaffaqiyatli yaratildi.",
                "data": inv_serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )


class JoinGroupView(views.APIView):
    """
    GET  /api/v1/groups/join/<str:token>/
         - Validates invite token.
         - Returns group preview information.
         - If user is unauthenticated, sets 'pending_invite_token' cookie for deferred OAuth auto-join!
    POST /api/v1/groups/join/<str:token>/
         - Authenticated student joins the group immediately.
    """
    permission_classes = [AllowAny]

    def get(self, request, token, *args, **kwargs):
        is_valid, message, invitation = GroupService.validate_invite(token)
        if not is_valid or not invitation:
            return Response(
                {"success": False, "error": {"code": "INVALID_INVITE", "message": message}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        group = invitation.group
        courses_list = [{"id": str(c.id), "title": c.title, "slug": c.slug} for c in group.courses.all()]

        # Check if current user is already member
        is_member = False
        if request.user and request.user.is_authenticated:
            is_member = GroupMembership.objects.filter(group=group, student=request.user, status="ACTIVE").exists()

        data = {
            "token": token,
            "group_id": str(group.id),
            "group_name": group.name,
            "description": group.description,
            "mentor_name": group.mentor.full_name,
            "mentor_email": group.mentor.email,
            "courses": courses_list,
            "is_member": is_member,
            "expires_at": invitation.expires_at,
            "user_authenticated": request.user.is_authenticated,
        }

        response = Response({
            "success": True,
            "message": "Taklifnoma yaroqli.",
            "data": data,
        })

        # If user is unauthenticated, store token in HttpOnly cookie
        # so when they sign in via Google OAuth or Register, backend auto-enrolls them!
        if not request.user.is_authenticated:
            response.set_cookie(
                key="pending_invite_token",
                value=token,
                max_age=86400 * 7,  # 7 days
                httponly=True,
                samesite="Lax",
            )
            logger.info("Set pending_invite_token cookie for token %s", token[:8])

        return response

    def post(self, request, token, *args, **kwargs):
        if not request.user or not request.user.is_authenticated:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "UNAUTHORIZED",
                        "message": "Guruhga qo'shilish uchun tizimga kirishingiz yoki ro'yxatdan o'tishingiz lozim.",
                    },
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if request.user.role not in ("STUDENT", "ADMIN"):
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "ROLE_NOT_ALLOWED",
                        "message": "Faqat talabalar guruhga a'zo bo'la oladi.",
                    },
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        success, message, group = GroupService.join_group_with_token(request.user, token)
        if not success:
            return Response(
                {"success": False, "error": {"code": "JOIN_FAILED", "message": message}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        response = Response({
            "success": True,
            "message": message,
            "data": {
                "group_id": str(group.id),
                "group_name": group.name,
                "mentor": group.mentor.full_name,
            },
        })
        # Clear the cookie if it existed
        response.delete_cookie("pending_invite_token")
        return response


class GroupMembersListView(views.APIView):
    """
    GET    /api/v1/groups/<uuid:pk>/members/
           - List all students enrolled in the group.
    DELETE /api/v1/groups/<uuid:pk>/members/<uuid:student_id>/
           - Mentor removes a student from the group.
    """
    permission_classes = [IsAuthenticated, IsGroupMentorOrAdmin]

    def get(self, request, pk, *args, **kwargs):
        try:
            group = Group.objects.get(pk=pk)
        except Group.DoesNotExist:
            return Response(
                {"success": False, "error": {"code": "NOT_FOUND", "message": "Guruh topilmadi."}},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check permission
        if request.user.role != "ADMIN" and group.mentor != request.user:
            return Response(
                {"success": False, "error": {"code": "PERMISSION_DENIED", "message": "Ruxsat berilmadi."}},
                status=status.HTTP_403_FORBIDDEN,
            )

        memberships = list(group.memberships.select_related("student", "student__profile").all())
        serializer = GroupMembershipSerializer(memberships, many=True)
        return Response({"success": True, "count": len(memberships), "data": serializer.data})

    def delete(self, request, pk, student_id, *args, **kwargs):
        try:
            group = Group.objects.get(pk=pk)
            membership = GroupMembership.objects.get(group=group, student_id=student_id)
        except (Group.DoesNotExist, GroupMembership.DoesNotExist):
            return Response(
                {"success": False, "error": {"code": "NOT_FOUND", "message": "A'zolik topilmadi."}},
                status=status.HTTP_404_NOT_FOUND,
            )

        if request.user.role != "ADMIN" and group.mentor != request.user:
            return Response(
                {"success": False, "error": {"code": "PERMISSION_DENIED", "message": "Ruxsat berilmadi."}},
                status=status.HTTP_403_FORBIDDEN,
            )

        membership.delete()
        return Response({"success": True, "message": "Talaba guruhdan chiqarildi."})
