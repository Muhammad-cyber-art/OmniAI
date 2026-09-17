"""
OmniLab AI - Custom DRF Permission Classes
Provides role-based access control for all API endpoints.
"""
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsStudent(BasePermission):
    """Allows access only to STUDENT role users."""
    message = "Only students can perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "STUDENT"
        )


class IsInstructor(BasePermission):
    """Allows access only to INSTRUCTOR role users."""
    message = "Only instructors can perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "INSTRUCTOR"
        )


class IsAdminUser(BasePermission):
    """Allows access only to ADMIN role users."""
    message = "Only admins can perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "ADMIN"
        )


class IsRecruiter(BasePermission):
    """Allows access only to RECRUITER role users."""
    message = "Only recruiters can perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "RECRUITER"
        )


class IsStudentOrInstructor(BasePermission):
    """Allows access to STUDENT or INSTRUCTOR roles."""
    message = "Only students or instructors can perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in ("STUDENT", "INSTRUCTOR")
        )


class IsInstructorOrAdmin(BasePermission):
    """Allows access to INSTRUCTOR or ADMIN roles."""
    message = "Only instructors or admins can perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in ("INSTRUCTOR", "ADMIN")
        )


class IsOwnerOrAdmin(BasePermission):
    """
    Object-level permission: allow if the request user owns the object
    (obj.user == request.user) OR is an ADMIN.
    Objects must have a .user attribute.
    """
    message = "You do not have permission to access this resource."

    def has_object_permission(self, request, view, obj):
        if request.user.role == "ADMIN":
            return True
        owner = getattr(obj, "user", getattr(obj, "student", None))
        return owner == request.user


class HasActiveSubscription(BasePermission):
    """
    Verifies the student has a non-expired active subscription.
    Used as a guard on premium endpoints.
    """
    message = "An active subscription is required to access this resource."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.role != "STUDENT":
            return True  # non-students bypass subscription checks
        # Lazy import to avoid circular dependency
        from apps.billing.models import UserSubscription
        return UserSubscription.objects.filter(
            user=request.user,
            is_active=True,
        ).exists()


class HasActiveQuota(BasePermission):
    """
    Checks that the student still has remaining quota for simulations.
    Used on simulation start/turn endpoints.
    """
    message = "You have exhausted your monthly simulation quota. Please upgrade your plan."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.role != "STUDENT":
            return True
        from apps.billing.services import BillingService
        can_start, reason = BillingService.can_start_simulation(request.user)
        if not can_start:
            self.message = reason
        return can_start
