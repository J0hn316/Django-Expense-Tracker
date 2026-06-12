from django.urls import reverse
from django.test import TestCase
from django.db import IntegrityError
from django.contrib.auth.models import User

from .models import Category


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


class CategoryModelTests(TestCase):
    def test_category_can_be_created(self) -> None:
        user = User.objects.create_user(
            username="johnny",
            password="StrongPass123!",
        )

        category = Category.objects.create(
            user=user,
            name="Food",
            category_type=Category.CategoryType.EXPENSE,
        )

        self.assertEqual(category.user, user)
        self.assertEqual(category.name, "Food")
        self.assertEqual(category.category_type, Category.CategoryType.EXPENSE)

    def test_category_string_representation(self) -> None:
        user = User.objects.create_user(
            username="johnny",
            password="StrongPass123!",
        )

        category = Category.objects.create(
            user=user,
            name="Food",
            category_type=Category.CategoryType.EXPENSE,
        )

        self.assertEqual(str(category), "Food (Expense)")

    def test_user_can_have_income_and_expense_category_with_same_name(self) -> None:
        user = User.objects.create_user(
            username="johnny",
            password="StrongPass123!",
        )

        Category.objects.create(
            user=user,
            name="Bonus",
            category_type=Category.CategoryType.INCOME,
        )

        Category.objects.create(
            user=user,
            name="Bonus",
            category_type=Category.CategoryType.EXPENSE,
        )

        self.assertEqual(Category.objects.filter(user=user, name="Bonus").count(), 2)

    def test_duplicate_category_name_and_type_for_same_user_is_not_allowed(
        self,
    ) -> None:
        user = User.objects.create_user(
            username="johnny",
            password="StrongPass123!",
        )

        Category.objects.create(
            user=user,
            name="Food",
            category_type=Category.CategoryType.EXPENSE,
        )

        with self.assertRaises(IntegrityError):
            Category.objects.create(
                user=user,
                name="Food",
                category_type=Category.CategoryType.EXPENSE,
            )

    def test_different_users_can_have_same_category_name_and_type(self) -> None:
        john = User.objects.create_user(
            username="johnny",
            password="StrongPass123!",
        )
        jane = User.objects.create_user(
            username="jane",
            password="StrongPass123!",
        )

        Category.objects.create(
            user=john,
            name="Food",
            category_type=Category.CategoryType.EXPENSE,
        )

        Category.objects.create(
            user=jane,
            name="Food",
            category_type=Category.CategoryType.EXPENSE,
        )

        self.assertEqual(Category.objects.filter(name="Food").count(), 2)
