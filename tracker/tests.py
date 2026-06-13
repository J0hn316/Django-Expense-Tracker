from datetime import date
from decimal import Decimal

from django.urls import reverse
from django.test import TestCase
from django.db import IntegrityError
from django.db.models import RestrictedError
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import Category, Transaction


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


class TransactionModelTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="johnny",
            password="StrongPass123!",
        )
        self.other_user = User.objects.create_user(
            username="jane",
            password="StrongPass123!",
        )

        self.expense_category = Category.objects.create(
            user=self.user,
            name="Food",
            category_type=Category.CategoryType.EXPENSE,
        )
        self.income_category = Category.objects.create(
            user=self.user,
            name="Paycheck",
            category_type=Category.CategoryType.INCOME,
        )
        self.other_user_expense_category = Category.objects.create(
            user=self.other_user,
            name="Food",
            category_type=Category.CategoryType.EXPENSE,
        )

    def test_expense_transaction_can_be_created(self) -> None:
        transaction = Transaction.objects.create(
            user=self.user,
            category=self.expense_category,
            transaction_type=Transaction.TransactionType.EXPENSE,
            amount=Decimal("84.32"),
            description="Groceries",
            transaction_date=date(2026, 6, 11),
        )

        self.assertEqual(transaction.user, self.user)
        self.assertEqual(transaction.category, self.expense_category)
        self.assertEqual(
            transaction.transaction_type, Transaction.TransactionType.EXPENSE
        )
        self.assertEqual(transaction.amount, Decimal("84.32"))
        self.assertEqual(transaction.description, "Groceries")

    def test_income_transaction_can_be_created(self) -> None:
        transaction = Transaction.objects.create(
            user=self.user,
            category=self.income_category,
            transaction_type=Transaction.TransactionType.INCOME,
            amount=Decimal("2000.00"),
            description="Biweekly paycheck",
            transaction_date=date(2026, 6, 11),
        )

        self.assertEqual(
            transaction.transaction_type, Transaction.TransactionType.INCOME
        )
        self.assertEqual(transaction.amount, Decimal("2000.00"))

    def test_transaction_string_representation(self) -> None:
        transaction = Transaction.objects.create(
            user=self.user,
            category=self.expense_category,
            transaction_type=Transaction.TransactionType.EXPENSE,
            amount=Decimal("84.32"),
            description="Groceries",
            transaction_date=date(2026, 6, 11),
        )

        self.assertEqual(str(transaction), "Groceries - 84.32")

    def test_transaction_amount_must_be_positive(self) -> None:
        transaction = Transaction(
            user=self.user,
            category=self.expense_category,
            transaction_type=Transaction.TransactionType.EXPENSE,
            amount=Decimal("0.00"),
            description="Invalid groceries",
            transaction_date=date(2026, 6, 11),
        )

        with self.assertRaises(ValidationError):
            transaction.full_clean()

    def test_transaction_category_must_belong_to_same_user(self) -> None:
        transaction = Transaction(
            user=self.user,
            category=self.other_user_expense_category,
            transaction_type=Transaction.TransactionType.EXPENSE,
            amount=Decimal("84.32"),
            description="Groceries",
            transaction_date=date(2026, 6, 11),
        )

        with self.assertRaises(ValidationError):
            transaction.full_clean()

    def test_transaction_type_must_match_category_type(self) -> None:
        transaction = Transaction(
            user=self.user,
            category=self.income_category,
            transaction_type=Transaction.TransactionType.EXPENSE,
            amount=Decimal("84.32"),
            description="Groceries",
            transaction_date=date(2026, 6, 11),
        )

        with self.assertRaises(ValidationError):
            transaction.full_clean()

    def test_category_with_transactions_cannot_be_deleted(self) -> None:
        Transaction.objects.create(
            user=self.user,
            category=self.expense_category,
            transaction_type=Transaction.TransactionType.EXPENSE,
            amount=Decimal("84.32"),
            description="Groceries",
            transaction_date=date(2026, 6, 11),
        )

        with self.assertRaises(RestrictedError):
            self.expense_category.delete()

    def test_user_deletion_deletes_user_transactions(self) -> None:
        Transaction.objects.create(
            user=self.user,
            category=self.expense_category,
            transaction_type=Transaction.TransactionType.EXPENSE,
            amount=Decimal("84.32"),
            description="Groceries",
            transaction_date=date(2026, 6, 11),
        )

        self.user.delete()

        self.assertFalse(Transaction.objects.filter(description="Groceries").exists())

    def test_transactions_are_ordered_by_newest_date_first(self) -> None:
        older_transaction = Transaction.objects.create(
            user=self.user,
            category=self.expense_category,
            transaction_type=Transaction.TransactionType.EXPENSE,
            amount=Decimal("25.00"),
            description="Older transaction",
            transaction_date=date(2026, 5, 1),
        )
        newer_transaction = Transaction.objects.create(
            user=self.user,
            category=self.expense_category,
            transaction_type=Transaction.TransactionType.EXPENSE,
            amount=Decimal("40.00"),
            description="Newer transaction",
            transaction_date=date(2026, 6, 1),
        )

        transactions = list(Transaction.objects.all())

        self.assertEqual(transactions[0], newer_transaction)
        self.assertEqual(transactions[1], older_transaction)
