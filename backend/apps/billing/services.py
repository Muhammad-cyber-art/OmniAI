"""
OmniLab AI - BillingService
Atomic business logic for subscriptions, wallet operations, and quota management.
"""
import logging
from decimal import Decimal
from typing import Tuple, Optional
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from django.conf import settings

from apps.billing.models import (
    SubscriptionPlan,
    UserSubscription,
    SubscriptionPaymentMethod,
    Wallet,
    WalletTransaction,
    TransactionType,
    UserQuotaUsage,
)

logger = logging.getLogger(__name__)
User = get_user_model()


class InsufficientFundsError(Exception):
    pass


class QuotaExceededError(Exception):
    pass


class SubscriptionError(Exception):
    pass


class BillingService:
    """
    Centralized service for all billing operations.
    All methods that mutate state use atomic DB transactions.
    """

    # ── Wallet Operations ─────────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def credit_wallet(
        wallet: Wallet,
        amount: int,
        transaction_type: str,
        description: str = "",
        simulation_session=None,
        subscription=None,
        multiplier: Decimal = Decimal("1.00"),
    ) -> WalletTransaction:
        """
        Credit coins to a wallet.
        Applies plan multiplier if provided (e.g. 1.5x for Standard).
        Thread-safe via select_for_update.
        """
        if amount <= 0:
            raise ValueError("Credit amount must be positive.")

        actual_amount = int(amount * multiplier)

        wallet = Wallet.objects.select_for_update().get(pk=wallet.pk)
        wallet.balance += actual_amount
        wallet.lifetime_earned += actual_amount
        wallet.save(update_fields=["balance", "lifetime_earned", "updated_at"])

        txn = WalletTransaction.objects.create(
            wallet=wallet,
            transaction_type=transaction_type,
            amount=actual_amount,
            balance_after=wallet.balance,
            description=description,
            simulation_session=simulation_session,
            subscription=subscription,
        )
        logger.info(
            "CREDIT wallet[%s] +%d coins (type=%s, balance=%d)",
            wallet.user.email, actual_amount, transaction_type, wallet.balance,
        )
        return txn

    @staticmethod
    @transaction.atomic
    def debit_wallet(
        wallet: Wallet,
        amount: int,
        transaction_type: str,
        description: str = "",
        simulation_session=None,
        subscription=None,
    ) -> WalletTransaction:
        """
        Debit coins from a wallet.
        Raises InsufficientFundsError if balance would go negative.
        Thread-safe via select_for_update.
        """
        if amount <= 0:
            raise ValueError("Debit amount must be positive.")

        wallet = Wallet.objects.select_for_update().get(pk=wallet.pk)
        if wallet.balance < amount:
            raise InsufficientFundsError(
                f"Insufficient coins: balance={wallet.balance}, required={amount}."
            )

        wallet.balance -= amount
        wallet.lifetime_spent += amount
        wallet.save(update_fields=["balance", "lifetime_spent", "updated_at"])

        txn = WalletTransaction.objects.create(
            wallet=wallet,
            transaction_type=transaction_type,
            amount=-amount,
            balance_after=wallet.balance,
            description=description,
            simulation_session=simulation_session,
            subscription=subscription,
        )
        logger.info(
            "DEBIT wallet[%s] -%d coins (type=%s, balance=%d)",
            wallet.user.email, amount, transaction_type, wallet.balance,
        )
        return txn

    # ── Subscription Purchase ─────────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def purchase_subscription_with_coins(user: User, plan_tier: str) -> UserSubscription:
        """
        Purchase or upgrade a subscription using wallet coins.
        Steps:
        1. Validate plan exists and is active.
        2. Debit coins atomically.
        3. Deactivate current active subscription.
        4. Create new active subscription.
        5. Update quota tracker to new plan.
        """
        try:
            plan = SubscriptionPlan.objects.get(tier=plan_tier, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            raise SubscriptionError(f"Plan '{plan_tier}' not found or inactive.")

        if plan.price_coins == 0 and plan_tier != "FREE":
            raise SubscriptionError(f"Plan '{plan_tier}' cannot be purchased with coins (price=0).")

        wallet = Wallet.objects.select_for_update().get(user=user)

        # Debit coins
        BillingService.debit_wallet(
            wallet=wallet,
            amount=plan.price_coins,
            transaction_type=TransactionType.SUBSCRIPTION_PURCHASE,
            description=f"Subscription: {plan.name} plan",
        )

        return BillingService._activate_subscription(
            user=user,
            plan=plan,
            payment_method=SubscriptionPaymentMethod.COINS,
            amount_paid_coins=plan.price_coins,
        )

    @staticmethod
    @transaction.atomic
    def purchase_subscription_with_money(
        user: User,
        plan_tier: str,
        payment_reference: str,
        amount_paid_uzs: int,
    ) -> UserSubscription:
        """
        Activate a subscription after real-money payment verification.
        The payment_reference is the transaction ID from the payment gateway.
        """
        try:
            plan = SubscriptionPlan.objects.get(tier=plan_tier, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            raise SubscriptionError(f"Plan '{plan_tier}' not found or inactive.")

        if amount_paid_uzs < plan.price_uzs:
            raise SubscriptionError(
                f"Underpayment: expected {plan.price_uzs} UZS, received {amount_paid_uzs} UZS."
            )

        sub = BillingService._activate_subscription(
            user=user,
            plan=plan,
            payment_method=SubscriptionPaymentMethod.REAL_MONEY,
            amount_paid_uzs=amount_paid_uzs,
            payment_reference=payment_reference,
        )

        # Grant welcome coins on upgrade
        if plan.welcome_coins > 0:
            wallet = Wallet.objects.get(user=user)
            BillingService.credit_wallet(
                wallet=wallet,
                amount=plan.welcome_coins,
                transaction_type=TransactionType.WELCOME_BONUS,
                description=f"Welcome coins for {plan.name} plan activation",
                subscription=sub,
            )

        return sub

    @staticmethod
    def _activate_subscription(
        user: User,
        plan: SubscriptionPlan,
        payment_method: str,
        amount_paid_uzs: int = 0,
        amount_paid_coins: int = 0,
        payment_reference: str = "",
    ) -> UserSubscription:
        """
        Internal helper: deactivates existing sub, creates new one, updates quota.
        Must be called within an atomic block.
        """
        now = timezone.now()

        # Deactivate existing active subscription
        UserSubscription.objects.filter(user=user, is_active=True).update(
            is_active=False,
            cancelled_at=now,
        )

        # Create new subscription
        sub = UserSubscription.objects.create(
            user=user,
            plan=plan,
            is_active=True,
            payment_method=payment_method,
            amount_paid_uzs=amount_paid_uzs,
            amount_paid_coins=amount_paid_coins,
            payment_reference=payment_reference,
            started_at=now,
            expires_at=now + timedelta(days=plan.duration_days),
        )

        # Update quota tracker
        quota, _ = UserQuotaUsage.objects.get_or_create(user=user, defaults={"plan": plan})
        quota.plan = plan
        quota.save(update_fields=["plan", "updated_at"])

        logger.info(
            "Subscription activated: user=%s plan=%s expires=%s",
            user.email, plan.tier, sub.expires_at,
        )
        return sub

    # ── Quota Checks ──────────────────────────────────────────────────────────

    @staticmethod
    def can_start_simulation(user: User) -> Tuple[bool, str]:
        """
        Returns (can_start: bool, reason: str).
        Checks:
        1. Active non-expired subscription.
        2. Monthly simulation quota not exhausted.
        3. Max concurrent sessions not exceeded.
        """
        try:
            sub = UserSubscription.objects.select_related("plan").get(
                user=user, is_active=True
            )
        except UserSubscription.DoesNotExist:
            return False, "No active subscription found."

        if sub.is_expired:
            return False, "Your subscription has expired. Please renew."

        try:
            quota = UserQuotaUsage.objects.select_related("plan").get(user=user)
        except UserQuotaUsage.DoesNotExist:
            return False, "Quota record not found. Please contact support."

        quota.reset_monthly_if_needed()

        if quota.monthly_simulations_used >= quota.plan.monthly_simulations:
            return (
                False,
                f"Monthly simulation limit reached ({quota.plan.monthly_simulations}). "
                f"Upgrade your plan or wait until next month.",
            )

        if quota.active_sessions_count >= quota.plan.max_active_sessions:
            return (
                False,
                f"Maximum concurrent sessions ({quota.plan.max_active_sessions}) reached. "
                f"Complete or abandon an existing session first.",
            )

        return True, "OK"

    @staticmethod
    def can_send_ai_turn(user: User) -> Tuple[bool, str]:
        """
        Returns (can_send: bool, reason: str).
        Checks daily AI turn quota.
        """
        try:
            quota = UserQuotaUsage.objects.select_related("plan").get(user=user)
        except UserQuotaUsage.DoesNotExist:
            return False, "Quota record not found."

        quota.reset_daily_if_needed()

        if quota.daily_ai_turns_used >= quota.plan.daily_ai_turns:
            return (
                False,
                f"Daily AI turn limit ({quota.plan.daily_ai_turns}) reached. Try again tomorrow.",
            )

        return True, "OK"

    # ── Reward After Completion ───────────────────────────────────────────────

    @staticmethod
    @transaction.atomic
    def reward_user_for_completion(user: User, session) -> Optional[WalletTransaction]:
        """
        Awards coins to a student after a successful simulation.
        Anti-farming: checks if the same case was completed within
        COIN_FARMING_COOLDOWN_HOURS. Returns None if cooldown is active.
        """
        from apps.simulation.models import SimulationSession

        cooldown_hours = getattr(settings, "COIN_FARMING_COOLDOWN_HOURS", 24)
        cutoff = timezone.now() - timedelta(hours=cooldown_hours)

        # Farming protection: any other COMPLETED session for same case recently?
        already_rewarded = SimulationSession.objects.filter(
            student=user,
            case=session.case,
            status=SimulationSession.Status.COMPLETED,
            completed_at__gte=cutoff,
        ).exclude(pk=session.pk).exists()

        if already_rewarded:
            logger.warning(
                "Farming protection triggered: user=%s case=%s",
                user.email, session.case_id,
            )
            return None

        # Get plan multiplier
        try:
            quota = UserQuotaUsage.objects.select_related("plan").get(user=user)
            multiplier = quota.plan.coin_multiplier
        except UserQuotaUsage.DoesNotExist:
            multiplier = Decimal("1.00")

        base_reward = session.case.coin_reward
        wallet = Wallet.objects.get(user=user)

        txn = BillingService.credit_wallet(
            wallet=wallet,
            amount=base_reward,
            transaction_type=TransactionType.TASK_REWARD,
            description=f"Completed: {session.case.title}",
            simulation_session=session,
            multiplier=multiplier,
        )

        # Update profile stats
        profile = user.profile
        profile.total_coins_earned += int(base_reward * multiplier)
        profile.total_simulations_completed += 1
        profile.save(update_fields=["total_coins_earned", "total_simulations_completed"])

        return txn

    @staticmethod
    @transaction.atomic
    def award_streak_bonus(user: User, streak_days: int) -> WalletTransaction:
        """
        Awards streak bonus coins. Bonus scales with streak length.
        7-day: 50 coins, 30-day: 200 coins, 100-day: 500 coins.
        """
        STREAK_REWARDS = {7: 50, 14: 75, 30: 200, 60: 350, 100: 500}
        bonus = STREAK_REWARDS.get(streak_days, 0)
        if not bonus:
            return None

        wallet = Wallet.objects.get(user=user)
        return BillingService.credit_wallet(
            wallet=wallet,
            amount=bonus,
            transaction_type=TransactionType.STREAK_BONUS,
            description=f"{streak_days}-day streak bonus!",
        )

    @staticmethod
    @transaction.atomic
    def consume_hint(user: User, session) -> Tuple[bool, str, int]:
        """
        Returns (success, message, coins_spent).
        Uses free monthly hints first; then deducts coins.
        """
        try:
            quota = UserQuotaUsage.objects.select_related("plan").get(user=user)
        except UserQuotaUsage.DoesNotExist:
            return False, "Quota not found.", 0

        quota.reset_monthly_if_needed()

        if quota.monthly_hints_used < quota.plan.free_hints:
            quota.monthly_hints_used += 1
            quota.save(update_fields=["monthly_hints_used"])
            return True, "Free hint used.", 0
        else:
            # Paid hint: 10 coins
            HINT_COST = 10
            wallet = Wallet.objects.get(user=user)
            if wallet.balance < HINT_COST:
                return False, f"Insufficient coins for hint (need {HINT_COST}).", 0
            BillingService.debit_wallet(
                wallet=wallet,
                amount=HINT_COST,
                transaction_type=TransactionType.HINT_PURCHASE,
                description=f"Hint in session {session.id}",
                simulation_session=session,
            )
            return True, f"Hint purchased for {HINT_COST} coins.", HINT_COST
