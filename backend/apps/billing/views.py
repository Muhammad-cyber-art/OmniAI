"""
OmniLab AI - Billing Views
Subscription purchase, wallet info, quota status, hint endpoint.
"""
import logging
from rest_framework import generics, views, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.users.permissions import IsStudent
from .models import (
    SubscriptionPlan,
    UserSubscription,
    Wallet,
    WalletTransaction,
    UserQuotaUsage,
)
from .serializers import (
    SubscriptionPlanSerializer,
    UserSubscriptionSerializer,
    WalletSerializer,
    WalletTransactionSerializer,
    UserQuotaUsageSerializer,
    PurchaseWithCoinsSerializer,
    PurchaseWithMoneySerializer,
    HintRequestSerializer,
)
from .services import BillingService, InsufficientFundsError, SubscriptionError

logger = logging.getLogger(__name__)


class PlanListView(generics.ListAPIView):
    """
    GET /api/v1/billing/plans/
    Public endpoint listing all active subscription plans.
    """
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [IsAuthenticated]
    queryset = SubscriptionPlan.objects.filter(is_active=True).order_by("price_uzs")


class MySubscriptionView(generics.RetrieveAPIView):
    """
    GET /api/v1/billing/my-subscription/
    Returns the authenticated user's active subscription.
    """
    serializer_class = UserSubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return (
            UserSubscription.objects.select_related("plan")
            .filter(user=self.request.user, is_active=True)
            .first()
        )

    def retrieve(self, request, *args, **kwargs):
        obj = self.get_object()
        if not obj:
            return Response(
                {"success": False, "error": {"code": "NOT_FOUND", "message": "No active subscription."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response({"success": True, "data": self.get_serializer(obj).data})


class SubscribeWithCoinsView(views.APIView):
    """
    POST /api/v1/billing/subscribe/coins/
    Body: { "plan_tier": "STANDARD" | "PREMIUM" }
    Purchases a subscription using the student's coin wallet.
    """
    permission_classes = [IsStudent]

    def post(self, request, *args, **kwargs):
        serializer = PurchaseWithCoinsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            sub = BillingService.purchase_subscription_with_coins(
                user=request.user,
                plan_tier=serializer.validated_data["plan_tier"],
            )
        except InsufficientFundsError as e:
            return Response(
                {"success": False, "error": {"code": "INSUFFICIENT_FUNDS", "message": str(e)}},
                status=status.HTTP_402_PAYMENT_REQUIRED,
            )
        except SubscriptionError as e:
            return Response(
                {"success": False, "error": {"code": "SUBSCRIPTION_ERROR", "message": str(e)}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "success": True,
                "message": f"Successfully subscribed to {sub.plan.name} plan!",
                "data": UserSubscriptionSerializer(sub).data,
            },
            status=status.HTTP_201_CREATED,
        )


class SubscribeWithMoneyView(views.APIView):
    """
    POST /api/v1/billing/subscribe/money/
    Body: { "plan_tier": "PREMIUM", "payment_reference": "...", "amount_paid_uzs": 99000 }
    Activates a subscription after confirmed real-money payment.
    """
    permission_classes = [IsStudent]

    def post(self, request, *args, **kwargs):
        serializer = PurchaseWithMoneySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            sub = BillingService.purchase_subscription_with_money(
                user=request.user,
                plan_tier=data["plan_tier"],
                payment_reference=data["payment_reference"],
                amount_paid_uzs=data["amount_paid_uzs"],
            )
        except SubscriptionError as e:
            return Response(
                {"success": False, "error": {"code": "SUBSCRIPTION_ERROR", "message": str(e)}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "success": True,
                "message": f"Payment verified. {sub.plan.name} plan activated!",
                "data": UserSubscriptionSerializer(sub).data,
            },
            status=status.HTTP_201_CREATED,
        )


class WalletView(generics.RetrieveAPIView):
    """
    GET /api/v1/billing/wallet/
    Returns current wallet balance and stats.
    """
    serializer_class = WalletSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        wallet, _ = Wallet.objects.get_or_create(user=self.request.user, defaults={"balance": 0})
        return wallet

    def retrieve(self, request, *args, **kwargs):
        return Response({"success": True, "data": self.get_serializer(self.get_object()).data})


class WalletTransactionListView(generics.ListAPIView):
    """
    GET /api/v1/billing/wallet/transactions/
    Paginated transaction history for the authenticated user.
    """
    serializer_class = WalletTransactionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["transaction_type"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return WalletTransaction.objects.filter(
            wallet__user=self.request.user
        ).select_related("simulation_session__case", "wallet")


class QuotaStatusView(generics.RetrieveAPIView):
    """
    GET /api/v1/billing/quota/
    Returns current quota usage vs plan limits.
    """
    serializer_class = UserQuotaUsageSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        quota = UserQuotaUsage.objects.select_related("plan").filter(user=self.request.user).first()
        if not quota:
            plan, _ = SubscriptionPlan.objects.get_or_create(
                tier="FREE",
                defaults={
                    "name": "Free",
                    "price_uzs": 0,
                    "price_coins": 0,
                    "monthly_simulations": 5,
                    "daily_ai_turns": 10,
                    "free_hints": 3,
                },
            )
            quota = UserQuotaUsage.objects.create(user=self.request.user, plan=plan)
        quota.reset_daily_if_needed()
        quota.reset_monthly_if_needed()
        return quota

    def retrieve(self, request, *args, **kwargs):
        return Response({"success": True, "data": self.get_serializer(self.get_object()).data})


class HintView(views.APIView):
    """
    POST /api/v1/billing/hint/
    Consume a hint for a simulation session.
    Uses free monthly hints first; then deducts coins.
    """
    permission_classes = [IsStudent]

    def post(self, request, *args, **kwargs):
        from apps.simulation.models import SimulationSession

        serializer = HintRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            session = SimulationSession.objects.select_related("case").get(
                id=serializer.validated_data["session_id"],
                student=request.user,
                status=SimulationSession.Status.ACTIVE,
            )
        except SimulationSession.DoesNotExist:
            return Response(
                {"success": False, "error": {"code": "NOT_FOUND", "message": "Active session not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )

        success, message, coins_spent = BillingService.consume_hint(
            user=request.user,
            session=session,
        )

        if not success:
            return Response(
                {"success": False, "error": {"code": "INSUFFICIENT_FUNDS", "message": message}},
                status=status.HTTP_402_PAYMENT_REQUIRED,
            )

        return Response(
            {
                "success": True,
                "message": message,
                "coins_spent": coins_spent,
                "hint": session.case.hint_text or "No hint available for this case.",
            }
        )
