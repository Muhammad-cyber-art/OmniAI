"""
OmniLab AI - Groups App Models
Group, GroupMembership, GroupInvitation for Mentor-Student collaboration.
"""
import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from apps.users.models import UserRole

User = get_user_model()


class Group(models.Model):
    """
    Mentor-managed study group or cohort.
    Mentors invite students, assign courses, and track simulation performance.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_("Group Name"), max_length=255)
    description = models.TextField(_("Description"), blank=True)

    mentor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="mentored_groups",
        limit_choices_to={"role__in": [UserRole.INSTRUCTOR, UserRole.ADMIN]},
        help_text=_("The mentor / instructor managing this cohort."),
    )
    courses = models.ManyToManyField(
        "curriculum.Course",
        related_name="groups",
        blank=True,
        help_text=_("Curriculum courses assigned to this group."),
    )
    students = models.ManyToManyField(
        User,
        through="GroupMembership",
        related_name="enrolled_groups",
        blank=True,
    )

    is_active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "groups_group"
        verbose_name = _("Group")
        verbose_name_plural = _("Groups")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["mentor", "is_active"], name="idx_group_mentor_active"),
        ]

    def __str__(self) -> str:
        return f"{self.name} (Mentor: {self.mentor.email})"

    @property
    def student_count(self) -> int:
        if hasattr(self, "_annotated_student_count"):
            return self._annotated_student_count
        if hasattr(self, "_prefetched_objects_cache") and "memberships" in self._prefetched_objects_cache:
            return sum(1 for m in self.memberships.all() if m.status == "ACTIVE")
        return self.memberships.filter(status="ACTIVE").count()

    @property
    def courses_count(self) -> int:
        if hasattr(self, "_annotated_courses_count"):
            return self._annotated_courses_count
        if hasattr(self, "_prefetched_objects_cache") and "courses" in self._prefetched_objects_cache:
            return len(self.courses.all())
        return self.courses.count()


class GroupMembership(models.Model):
    """
    Through-table linking a student to a group with status and join date.
    """

    class MembershipStatus(models.TextChoices):
        ACTIVE = "ACTIVE", _("Active")
        SUSPENDED = "SUSPENDED", _("Suspended")
        COMPLETED = "COMPLETED", _("Completed")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="group_memberships",
        limit_choices_to={"role": UserRole.STUDENT},
    )
    status = models.CharField(
        max_length=20,
        choices=MembershipStatus.choices,
        default=MembershipStatus.ACTIVE,
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "groups_group_membership"
        verbose_name = _("Group Membership")
        verbose_name_plural = _("Group Memberships")
        ordering = ["-joined_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["group", "student"],
                name="unique_student_group_membership",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.student.email} in {self.group.name} [{self.status}]"


class GroupInvitation(models.Model):
    """
    Shareable invitation link with cryptographic token for quick student enrollment.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="invitations",
    )
    token = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text=_("URL-safe unique invitation token."),
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_invitations",
    )

    expires_at = models.DateTimeField(
        help_text=_("Expiration timestamp after which link is no longer valid."),
    )
    max_uses = models.PositiveIntegerField(
        default=0,
        help_text=_("Maximum number of times this link can be used. 0 = unlimited."),
    )
    times_used = models.PositiveIntegerField(
        default=0,
        help_text=_("Total number of times a student joined via this token."),
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_("Allows mentor to deactivate/revoke the invite link manually."),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "groups_group_invitation"
        verbose_name = _("Group Invitation")
        verbose_name_plural = _("Group Invitations")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Invite({self.group.name}) [{self.token[:8]}...]"

    @property
    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at

    @property
    def is_valid(self) -> bool:
        if not self.is_active:
            return False
        if self.is_expired:
            return False
        if self.max_uses > 0 and self.times_used >= self.max_uses:
            return False
        return True
