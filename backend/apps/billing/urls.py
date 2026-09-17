"""OmniLab AI - Billing URL Configuration"""
from django.urls import path

from .views import (
    PlanListView,
    MySubscriptionView,
    SubscribeWithCoinsView,
    SubscribeWithMoneyView,
    WalletView,
    WalletTransactionListView,
    QuotaStatusView,
    HintView,
)

app_name = "billing"

urlpatterns = [
    path("plans/", PlanListView.as_view(), name="plan_list"),
    path("my-subscription/", MySubscriptionView.as_view(), name="my_subscription"),
    path("subscribe/coins/", SubscribeWithCoinsView.as_view(), name="subscribe_coins"),
    path("subscribe/money/", SubscribeWithMoneyView.as_view(), name="subscribe_money"),
    path("wallet/", WalletView.as_view(), name="wallet"),
    path("wallet/transactions/", WalletTransactionListView.as_view(), name="wallet_transactions"),
    path("quota/", QuotaStatusView.as_view(), name="quota_status"),
    path("hint/", HintView.as_view(), name="hint"),
]
