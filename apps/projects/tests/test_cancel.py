from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.projects.models import Category, Project

User = get_user_model()


class CancelProjectTests(TestCase):
    """
    CORRECTED cancel rule:
      current_amount <  25% of total_target → ALLOWED
      current_amount == 25% of total_target → BLOCKED
      current_amount >  25% of total_target → BLOCKED
    """

    def setUp(self):
        self.client = APIClient()

        self.owner = User.objects.create_user(
            username="owner",
            email="owner@test.com",
            password="TestPass123!",
            first_name="Owner",
            last_name="User",
            phone_number="01012345678",
            is_active=True,
        )
        self.other_user = User.objects.create_user(
            username="other",
            email="other@test.com",
            password="TestPass123!",
            first_name="Other",
            last_name="User",
            phone_number="01112345678",
            is_active=True,
        )

        self.category = Category.objects.create(name="Technology")

    def _create_project(self, total_target=10000, current_donations=0):
        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(days=30)
        return Project.objects.create(
            title="Test Project",
            details="Details here.",
            total_target=Decimal(str(total_target)),
            current_donations=Decimal(str(current_donations)),
            current_amount=Decimal(str(current_donations)),
            start_time=start_time,
            end_time=end_time,
            owner=self.owner,
            category=self.category,
        )

    # ── BOUNDARY TESTS ───────────────────────

    def test_cancel_at_0_percent_allowed(self):
        """0% funded → cancel ALLOWED."""
        project = self._create_project(total_target=10000, current_donations=0)
        self.client.force_authenticate(self.owner)

        response = self.client.post(f"/api/projects/{project.pk}/cancel/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        project.refresh_from_db()
        self.assertTrue(project.is_cancelled)

    def test_cancel_at_24_percent_allowed(self):
        """24% funded (2400 / 10000) → cancel ALLOWED."""
        project = self._create_project(total_target=10000, current_donations=2400)
        self.client.force_authenticate(self.owner)

        response = self.client.post(f"/api/projects/{project.pk}/cancel/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        project.refresh_from_db()
        self.assertTrue(project.is_cancelled)

    def test_cancel_at_exactly_25_percent_blocked(self):
        """
        CRITICAL BOUNDARY: 25% funded (2500 / 10000) → cancel BLOCKED.
        This is the corrected rule from v3.0.
        """
        project = self._create_project(total_target=10000, current_donations=2500)
        self.client.force_authenticate(self.owner)

        response = self.client.post(f"/api/projects/{project.pk}/cancel/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        project.refresh_from_db()
        self.assertFalse(project.is_cancelled)

    def test_cancel_at_26_percent_blocked(self):
        """26% funded (2600 / 10000) → cancel BLOCKED."""
        project = self._create_project(total_target=10000, current_donations=2600)
        self.client.force_authenticate(self.owner)

        response = self.client.post(f"/api/projects/{project.pk}/cancel/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        project.refresh_from_db()
        self.assertFalse(project.is_cancelled)

    def test_cancel_at_100_percent_blocked(self):
        """Fully funded → cancel BLOCKED."""
        project = self._create_project(total_target=10000, current_donations=10000)
        self.client.force_authenticate(self.owner)

        response = self.client.post(f"/api/projects/{project.pk}/cancel/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        project.refresh_from_db()
        self.assertFalse(project.is_cancelled)

    # ── EDGE: just below 25% ────────────────

    def test_cancel_at_24_99_percent_allowed(self):
        """24.99% funded (2499 / 10000) → cancel ALLOWED."""
        project = self._create_project(total_target=10000, current_donations=2499)
        self.client.force_authenticate(self.owner)

        response = self.client.post(f"/api/projects/{project.pk}/cancel/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        project.refresh_from_db()
        self.assertTrue(project.is_cancelled)

    # ── PERMISSION TESTS ─────────────────────

    def test_cancel_by_non_owner_forbidden(self):
        """Non-owner cannot cancel the project."""
        project = self._create_project(total_target=10000, current_donations=0)
        self.client.force_authenticate(self.other_user)

        response = self.client.post(f"/api/projects/{project.pk}/cancel/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        project.refresh_from_db()
        self.assertFalse(project.is_cancelled)

    def test_cancel_by_anonymous_unauthorized(self):
        """Anonymous user cannot cancel."""
        project = self._create_project(total_target=10000, current_donations=0)

        response = self.client.post(f"/api/projects/{project.pk}/cancel/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cancel_already_cancelled_fails(self):
        """Already cancelled project cannot be cancelled again."""
        project = self._create_project(total_target=10000, current_donations=0)
        project.is_cancelled = True
        project.save()

        self.client.force_authenticate(self.owner)
        response = self.client.post(f"/api/projects/{project.pk}/cancel/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ── DECIMAL EDGE CASE ────────────────────

    def test_cancel_small_amounts_decimal_precision(self):
        """With total_target=100, current_amount=24.99 → allowed."""
        project = self._create_project(
            total_target=100, current_donations=Decimal("24.99")
        )
        self.client.force_authenticate(self.owner)

        response = self.client.post(f"/api/projects/{project.pk}/cancel/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cancel_small_amounts_exactly_25_blocked(self):
        """With total_target=100, current_amount=25.00 → BLOCKED."""
        project = self._create_project(
            total_target=100, current_donations=Decimal("25.00")
        )
        self.client.force_authenticate(self.owner)

        response = self.client.post(f"/api/projects/{project.pk}/cancel/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)