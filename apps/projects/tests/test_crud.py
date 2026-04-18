from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.projects.models import Category, Project, Tag

User = get_user_model()


class ProjectCRUDTests(TestCase):
    """Full CRUD + permission tests for ProjectViewSet."""

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

        start_time = timezone.now() + timedelta(days=1)
        end_time = start_time + timedelta(days=30)
        self.project_data = {
            "title": "Test Project",
            "details": "A detailed description of the project.",
            "category": self.category.pk,
            "total_target": "10000.00",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "tag_names": ["python", "django"],
        }

    # ── LIST ─────────────────────────────────

    def test_list_projects_anonymous(self):
        """Anyone can list projects."""
        response = self.client.get("/api/projects/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_projects_paginated_shape(self):
        """List endpoint returns DRF page metadata and supports page/page_size."""
        self.client.force_authenticate(self.owner)

        for idx in range(3):
            data = {
                **self.project_data,
                "title": f"Project {idx}",
            }
            self.client.post("/api/projects/", data, format="json")

        self.client.logout()
        response = self.client.get("/api/projects/?page=1&page_size=2")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("count", response.data)
        self.assertIn("next", response.data)
        self.assertIn("previous", response.data)
        self.assertIn("results", response.data)
        self.assertEqual(response.data["count"], 3)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertIsNotNone(response.data["next"])
        self.assertIsNone(response.data["previous"])
        self.assertIn("page=2", response.data["next"])
        self.assertIn("page_size=2", response.data["next"])

    def test_list_projects_second_page_has_previous(self):
        """Second page includes previous link and expected number of results."""
        self.client.force_authenticate(self.owner)

        for idx in range(3):
            data = {
                **self.project_data,
                "title": f"Paged Project {idx}",
            }
            self.client.post("/api/projects/", data, format="json")

        self.client.logout()
        response = self.client.get("/api/projects/?page=2&page_size=2")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 3)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertIsNone(response.data["next"])
        self.assertIsNotNone(response.data["previous"])
        self.assertIn("page=1", response.data["previous"])
        self.assertIn("page_size=2", response.data["previous"])

    # ── CREATE ───────────────────────────────

    def test_create_project_authenticated(self):
        """Authenticated user can create a project."""
        self.client.force_authenticate(self.owner)
        response = self.client.post(
            "/api/projects/", self.project_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "Test Project")
        self.assertEqual(Tag.objects.filter(name="python").count(), 1)
        self.assertEqual(Tag.objects.filter(name="django").count(), 1)

    def test_create_project_anonymous_forbidden(self):
        """Anonymous users cannot create projects."""
        response = self.client.post(
            "/api/projects/", self.project_data, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_project_invalid_dates(self):
        """End date before start date fails."""
        self.client.force_authenticate(self.owner)
        start_time = timezone.now() + timedelta(days=1)
        data = {
            **self.project_data,
            "start_time": start_time.isoformat(),
            "end_time": (start_time - timedelta(days=1)).isoformat(),
        }
        response = self.client.post("/api/projects/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        errors = response.data.get("errors", response.data)
        self.assertIn("end_time", errors)

    def test_create_project_negative_target(self):
        """Negative target is rejected."""
        self.client.force_authenticate(self.owner)
        data = {**self.project_data, "total_target": "-500.00"}
        response = self.client.post("/api/projects/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ── RETRIEVE ─────────────────────────────

    def test_retrieve_project(self):
        """Anyone can retrieve a single project."""
        self.client.force_authenticate(self.owner)
        self.client.post(
            "/api/projects/", self.project_data, format="json"
        )
        project_id = Project.objects.latest('id').id
        self.client.logout()

        response = self.client.get(f"/api/projects/{project_id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], project_id)

    # ── UPDATE ───────────────────────────────

    def test_update_own_project(self):
        """Owner can update their project."""
        self.client.force_authenticate(self.owner)
        self.client.post(
            "/api/projects/", self.project_data, format="json"
        )
        project_id = Project.objects.latest('id').id

        response = self.client.patch(
            f"/api/projects/{project_id}/",
            {"title": "Updated Title"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Updated Title")

    def test_update_other_users_project_forbidden(self):
        """Non-owner cannot update someone else's project."""
        self.client.force_authenticate(self.owner)
        self.client.post(
            "/api/projects/", self.project_data, format="json"
        )
        project_id = Project.objects.latest('id').id

        self.client.force_authenticate(self.other_user)
        response = self.client.patch(
            f"/api/projects/{project_id}/",
            {"title": "Hacked Title"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ── DELETE ───────────────────────────────

    def test_delete_own_project(self):
        """Owner can delete their project."""
        self.client.force_authenticate(self.owner)
        self.client.post(
            "/api/projects/", self.project_data, format="json"
        )
        project_id = Project.objects.latest('id').id

        response = self.client.delete(f"/api/projects/{project_id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Project.objects.filter(pk=project_id).exists())

    def test_delete_other_users_project_forbidden(self):
        """Non-owner cannot delete someone else's project."""
        self.client.force_authenticate(self.owner)
        self.client.post(
            "/api/projects/", self.project_data, format="json"
        )
        project_id = Project.objects.latest('id').id

        self.client.force_authenticate(self.other_user)
        response = self.client.delete(f"/api/projects/{project_id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # ── FILTER: creator=me ───────────────────

    def test_filter_creator_me(self):
        """?creator=me returns only the authenticated user's projects."""
        self.client.force_authenticate(self.owner)
        self.client.post("/api/projects/", self.project_data, format="json")

        self.client.force_authenticate(self.other_user)
        other_data = {
            **self.project_data,
            "title": "Other Project",
        }
        self.client.post("/api/projects/", other_data, format="json")

        # Owner sees only their project
        self.client.force_authenticate(self.owner)
        response = self.client.get("/api/projects/?creator=me")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["title"], "Test Project")

    # ── FILTER: category ─────────────────────

    def test_filter_by_category(self):
        """?category=<id> filters by category id."""
        self.client.force_authenticate(self.owner)
        self.client.post("/api/projects/", self.project_data, format="json")

        response = self.client.get(f"/api/projects/?category={self.category.pk}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    # ── TAGS GET-OR-CREATE ───────────────────

    def test_tags_get_or_create(self):
        """Creating a project with existing tag names reuses them."""
        Tag.objects.create(name="python")

        self.client.force_authenticate(self.owner)
        self.client.post("/api/projects/", self.project_data, format="json")

        self.assertEqual(Tag.objects.filter(name="python").count(), 1)