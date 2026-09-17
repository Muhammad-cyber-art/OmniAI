"""
OmniLab AI - Billing Admin Configuration
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import (
    SubscriptionPlan,
    UserSubscription,
    Wallet,
    WalletTransaction,
    UserQuotaUsage,
)


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "tier",
        "price_uzs_display",
        "price_coins_display",
        "monthly_simulations",
        "daily_ai_turns",
        "coin_multiplier",
        "is_active",
    )
    list_filter = ("tier", "is_active")
    search_fields = ("name", "tier")
    readonly_fields = ("id", "created_at", "updated_at")

    fieldsets = (
        ("Plan Info", {"fields": ("id", "tier", "name", "description", "is_active")}),
        ("Pricing", {"fields": ("price_uzs", "price_coins", "duration_days")}),
        ("Entitlements", {
            "fields": (
                "welcome_coins",
                "coin_multiplier",
                "monthly_simulations",
                "daily_ai_turns",
                "free_hints",
                "allowed_retries",
                "max_active_sessions",
            )
        }),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    @admin.display(description="Price (UZS)")
    def price_uzs_display(self, obj):
        return f"{obj.price_uzs:,} so'm" if obj.price_uzs else "Free"

    @admin.display(description="Price (Coins)")
    def price_coins_display(self, obj):
        return f"🪙 {obj.price_coins:,}" if obj.price_coins else "Free"


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "plan",
        "status_badge",
        "payment_method",
        "started_at",
        "expires_at",
    )
    list_filter = ("is_active", "payment_method", "plan__tier")
    search_fields = ("user__email", "user__username", "payment_reference")
    readonly_fields = ("id", "created_at")
    date_hierarchy = "started_at"
    ordering = ("-started_at",)

    @admin.display(description="Status")
    def status_badge(self, obj):
        if obj.is_active and not obj.is_expired:
            return format_html('<span style="color:#10B981;font-weight:bold;">● ACTIVE</span>')
        elif obj.is_active and obj.is_expired:
            return format_html('<span style="color:#EF4444;font-weight:bold;">● EXPIRED</span>')
        return format_html('<span style="color:#6B7280;">● INACTIVE</span>')


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ("user", "balance_display", "lifetime_earned_display", "lifetime_spent_display", "updated_at")
    search_fields = ("user__email", "user__username")
    readonly_fields = ("user", "balance", "lifetime_earned", "lifetime_spent", "updated_at")

    @admin.display(description="Balance")
    def balance_display(self, obj):
        return format_html(
            '<strong style="color:#10B981;">🪙 {:,}</strong>', obj.balance
        )

    @admin.display(description="Total Earned")
    def lifetime_earned_display(self, obj):
        return f"🪙 {obj.lifetime_earned:,}"

    @admin.display(description="Total Spent")
    def lifetime_spent_display(self, obj):
        return f"🪙 {obj.lifetime_spent:,}"

    def has_add_permission(self, request):
        return False


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "wallet_user",
        "transaction_type",
        "amount_display",
        "balance_after",
        "description",
        "created_at",
    )
    list_filter = ("transaction_type", "created_at")
    search_fields = ("wallet__user__email", "description")
    readonly_fields = (
        "id",
        "wallet",
        "transaction_type",
        "amount",
        "balance_after",
        "description",
        "simulation_session",
        "subscription",
        "created_at",
    )
    date_hierarchy = "created_at"
    ordering = ("-created_at",)

    @admin.display(description="User")
    def wallet_user(self, obj):
        return obj.wallet.user.email

    @admin.display(description="Amount")
    def amount_display(self, obj):
        if obj.amount > 0:
            return format_html('<span style="color:#10B981;">+{:,}</span>', obj.amount)
        return format_html('<span style="color:#EF4444;">{:,}</span>', obj.amount)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(UserQuotaUsage)
class UserQuotaUsageAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "plan",
        "monthly_simulations_display",
        "daily_ai_turns_display",
        "active_sessions_count",
        "monthly_reset_date",
        "daily_reset_date",
    )
    list_filter = ("plan__tier",)
    search_fields = ("user__email",)
    readonly_fields = ("user", "updated_at")

    @admin.display(description="Monthly Simulations")
    def monthly_simulations_display(self, obj):
        used = obj.monthly_simulations_used
        limit = obj.plan.monthly_simulations
        pct = (used / limit * 100) if limit else 0
        color = "#EF4444" if pct >= 90 else "#F59E0B" if pct >= 70 else "#10B981"
        return format_html(
            '<span style="color:{};">{}/{}</span>', color, used, limit
        )

    @admin.display(description="Daily AI Turns")
    def daily_ai_turns_display(self, obj):
        used = obj.daily_ai_turns_used
        limit = obj.plan.daily_ai_turns
        pct = (used / limit * 100) if limit else 0
        color = "#EF4444" if pct >= 90 else "#F59E0B" if pct >= 70 else "#10B981"
        return format_html(
            '<span style="color:{};">{}/{}</span>', color, used, limit
        )
