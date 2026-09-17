"""
OmniLab AI - Billing App Models
SubscriptionPlan, UserSubscription, Wallet, WalletTransaction, UserQuotaUsage
"""
import uuid
from decimal import Decimal
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db.models import CheckConstraint, UniqueConstraint, Q, F

User = get_user_model()


# ─── SUBSCRIPTION PLAN ────────────────────────────────────────────────────────

class PlanTier(models.TextChoices):
    FREE = "FREE", _("Free")
    STANDARD = "STANDARD", _("Standard")
    PREMIUM = "PREMIUM", _("Premium")


class SubscriptionPlan(models.Model):
    """
    Immutable plan definitions. Admin creates/modifies these.
    Never delete a plan that has active subscriptions — mark inactive instead.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tier = models.CharField(
        max_length=20,
        choices=PlanTier.choices,
        unique=True,
        db_index=True,
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, help_text=_("Set False to hide from purchase options."))

    # Pricing
    price_uzs = models.PositiveBigIntegerField(
        default=0,
        help_text=_("Price in Uzbek Soʻm. 0 = free."),
    )
    price_coins = models.PositiveBigIntegerField(
        default=0,
        help_text=_("Equivalent coin price if paying with coins."),
    )

    # Entitlements
    welcome_coins = models.PositiveIntegerField(
        default=0,
        help_text=_("One-time coins awarded on activation."),
    )
    coin_multiplier = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=Decimal("1.00"),
        validators=[MinValueValidator(Decimal("1.00")), MaxValueValidator(Decimal("5.00"))],
        help_text=_("Multiplier applied to earned coins (e.g. 1.5 = 50% bonus)."),
    )
    monthly_simulations = models.PositiveIntegerField(
        default=5,
        help_text=_("Max full simulation cases per month."),
    )
    daily_ai_turns = models.PositiveIntegerField(
        default=10,
        help_text=_("Max AI dialogue turns per day."),
    )
    free_hints = models.PositiveIntegerField(
        default=3,
        help_text=_("Free hints per month before coin deduction."),
    )
    allowed_retries = models.PositiveIntegerField(
        default=1,
        help_text=_("Free retries per simulation case before coin purchase."),
    )
    max_active_sessions = models.PositiveIntegerField(
        default=1,
        help_text=_("Maximum concurrent open simulation sessions."),
    )

    duration_days = models.PositiveIntegerField(
        default=30,
        help_text=_("Subscription validity in days after activation."),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "billing_subscription_plan"
        verbose_name = _("Subscription Plan")
        verbose_name_plural = _("Subscription Plans")
        ordering = ["price_uzs"]

    def __str__(self) -> str:
        return f"{self.name} ({self.tier})"


# ─── USER SUBSCRIPTION ────────────────────────────────────────────────────────

class SubscriptionPaymentMethod(models.TextChoices):
    REAL_MONEY = "REAL_MONEY", _("Real Money (So'm)")
    COINS = "COINS", _("Coins")
    PROMO = "PROMO", _("Promotional")


class UserSubscription(models.Model):
    """
    Tracks a user's current and historical subscriptions.
    Only one subscription per user can be is_active=True at a time.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="subscriptions",
        db_index=True,
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name="subscriptions",
    )
    is_active = models.BooleanField(default=False, db_index=True)
    payment_method = models.CharField(
        max_length=20,
        choices=SubscriptionPaymentMethod.choices,
        default=SubscriptionPaymentMethod.PROMO,
    )
    amount_paid_uzs = models.PositiveBigIntegerField(default=0)
    amount_paid_coins = models.PositiveBigIntegerField(default=0)

    started_at = models.DateTimeField()
    expires_at = models.DateTimeField(db_index=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    # External payment reference (for real money transactions)
    payment_reference = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "billing_user_subscription"
        verbose_name = _("User Subscription")
        verbose_name_plural = _("User Subscriptions")
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["user", "is_active"], name="idx_sub_user_active"),
            models.Index(fields=["expires_at", "is_active"], name="idx_sub_expiry"),
        ]
        constraints = [
            # Only one active subscription per user
            UniqueConstraint(
                fields=["user"],
                condition=Q(is_active=True),
                name="unique_active_subscription_per_user",
            ),
        ]

    def __str__(self) -> str:
        status = "ACTIVE" if self.is_active else "EXPIRED"
        return f"{self.user.email} → {self.plan.name} [{status}]"

    @property
    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at


# ─── WALLET ───────────────────────────────────────────────────────────────────

class Wallet(models.Model):
    """
    One wallet per user. Balance is the canonical source of truth.
    Never mutate balance directly — always use WalletTransaction records
    and the BillingService.credit/debit methods.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="wallet",
        primary_key=True,
    )
    balance = models.PositiveBigIntegerField(
        default=0,
        help_text=_("Current coin balance. Must never go negative."),
    )
    lifetime_earned = models.PositiveBigIntegerField(
        default=0,
        help_text=_("Total coins ever credited (historical audit)."),
    )
    lifetime_spent = models.PositiveBigIntegerField(
        default=0,
        help_text=_("Total coins ever debited (historical audit)."),
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "billing_wallet"
        verbose_name = _("Wallet")
        verbose_name_plural = _("Wallets")
        constraints = [
            CheckConstraint(
                condition=Q(balance__gte=0),
                name="wallet_balance_non_negative",
            ),
        ]

    def __str__(self) -> str:
        return f"Wallet({self.user.email}) = {self.balance:,} coins"


# ─── WALLET TRANSACTION ───────────────────────────────────────────────────────

class TransactionType(models.TextChoices):
    # Credits
    WELCOME_BONUS = "WELCOME_BONUS", _("Welcome Bonus")
    TASK_REWARD = "TASK_REWARD", _("Task/Simulation Reward")
    STREAK_BONUS = "STREAK_BONUS", _("Daily Streak Bonus")
    REFERRAL_BONUS = "REFERRAL_BONUS", _("Referral Bonus")
    ADMIN_CREDIT = "ADMIN_CREDIT", _("Admin Credit")
    REFUND = "REFUND", _("Refund")
    # Debits
    SUBSCRIPTION_PURCHASE = "SUBSCRIPTION_PURCHASE", _("Subscription Purchase")
    HINT_PURCHASE = "HINT_PURCHASE", _("Hint Purchase")
    RETRY_PURCHASE = "RETRY_PURCHASE", _("Retry Purchase")
    ADMIN_DEBIT = "ADMIN_DEBIT", _("Admin Debit")


class WalletTransaction(models.Model):
    """
    Immutable ledger of every coin movement.
    Positive amount = credit, negative amount = debit.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name="transactions",
        db_index=True,
    )
    transaction_type = models.CharField(
        max_length=30,
        choices=TransactionType.choices,
        db_index=True,
    )
    amount = models.BigIntegerField(
        help_text=_("Positive = credit, negative = debit."),
    )
    balance_after = models.PositiveBigIntegerField(
        help_text=_("Wallet balance after this transaction."),
    )
    description = models.CharField(max_length=512, blank=True)

    # Optional FK references for traceability
    simulation_session = models.ForeignKey(
        "simulation.SimulationSession",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="wallet_transactions",
    )
    subscription = models.ForeignKey(
        UserSubscription,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="wallet_transactions",
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "billing_wallet_transaction"
        verbose_name = _("Wallet Transaction")
        verbose_name_plural = _("Wallet Transactions")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["wallet", "-created_at"], name="idx_txn_wallet_time"),
            models.Index(fields=["transaction_type", "-created_at"], name="idx_txn_type_time"),
        ]
        constraints = [
            CheckConstraint(
                condition=~Q(amount=0),
                name="wallet_txn_nonzero_amount",
            ),
        ]

    def __str__(self) -> str:
        sign = "+" if self.amount > 0 else ""
        return f"[{self.transaction_type}] {sign}{self.amount} → {self.wallet.user.email}"


# ─── USER QUOTA USAGE ─────────────────────────────────────────────────────────

class UserQuotaUsage(models.Model):
    """
    Tracks per-user quota consumption against their current plan limits.
    Resets are handled by a management command or Celery beat task.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="quota_usage",
        primary_key=True,
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name="quota_usages",
    )

    # Monthly counters (reset on the 1st of each month)
    monthly_simulations_used = models.PositiveIntegerField(default=0)
    monthly_hints_used = models.PositiveIntegerField(default=0)
    monthly_reset_date = models.DateField(
        default=timezone.now,
        help_text=_("Date when monthly counters were last reset."),
    )

    # Daily counters (reset every day)
    daily_ai_turns_used = models.PositiveIntegerField(default=0)
    daily_reset_date = models.DateField(
        default=timezone.now,
        help_text=_("Date when daily counters were last reset."),
    )

    # Session tracking
    active_sessions_count = models.PositiveIntegerField(
        default=0,
        help_text=_("Number of currently open simulation sessions."),
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "billing_user_quota_usage"
        verbose_name = _("User Quota Usage")
        verbose_name_plural = _("User Quota Usages")
        constraints = [
            CheckConstraint(
                condition=Q(monthly_simulations_used__gte=0),
                name="quota_monthly_sims_gte_zero",
            ),
            CheckConstraint(
                condition=Q(daily_ai_turns_used__gte=0),
                name="quota_daily_turns_gte_zero",
            ),
            CheckConstraint(
                condition=Q(active_sessions_count__gte=0),
                name="quota_active_sessions_gte_zero",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"Quota({self.user.email}): "
            f"sims {self.monthly_simulations_used}/{self.plan.monthly_simulations}, "
            f"turns {self.daily_ai_turns_used}/{self.plan.daily_ai_turns}"
        )

    def reset_daily_if_needed(self):
        """Call before checking daily quotas. Resets counters if date has changed."""
        today = timezone.now().date()
        if self.daily_reset_date < today:
            self.daily_ai_turns_used = 0
            self.daily_reset_date = today
            self.save(update_fields=["daily_ai_turns_used", "daily_reset_date"])

    def reset_monthly_if_needed(self):
        """Call before checking monthly quotas. Resets counters if month has changed."""
        today = timezone.now().date()
        if (
            self.monthly_reset_date.year < today.year
            or self.monthly_reset_date.month < today.month
        ):
            self.monthly_simulations_used = 0
            self.monthly_hints_used = 0
            self.monthly_reset_date = today
            self.save(update_fields=["monthly_simulations_used", "monthly_hints_used", "monthly_reset_date"])
