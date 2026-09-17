"""
OmniLab AI - Users App Models
Custom AbstractBaseUser with RBAC roles and profile.
"""
import uuid
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class UserRole(models.TextChoices):
    STUDENT = "STUDENT", _("Student")
    INSTRUCTOR = "INSTRUCTOR", _("Instructor")
    ADMIN = "ADMIN", _("Admin")
    RECRUITER = "RECRUITER", _("Recruiter")


class UserManager(BaseUserManager):
    """Custom user manager that uses email as the unique identifier."""

    def _create_user(self, email: str, password: str, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str = None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("role", UserRole.STUDENT)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email: str, password: str, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", UserRole.ADMIN)
        extra_fields.setdefault("is_active", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    OmniLab AI Custom User Model.
    Primary key: UUID for security & scalability.
    Authentication: Email + Password.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_("email address"), unique=True, db_index=True)
    username = models.CharField(
        _("username"),
        max_length=64,
        unique=True,
        db_index=True,
        help_text=_("Required. Max 64 characters. Letters, digits and @/./+/-/_ only."),
    )
    first_name = models.CharField(_("first name"), max_length=64, blank=True)
    last_name = models.CharField(_("last name"), max_length=64, blank=True)

    role = models.CharField(
        _("role"),
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.STUDENT,
        db_index=True,
    )

    # Account state
    is_active = models.BooleanField(_("active"), default=True)
    is_staff = models.BooleanField(_("staff status"), default=False)
    is_email_verified = models.BooleanField(_("email verified"), default=False)

    # Portfolio visibility (RECRUITER can view if True)
    is_portfolio_public = models.BooleanField(
        _("portfolio public"),
        default=False,
        help_text=_("Allow recruiters to view this student's portfolio and certifications."),
    )

    # Timestamps
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)
    last_login = models.DateTimeField(_("last login"), blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    objects = UserManager()

    class Meta:
        db_table = "users_user"
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        ordering = ["-date_joined"]
        indexes = [
            models.Index(fields=["role", "is_active"], name="idx_user_role_active"),
        ]

    def __str__(self) -> str:
        return f"{self.email} ({self.get_role_display()})"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip() or self.username

    @property
    def is_student(self) -> bool:
        return self.role == UserRole.STUDENT

    @property
    def is_instructor(self) -> bool:
        return self.role == UserRole.INSTRUCTOR

    @property
    def is_admin_user(self) -> bool:
        return self.role == UserRole.ADMIN

    @property
    def is_recruiter(self) -> bool:
        return self.role == UserRole.RECRUITER


class UserProfile(models.Model):
    """
    Extended profile data for Students and Instructors.
    Separated from User for normalization and performance.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
        primary_key=True,
    )
    bio = models.TextField(_("biography"), blank=True, max_length=1000)
    avatar_url = models.URLField(_("avatar URL"), blank=True)
    linkedin_url = models.URLField(_("LinkedIn URL"), blank=True)
    github_url = models.URLField(_("GitHub URL"), blank=True)

    # Learning stats (denormalized for quick reads)
    total_simulations_completed = models.PositiveIntegerField(default=0)
    total_coins_earned = models.PositiveBigIntegerField(default=0)
    current_streak_days = models.PositiveIntegerField(
        default=0,
        help_text=_("Consecutive days with at least one completed simulation."),
    )
    longest_streak_days = models.PositiveIntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)

    # Instructor-specific
    institution = models.CharField(max_length=255, blank=True)
    specialization = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "users_profile"
        verbose_name = _("User Profile")
        verbose_name_plural = _("User Profiles")

    def __str__(self) -> str:
        return f"Profile of {self.user.email}"


class LoginHistory(models.Model):
    """Audit trail for user logins."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="login_history")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    success = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "users_login_history"
        verbose_name = _("Login History")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"], name="idx_login_user_time"),
        ]

    def __str__(self) -> str:
        status = "SUCCESS" if self.success else "FAILED"
        return f"{self.user.email} - {status} @ {self.created_at}"
