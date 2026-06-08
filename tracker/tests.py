from django.test import TestCase
from django.urls import reverse


class HomeViewTests(TestCase):
    def test_home_page_returns_successful_response(self) -> None:
        response = self.client.get(reverse("tracker:home"))

        self.assertEqual(response.status_code, 200)

    def test_home_page_uses_correct_template(self) -> None:
        response = self.client.get(reverse("tracker:home"))

        self.assertTemplateUsed(response, "tracker/home.html")

    def test_home_page_contains_project_name(self) -> None:
        response = self.client.get(reverse("tracker:home"))

        self.assertContains(response, "Personal Expense Tracker")
