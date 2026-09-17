"""
OmniLab AI - Billing App Tests
Verifies plans, subscription lifecycle, wallet transactions,
and quota tracking.
"""
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.billing.models import SubscriptionPlan, Wallet
from apps.billing.services import BillingService

User = get_user_model()


class BillingTests(APITestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            email="student_billing@omnilab.uz",
            username="student_billing",
            password="StrongPassword123!",
            role="STUDENT",
        )
        # Ensure plans exist
        self.free_plan = SubscriptionPlan.objects.get(tier="FREE")
        self.standard_plan, _ = SubscriptionPlan.objects.get_or_create(
            tier="STANDARD",
            defaults={
                "name": "Standard",
                "price_uzs": 49000,
                "price_coins": 100,
                "monthly_simulations": 30,
                "daily_ai_turns": 50,
                "free_hints": 10,
                "duration_days": 30,
            },
        )

    def test_plan_list(self):
        """GET /api/v1/billing/plans/ lists all active plans."""
        self.client.force_authenticate(user=self.student)
        url = reverse("billing:plan_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 2)

    def test_my_subscription(self):
        """GET /api/v1/billing/my-subscription/ returns student's active plan."""
        self.client.force_authenticate(user=self.student)
        url = reverse("billing:my_subscription")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["plan"]["tier"], "FREE")

    def test_wallet_view(self):
        """GET /api/v1/billing/wallet/ returns student's wallet balance."""
        self.client.force_authenticate(user=self.student)
        url = reverse("billing:wallet")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["balance"], 50)  # Free welcome coins

    def test_quota_status_view(self):
        """GET /api/v1/billing/quota/ returns quota usage against plan limits."""
        self.client.force_authenticate(user=self.student)
        url = reverse("billing:quota_status")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["plan_tier"], "FREE")
        self.assertEqual(response.data["data"]["monthly_simulations_limit"], 5)

    def test_subscribe_with_insufficient_coins(self):
        """Buying standard plan with insufficient coins returns 402."""
        self.client.force_authenticate(user=self.student)
        url = reverse("billing:subscribe_coins")
        payload = {"plan_tier": "STANDARD"}
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_402_PAYMENT_REQUIRED)
        self.assertEqual(response.data["error"]["code"], "INSUFFICIENT_FUNDS")

    def test_subscribe_with_enough_coins(self):
        """Adding coins and purchasing standard plan succeeds."""
        wallet = Wallet.objects.get(user=self.student)
        BillingService.credit_wallet(wallet, 200, "REWARD", "Testing reward")

        self.client.force_authenticate(user=self.student)
        url = reverse("billing:subscribe_coins")
        payload = {"plan_tier": "STANDARD"}
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["plan"]["tier"], "STANDARD")
