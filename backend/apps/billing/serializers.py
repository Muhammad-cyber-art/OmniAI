"""
OmniLab AI - Billing Serializers
"""
from decimal import Decimal
from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import (
    SubscriptionPlan,
    UserSubscription,
    Wallet,
    WalletTransaction,
    UserQuotaUsage,
)

User = get_user_model()


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = [
            "id",
            "tier",
            "name",
            "description",
            "price_uzs",
            "price_coins",
            "welcome_coins",
            "coin_multiplier",
            "monthly_simulations",
            "daily_ai_turns",
            "free_hints",
            "allowed_retries",
            "max_active_sessions",
            "duration_days",
        ]


class UserSubscriptionSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSerializer(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = UserSubscription
        fields = [
            "id",
            "plan",
            "is_active",
            "payment_method",
            "amount_paid_uzs",
            "amount_paid_coins",
            "started_at",
            "expires_at",
            "is_expired",
        ]
        read_only_fields = fields


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ["balance", "lifetime_earned", "lifetime_spent", "updated_at"]
        read_only_fields = fields


class WalletTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletTransaction
        fields = [
            "id",
            "transaction_type",
            "amount",
            "balance_after",
            "description",
            "created_at",
        ]
        read_only_fields = fields


class UserQuotaUsageSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source="plan.name", read_only=True)
    plan_tier = serializers.CharField(source="plan.tier", read_only=True)
    monthly_simulations_limit = serializers.IntegerField(source="plan.monthly_simulations", read_only=True)
    daily_ai_turns_limit = serializers.IntegerField(source="plan.daily_ai_turns", read_only=True)
    free_hints_limit = serializers.IntegerField(source="plan.free_hints", read_only=True)

    class Meta:
        model = UserQuotaUsage
        fields = [
            "plan_name",
            "plan_tier",
            "monthly_simulations_used",
            "monthly_simulations_limit",
            "daily_ai_turns_used",
            "daily_ai_turns_limit",
            "monthly_hints_used",
            "free_hints_limit",
            "active_sessions_count",
            "monthly_reset_date",
            "daily_reset_date",
        ]
        read_only_fields = fields


# ── Purchase Serializers ──────────────────────────────────────────────────────

class PurchaseWithCoinsSerializer(serializers.Serializer):
    plan_tier = serializers.ChoiceField(choices=["STANDARD", "PREMIUM"])


class PurchaseWithMoneySerializer(serializers.Serializer):
    plan_tier = serializers.ChoiceField(choices=["STANDARD", "PREMIUM"])
    payment_reference = serializers.CharField(max_length=255)
    amount_paid_uzs = serializers.IntegerField(min_value=1)


class HintRequestSerializer(serializers.Serializer):
    session_id = serializers.UUIDField()
