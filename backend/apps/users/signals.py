"""
OmniLab AI - Users App Signals
Auto-creates wallet and quota on user registration.
"""
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.conf import settings

logger = logging.getLogger(__name__)
User = get_user_model()


@receiver(post_save, sender=User)
def provision_new_user(sender, instance, created, **kwargs):
    """
    On new user creation:
    1. Create Wallet with welcome coins based on plan (FREE by default)
    2. Create UserSubscription with FREE plan
    3. Create UserQuotaUsage record
    """
    if not created:
        return

    try:
        from apps.users.models import UserProfile
        UserProfile.objects.get_or_create(user=instance)

        from apps.billing.models import (
            Wallet,
            WalletTransaction,
            SubscriptionPlan,
            UserSubscription,
            UserQuotaUsage,
        )

        # 1. Get or create FREE plan
        free_plan, _ = SubscriptionPlan.objects.get_or_create(
            tier="FREE",
            defaults={
                "name": "Free",
                "price_uzs": 0,
                "price_coins": 0,
                "welcome_coins": settings.WELCOME_COINS_FREE,
                "coin_multiplier": "1.00",
                "monthly_simulations": 5,
                "daily_ai_turns": 10,
                "free_hints": 3,
                "allowed_retries": 1,
                "max_active_sessions": 1,
                "duration_days": 36500,  # "Lifetime" free tier
            },
        )

        # 2. Create Wallet
        wallet = Wallet.objects.create(
            user=instance,
            balance=free_plan.welcome_coins,
        )

        # 3. Log welcome coins transaction
        if free_plan.welcome_coins > 0:
            WalletTransaction.objects.create(
                wallet=wallet,
                amount=free_plan.welcome_coins,
                balance_after=free_plan.welcome_coins,
                transaction_type="WELCOME_BONUS",
                description=f"Welcome bonus for joining OmniLab AI ({free_plan.name} plan)",
            )

        # 4. Create FREE subscription
        from django.utils import timezone
        from datetime import timedelta

        UserSubscription.objects.create(
            user=instance,
            plan=free_plan,
            is_active=True,
            started_at=timezone.now(),
            expires_at=timezone.now() + timedelta(days=free_plan.duration_days),
        )

        # 5. Create quota usage tracker
        UserQuotaUsage.objects.create(user=instance, plan=free_plan)

        logger.info(
            "Provisioned new user %s: wallet(%d coins), FREE subscription",
            instance.email,
            free_plan.welcome_coins,
        )

    except Exception as exc:
        logger.exception("Failed to provision user %s: %s", instance.email, exc)
