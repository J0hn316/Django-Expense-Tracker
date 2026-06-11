from django.contrib.auth.models import User
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


class RegisterViewTests(TestCase):
    def test_register_page_returns_successful_response(self) -> None:
        response = self.client.get(reverse("tracker:register"))

        self.assertEqual(response.status_code, 200)

    def test_register_page_uses_correct_template(self) -> None:
        response = self.client.get(reverse("tracker:register"))

        self.assertTemplateUsed(response, "registration/register.html")

    def test_user_can_register_successfully(self) -> None:
        response = self.client.post(
            reverse("tracker:register"),
            {
                "username": "johnny",
                "email": "johnny@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        self.assertRedirects(response, reverse("tracker:dashboard"))
        self.assertTrue(User.objects.filter(username="johnny").exists())

    def test_registered_user_is_logged_in_automatically(self) -> None:
        self.client.post(
            reverse("tracker:register"),
            {
                "username": "johnny",
                "email": "johnny@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        response = self.client.get(reverse("tracker:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Welcome, johnny.")


class DashboardViewTests(TestCase):
    def test_logged_out_user_is_redirected_from_dashboard(self) -> None:
        response = self.client.get(reverse("tracker:dashboard"))

        expected_url = f"{reverse('login')}?next={reverse('tracker:dashboard')}"
        self.assertRedirects(response, expected_url)

    def test_logged_in_user_can_view_dashboard(self) -> None:
        user = User.objects.create_user(
            username="johnny",
            password="StrongPass123!",
        )

        self.client.login(username="johnny", password="StrongPass123!")

        response = self.client.get(reverse("tracker:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"Welcome, {user.username}.")


class LoginViewTests(TestCase):
    def test_login_page_returns_successful_response(self) -> None:
        response = self.client.get(reverse("login"))

        self.assertEqual(response.status_code, 200)

    def test_login_page_uses_correct_template(self) -> None:
        response = self.client.get(reverse("login"))

        self.assertTemplateUsed(response, "registration/login.html")

    def test_user_can_log_in_successfully(self) -> None:
        User.objects.create_user(
            username="johnny",
            password="StrongPass123!",
        )

        response = self.client.post(
            reverse("login"),
            {
                "username": "johnny",
                "password": "StrongPass123!",
            },
        )

        self.assertRedirects(response, reverse("tracker:dashboard"))
