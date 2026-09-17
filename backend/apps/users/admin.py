"""
OmniLab AI - Users Admin Configuration
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html

from .models import User, UserProfile, LoginHistory


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "Profile"
    fields = (
        "bio",
        "avatar_url",
        "institution",
        "specialization",
        "total_simulations_completed",
        "total_coins_earned",
        "current_streak_days",
        "longest_streak_days",
        "last_activity_date",
    )
    readonly_fields = (
        "total_simulations_completed",
        "total_coins_earned",
        "current_streak_days",
        "longest_streak_days",
        "last_activity_date",
    )


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    inlines = [UserProfileInline]

    list_display = (
        "email",
        "username",
        "full_name_display",
        "role_badge",
        "is_active",
        "is_email_verified",
        "wallet_balance_display",
        "date_joined",
    )
    list_filter = ("role", "is_active", "is_email_verified", "is_portfolio_public", "date_joined")
    search_fields = ("email", "username", "first_name", "last_name")
    ordering = ("-date_joined",)
    readonly_fields = ("id", "date_joined", "last_login", "updated_at")

    fieldsets = (
        (None, {"fields": ("id", "email", "password")}),
        (_("Personal info"), {"fields": ("username", "first_name", "last_name")}),
        (_("Role & Status"), {"fields": ("role", "is_active", "is_staff", "is_superuser", "is_email_verified", "is_portfolio_public")}),
        (_("Permissions"), {"fields": ("groups", "user_permissions"), "classes": ("collapse",)}),
        (_("Timestamps"), {"fields": ("date_joined", "last_login", "updated_at")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "username", "role", "password1", "password2"),
        }),
    )

    @admin.display(description="Full Name")
    def full_name_display(self, obj):
        return obj.full_name

    @admin.display(description="Role")
    def role_badge(self, obj):
        colors = {
            "STUDENT": "#3B82F6",
            "INSTRUCTOR": "#10B981",
            "ADMIN": "#EF4444",
            "RECRUITER": "#8B5CF6",
        }
        color = colors.get(obj.role, "#6B7280")
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:4px;font-size:11px;">{}</span>',
            color,
            obj.get_role_display(),
        )

    @admin.display(description="Wallet Balance")
    def wallet_balance_display(self, obj):
        try:
            return f"🪙 {obj.wallet.balance:,}"
        except Exception:
            return "—"


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "total_simulations_completed",
        "total_coins_earned",
        "current_streak_days",
        "last_activity_date",
    )
    search_fields = ("user__email", "user__username")
    readonly_fields = (
        "total_simulations_completed",
        "total_coins_earned",
        "current_streak_days",
        "longest_streak_days",
        "last_activity_date",
    )


@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = ("user", "ip_address", "success", "created_at")
    list_filter = ("success", "created_at")
    search_fields = ("user__email",)
    readonly_fields = ("user", "ip_address", "user_agent", "success", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
