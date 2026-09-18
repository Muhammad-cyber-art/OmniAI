"""
OmniLab AI - Groups Permissions
Role-based access control for Group and Invitation endpoints.
"""
from rest_framework.permissions import BasePermission


class IsMentor(BasePermission):
    """Allows access only to INSTRUCTOR or ADMIN roles."""
    message = "Faqat mentorlar yoki adminlar ushbu amalni bajara oladi."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in ("INSTRUCTOR", "ADMIN")
        )


class IsGroupMentorOrAdmin(BasePermission):
    """
    Object-level permission: allows if request.user is the mentor of the group or an ADMIN.
    """
    message = "Siz ushbu guruh mentori emassiz."

    def has_object_permission(self, request, view, obj):
        if request.user.role == "ADMIN":
            return True
        mentor = getattr(obj, "mentor", None)
        if mentor is None and hasattr(obj, "group"):
            mentor = obj.group.mentor
        return mentor == request.user
