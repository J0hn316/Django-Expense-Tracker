from decimal import Decimal
from django.utils import timezone
from datetime import date, timedelta

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

    def test_home_page_contains_hero_heading(self) -> None:
        response = self.client.get(reverse("tracker:home"))

        self.assertContains(response, "Take control of your finances")


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
        self.assertContains(response, "Welcome back, johnny.")


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
        self.assertContains(response, f"Welcome back, {user.username}.")


class DashboardAggregationTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="johnny",
            password="StrongPass123!",
        )
        self.other_user = User.objects.create_user(
            username="jane",
            password="StrongPass123!",
        )

        self.food_category = Category.objects.create(
            user=self.user,
            name="Food",
            category_type=Category.CategoryType.EXPENSE,
        )
        self.housing_category = Category.objects.create(
            user=self.user,
            name="Housing",
            category_type=Category.CategoryType.EXPENSE,
        )
        self.income_category = Category.objects.create(
            user=self.user,
            name="Paycheck",
            category_type=Category.CategoryType.INCOME,
        )

        self.other_user_category = Category.objects.create(
            user=self.other_user,
            name="Jane Food",
            category_type=Category.CategoryType.EXPENSE,
        )

        Transaction.objects.create(
            user=self.user,
            category=self.income_category,
            transaction_type=Transaction.TransactionType.INCOME,
            amount=Decimal("1500.00"),
            description="First paycheck",
            transaction_date=date(2026, 6, 1),
        )
        Transaction.objects.create(
            user=self.user,
            category=self.income_category,
            transaction_type=Transaction.TransactionType.INCOME,
            amount=Decimal("1500.00"),
            description="Second paycheck",
            transaction_date=date(2026, 6, 15),
        )
        Transaction.objects.create(
            user=self.user,
            category=self.food_category,
            transaction_type=Transaction.TransactionType.EXPENSE,
            amount=Decimal("75.50"),
            description="Groceries",
            transaction_date=date(2026, 6, 10),
        )
        Transaction.objects.create(
            user=self.user,
            category=self.food_category,
            transaction_type=Transaction.TransactionType.EXPENSE,
            amount=Decimal("25.00"),
            description="Restaurant",
            transaction_date=date(2026, 6, 12),
        )
        Transaction.objects.create(
            user=self.user,
            category=self.housing_category,
            transaction_type=Transaction.TransactionType.EXPENSE,
            amount=Decimal("950.00"),
            description="Rent",
            transaction_date=date(2026, 6, 5),
        )

        Transaction.objects.create(
            user=self.other_user,
            category=self.other_user_category,
            transaction_type=Transaction.TransactionType.EXPENSE,
            amount=Decimal("9999.99"),
            description="Jane private expense",
            transaction_date=date(2026, 6, 20),
        )

    def test_dashboard_displays_total_income(self) -> None:
        self.client.login(username="johnny", password="StrongPass123!")

        response = self.client.get(reverse("tracker:dashboard"))

        self.assertEqual(response.context["total_income"], Decimal("3000.00"))
        self.assertContains(response, "3000.00")

    def test_dashboard_displays_total_expenses(self) -> None:
        self.client.login(username="johnny", password="StrongPass123!")

        response = self.client.get(reverse("tracker:dashboard"))

        self.assertEqual(response.context["total_expenses"], Decimal("1050.50"))
        self.assertContains(response, "1050.50")

    def test_dashboard_calculates_balance(self) -> None:
        self.client.login(username="johnny", password="StrongPass123!")

        response = self.client.get(reverse("tracker:dashboard"))

        self.assertEqual(response.context["balance"], Decimal("1949.50"))
        self.assertContains(response, "1949.50")

    def test_dashboard_groups_expenses_by_category(self) -> None:
        self.client.login(username="johnny", password="StrongPass123!")

        response = self.client.get(reverse("tracker:dashboard"))

        category_totals = list(response.context["expense_totals_by_category"])

        self.assertEqual(
            category_totals,
            [
                {
                    "category__name": "Housing",
                    "total": Decimal("950.00"),
                },
                {
                    "category__name": "Food",
                    "total": Decimal("100.50"),
                },
            ],
        )

    def test_dashboard_does_not_include_another_users_transactions(self) -> None:
        self.client.login(username="johnny", password="StrongPass123!")

        response = self.client.get(reverse("tracker:dashboard"))

        self.assertEqual(response.context["total_income"], Decimal("3000.00"))
        self.assertEqual(response.context["total_expenses"], Decimal("1050.50"))
        self.assertNotContains(response, "Jane private expense")
        self.assertNotContains(response, "9999.99")

    def test_dashboard_displays_five_most_recent_transactions(self) -> None:
        self.client.login(username="johnny", password="StrongPass123!")

        response = self.client.get(reverse("tracker:dashboard"))

        recent_transactions = list(response.context["recent_transactions"])

        self.assertEqual(len(recent_transactions), 5)
        self.assertEqual(recent_transactions[0].description, "Second paycheck")
        self.assertEqual(recent_transactions[1].description, "Restaurant")
        self.assertEqual(recent_transactions[2].description, "Groceries")

    def test_dashboard_with_no_transactions_uses_zero_totals(self) -> None:
        User.objects.create_user(
            username="emptyuser",
            password="StrongPass123!",
        )
        self.client.login(username="emptyuser", password="StrongPass123!")

        response = self.client.get(reverse("tracker:dashboard"))

        self.assertEqual(response.context["total_income"], Decimal("0.00"))
        self.assertEqual(response.context["total_expenses"], Decimal("0.00"))
        self.assertEqual(response.context["balance"], Decimal("0.00"))
        self.assertContains(response, "No expense data is available yet.")
        self.assertContains(response, "You do not have any transactions yet.")


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


class CategoryViewTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="johnny",
            password="StrongPass123!",
        )
        self.other_user = User.objects.create_user(
            username="jane",
            password="StrongPass123!",
        )

        self.category = Category.objects.create(
            user=self.user,
            name="Food",
            category_type=Category.CategoryType.EXPENSE,
        )
        self.other_user_category = Category.objects.create(
            user=self.other_user,
            name="Jane Secret Category",
            category_type=Category.CategoryType.EXPENSE,
        )

    def test_logged_out_user_is_redirected_from_category_list(self) -> None:
        response = self.client.get(reverse("tracker:category_list"))

        expected_url = f"{reverse('login')}?next={reverse('tracker:category_list')}"
        self.assertRedirects(response, expected_url)

    def test_logged_in_user_can_view_category_list(self) -> None:
        self.client.login(username="johnny", password="StrongPass123!")

        response = self.client.get(reverse("tracker:category_list"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tracker/category_list.html")
        self.assertContains(response, "Food")

    def test_user_only_sees_their_own_categories(self) -> None:
        self.client.login(username="johnny", password="StrongPass123!")

        response = self.client.get(reverse("tracker:category_list"))

        self.assertContains(response, "Food")
        self.assertNotContains(response, "Jane Secret Category")

    def test_logged_in_user_can_create_category(self) -> None:
        self.client.login(username="johnny", password="StrongPass123!")

        response = self.client.post(
            reverse("tracker:category_create"),
            {
                "name": "Rent",
                "category_type": Category.CategoryType.EXPENSE,
            },
        )

        self.assertRedirects(response, reverse("tracker:category_list"))
        self.assertTrue(
            Category.objects.filter(
                user=self.user,
                name="Rent",
                category_type=Category.CategoryType.EXPENSE,
            ).exists()
        )

    def test_created_category_is_assigned_to_logged_in_user(self) -> None:
        self.client.login(username="johnny", password="StrongPass123!")

        self.client.post(
            reverse("tracker:category_create"),
            {
                "name": "Paycheck",
                "category_type": Category.CategoryType.INCOME,
            },
        )

        category = Category.objects.get(name="Paycheck")

        self.assertEqual(category.user, self.user)

    def test_duplicate_category_for_same_user_shows_form_error(self) -> None:
        self.client.login(username="johnny", password="StrongPass123!")

        response = self.client.post(
            reverse("tracker:category_create"),
            {
                "name": "Food",
                "category_type": Category.CategoryType.EXPENSE,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "You already have a category with this name and type.",
        )
        self.assertEqual(
            Category.objects.filter(
                user=self.user,
                name__iexact="Food",
                category_type=Category.CategoryType.EXPENSE,
            ).count(),
            1,
        )

    def test_logged_in_user_can_update_their_own_category(self) -> None:
        self.client.login(username="johnny", password="StrongPass123!")

        response = self.client.post(
            reverse("tracker:category_update", args=[self.category.pk]),
            {
                "name": "Groceries",
                "category_type": Category.CategoryType.EXPENSE,
            },
        )

        self.assertRedirects(response, reverse("tracker:category_list"))

        self.category.refresh_from_db()

        self.assertEqual(self.category.name, "Groceries")

    def test_user_cannot_update_another_users_category(self) -> None:
        self.client.login(username="johnny", password="StrongPass123!")

        response = self.client.post(
            reverse("tracker:category_update", args=[self.other_user_category.pk]),
            {
                "name": "Hacked Category",
                "category_type": Category.CategoryType.EXPENSE,
            },
        )

        self.assertEqual(response.status_code, 404)

        self.other_user_category.refresh_from_db()

        self.assertEqual(self.other_user_category.name, "Jane Secret Category")

    def test_logged_in_user_can_delete_their_own_category(self) -> None:
        self.client.login(username="johnny", password="StrongPass123!")

        response = self.client.post(
            reverse("tracker:category_delete", args=[self.category.pk])
        )

        self.assertRedirects(response, reverse("tracker:category_list"))
        self.assertFalse(Category.objects.filter(pk=self.category.pk).exists())

    def test_user_cannot_delete_another_users_category(self) -> None:
        self.client.login(username="johnny", password="StrongPass123!")

        response = self.client.post(
            reverse("tracker:category_delete", args=[self.other_user_category.pk])
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(
            Category.objects.filter(pk=self.other_user_category.pk).exists()
        )

    def test_delete_category_confirmation_page_loads(self) -> None:
        self.client.login(username="johnny", password="StrongPass123!")

        response = self.client.get(
            reverse("tracker:category_delete", args=[self.category.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tracker/category_confirm_delete.html")
        self.assertContains(response, "Are you sure you want to delete")


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

    def test_transaction_date_cannot_be_in_future(self) -> None:
        future_date = timezone.localdate() + timedelta(days=1)

        transaction = Transaction(
            user=self.user,
            category=self.expense_category,
            transaction_type=Transaction.TransactionType.EXPENSE,
            amount=Decimal("25.00"),
            description="Future transaction",
            transaction_date=future_date,
        )

        with self.assertRaises(ValidationError) as context:
            transaction.full_clean()

        self.assertIn("transaction_date", context.exception.message_dict)
        self.assertIn(
            "Transaction date cannot be in the future.",
            context.exception.message_dict["transaction_date"],
        )

    def test_transaction_description_is_stripped(self) -> None:
        transaction = Transaction(
            user=self.user,
            category=self.expense_category,
            transaction_type=Transaction.TransactionType.EXPENSE,
            amount=Decimal("25.00"),
            description="   Groceries   ",
            transaction_date=timezone.localdate(),
        )

        transaction.full_clean()

        self.assertEqual(transaction.description, "Groceries")

    def test_transaction_description_cannot_be_only_whitespace(self) -> None:
        transaction = Transaction(
            user=self.user,
            category=self.expense_category,
            transaction_type=Transaction.TransactionType.EXPENSE,
            amount=Decimal("25.00"),
            description="      ",
            transaction_date=timezone.localdate(),
        )

        with self.assertRaises(ValidationError) as context:
            transaction.full_clean()

        self.assertIn("description", context.exception.message_dict)
        self.assertIn(
            "Description cannot contain only whitespace.",
            context.exception.message_dict["description"],
        )


class TransactionViewTests(TestCase):
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
        self.other_user_category = Category.objects.create(
            user=self.other_user,
            name="Jane Food",
            category_type=Category.CategoryType.EXPENSE,
        )

        self.transaction = Transaction.objects.create(
            user=self.user,
            category=self.expense_category,
            transaction_type=Transaction.TransactionType.EXPENSE,
            amount=Decimal("84.32"),
            description="Groceries",
            transaction_date=date(2026, 6, 11),
        )
        self.other_user_transaction = Transaction.objects.create(
            user=self.other_user,
            category=self.other_user_category,
            transaction_type=Transaction.TransactionType.EXPENSE,
            amount=Decimal("50.00"),
            description="Jane Secret Transaction",
            transaction_date=date(2026, 6, 11),
        )

    def test_logged_out_user_is_redirected_from_transaction_list(self) -> None:
        response = self.client.get(reverse("tracker:transaction_list"))

        expected_url = f"{reverse('login')}?next={reverse('tracker:transaction_list')}"
        self.assertRedirects(response, expected_url)

    def test_logged_in_user_can_view_transaction_list(self) -> None:
        self.client.login(username="johnny", password="StrongPass123!")

        response = self.client.get(reverse("tracker:transaction_list"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tracker/transaction_list.html")
        self.assertContains(response, "Groceries")

    def test_user_only_sees_their_own_transactions(self) -> None:
        self.client.login(username="johnny", password="StrongPass123!")

        response = self.client.get(reverse("tracker:transaction_list"))

        self.assertContains(response, "Groceries")
        self.assertNotContains(response, "Jane Secret Transaction")

    def test_logged_in_user_can_view_transaction_detail(self) -> None:
        self.client.login(username="johnny", password="StrongPass123!")

        response = self.client.get(
            reverse("tracker:transaction_detail", args=[self.transaction.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tracker/transaction_detail.html")
        self.assertContains(response, "Groceries")
        self.assertContains(response, "84.32")

    def test_user_cannot_view_another_users_transaction_detail(self) -> None:
        self.client.login(username="johnny", password="StrongPass123!")

        response = self.client.get(
            reverse(
                "tracker:transaction_detail",
                args=[self.other_user_transaction.pk],
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_logged_in_user_can_create_transaction(self) -> None:
        self.client.login(username="johnny", password="StrongPass123!")

        response = self.client.post(
            reverse("tracker:transaction_create"),
            {
                "transaction_type": Transaction.TransactionType.EXPENSE,
                "category": self.expense_category.pk,
                "amount": "25.50",
                "description": "Gas",
                "transaction_date": "2026-06-12",
            },
        )

        self.assertRedirects(response, reverse("tracker:transaction_list"))
        self.assertTrue(
            Transaction.objects.filter(
                user=self.user,
                description="Gas",
                amount=Decimal("25.50"),
            ).exists()
        )

    def test_created_transaction_is_assigned_to_logged_in_user(self) -> None:
        self.client.login(username="johnny", password="StrongPass123!")

        self.client.post(
            reverse("tracker:transaction_create"),
            {
                "transaction_type": Transaction.TransactionType.INCOME,
                "category": self.income_category.pk,
                "amount": "2000.00",
                "description": "Paycheck",
                "transaction_date": "2026-06-13",
            },
        )

        transaction = Transaction.objects.get(description="Paycheck")

        self.assertEqual(transaction.user, self.user)

    def test_user_cannot_create_transaction_with_another_users_category(self) -> None:
        self.client.login(username="johnny", password="StrongPass123!")

        response = self.client.post(
            reverse("tracker:transaction_create"),
            {
                "transaction_type": Transaction.TransactionType.EXPENSE,
                "category": self.other_user_category.pk,
                "amount": "25.50",
                "description": "Invalid transaction",
                "transaction_date": "2026-06-12",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            Transaction.objects.filter(description="Invalid transaction").exists()
        )

    def test_transaction_type_must_match_category_type_in_form(self) -> None:
        self.client.login(username="johnny", password="StrongPass123!")

        response = self.client.post(
            reverse("tracker:transaction_create"),
            {
                "transaction_type": Transaction.TransactionType.EXPENSE,
                "category": self.income_category.pk,
                "amount": "25.50",
                "description": "Wrong category type",
                "transaction_date": "2026-06-12",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "The selected category type must match the transaction type.",
        )
        self.assertFalse(
            Transaction.objects.filter(description="Wrong category type").exists()
        )

    def test_logged_in_user_can_update_their_own_transaction(self) -> None:
        self.client.login(username="johnny", password="StrongPass123!")

        response = self.client.post(
            reverse("tracker:transaction_update", args=[self.transaction.pk]),
            {
                "transaction_type": Transaction.TransactionType.EXPENSE,
                "category": self.expense_category.pk,
                "amount": "99.99",
                "description": "Updated groceries",
                "transaction_date": "2026-06-14",
            },
        )

        self.assertRedirects(
            response,
            reverse("tracker:transaction_detail", args=[self.transaction.pk]),
        )

        self.transaction.refresh_from_db()

        self.assertEqual(self.transaction.description, "Updated groceries")
        self.assertEqual(self.transaction.amount, Decimal("99.99"))

    def test_user_cannot_update_another_users_transaction(self) -> None:
        self.client.login(username="johnny", password="StrongPass123!")

        response = self.client.post(
            reverse(
                "tracker:transaction_update",
                args=[self.other_user_transaction.pk],
            ),
            {
                "transaction_type": Transaction.TransactionType.EXPENSE,
                "category": self.expense_category.pk,
                "amount": "1.00",
                "description": "Hacked transaction",
                "transaction_date": "2026-06-14",
            },
        )

        self.assertEqual(response.status_code, 404)

        self.other_user_transaction.refresh_from_db()

        self.assertEqual(
            self.other_user_transaction.description,
            "Jane Secret Transaction",
        )

    def test_logged_in_user_can_delete_their_own_transaction(self) -> None:
        self.client.login(username="johnny", password="StrongPass123!")

        response = self.client.post(
            reverse("tracker:transaction_delete", args=[self.transaction.pk])
        )

        self.assertRedirects(response, reverse("tracker:transaction_list"))
        self.assertFalse(Transaction.objects.filter(pk=self.transaction.pk).exists())

    def test_user_cannot_delete_another_users_transaction(self) -> None:
        self.client.login(username="johnny", password="StrongPass123!")

        response = self.client.post(
            reverse(
                "tracker:transaction_delete",
                args=[self.other_user_transaction.pk],
            )
        )

        self.assertEqual(response.status_code, 404)
        self.assertTrue(
            Transaction.objects.filter(pk=self.other_user_transaction.pk).exists()
        )

    def test_delete_transaction_confirmation_page_loads(self) -> None:
        self.client.login(username="johnny", password="StrongPass123!")

        response = self.client.get(
            reverse("tracker:transaction_delete", args=[self.transaction.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tracker/transaction_confirm_delete.html")
        self.assertContains(response, "Are you sure you want to delete")


class TransactionFilterTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="johnny",
            password="StrongPass123!",
        )
        self.other_user = User.objects.create_user(
            username="jane",
            password="StrongPass123!",
        )

        self.food_category = Category.objects.create(
            user=self.user,
            name="Food",
            category_type=Category.CategoryType.EXPENSE,
        )
        self.transportation_category = Category.objects.create(
            user=self.user,
            name="Transportation",
            category_type=Category.CategoryType.EXPENSE,
        )
        self.income_category = Category.objects.create(
            user=self.user,
            name="Paycheck",
            category_type=Category.CategoryType.INCOME,
        )
        self.other_user_category = Category.objects.create(
            user=self.other_user,
            name="Jane Food",
            category_type=Category.CategoryType.EXPENSE,
        )

        Transaction.objects.create(
            user=self.user,
            category=self.food_category,
            transaction_type=Transaction.TransactionType.EXPENSE,
            amount=Decimal("75.50"),
            description="Weekly groceries",
            transaction_date=date(2026, 6, 10),
        )
        Transaction.objects.create(
            user=self.user,
            category=self.food_category,
            transaction_type=Transaction.TransactionType.EXPENSE,
            amount=Decimal("25.00"),
            description="Restaurant dinner",
            transaction_date=date(2026, 5, 15),
        )
        Transaction.objects.create(
            user=self.user,
            category=self.transportation_category,
            transaction_type=Transaction.TransactionType.EXPENSE,
            amount=Decimal("40.00"),
            description="Gas station",
            transaction_date=date(2025, 6, 5),
        )
        Transaction.objects.create(
            user=self.user,
            category=self.income_category,
            transaction_type=Transaction.TransactionType.INCOME,
            amount=Decimal("1500.00"),
            description="Biweekly paycheck",
            transaction_date=date(2026, 6, 1),
        )
        Transaction.objects.create(
            user=self.other_user,
            category=self.other_user_category,
            transaction_type=Transaction.TransactionType.EXPENSE,
            amount=Decimal("999.99"),
            description="Jane private groceries",
            transaction_date=date(2026, 6, 10),
        )

        self.client.login(
            username="johnny",
            password="StrongPass123!",
        )

    def test_search_filters_by_description(self) -> None:
        response = self.client.get(
            reverse("tracker:transaction_list"),
            {"search": "groceries"},
        )

        self.assertContains(response, "Weekly groceries")
        self.assertNotContains(response, "Restaurant dinner")
        self.assertNotContains(response, "Gas station")
        self.assertNotContains(response, "Biweekly paycheck")

    def test_search_is_case_insensitive(self) -> None:
        response = self.client.get(
            reverse("tracker:transaction_list"),
            {"search": "GROCERIES"},
        )

        self.assertContains(response, "Weekly groceries")

    def test_search_filters_by_category_name(self) -> None:
        response = self.client.get(
            reverse("tracker:transaction_list"),
            {"search": "Transportation"},
        )

        self.assertContains(response, "Gas station")
        self.assertNotContains(response, "Weekly groceries")

    def test_filter_by_transaction_type(self) -> None:
        response = self.client.get(
            reverse("tracker:transaction_list"),
            {
                "transaction_type": Transaction.TransactionType.INCOME,
            },
        )

        self.assertContains(response, "Biweekly paycheck")
        self.assertNotContains(response, "Weekly groceries")
        self.assertNotContains(response, "Restaurant dinner")
        self.assertNotContains(response, "Gas station")

    def test_filter_by_category(self) -> None:
        response = self.client.get(
            reverse("tracker:transaction_list"),
            {"category": self.food_category.pk},
        )

        self.assertContains(response, "Weekly groceries")
        self.assertContains(response, "Restaurant dinner")
        self.assertNotContains(response, "Gas station")
        self.assertNotContains(response, "Biweekly paycheck")

    def test_filter_by_month(self) -> None:
        response = self.client.get(
            reverse("tracker:transaction_list"),
            {"month": "6"},
        )

        self.assertContains(response, "Weekly groceries")
        self.assertContains(response, "Gas station")
        self.assertContains(response, "Biweekly paycheck")
        self.assertNotContains(response, "Restaurant dinner")

    def test_filter_by_year(self) -> None:
        response = self.client.get(
            reverse("tracker:transaction_list"),
            {"year": "2025"},
        )

        self.assertContains(response, "Gas station")
        self.assertNotContains(response, "Weekly groceries")
        self.assertNotContains(response, "Restaurant dinner")
        self.assertNotContains(response, "Biweekly paycheck")

    def test_multiple_filters_can_be_combined(self) -> None:
        response = self.client.get(
            reverse("tracker:transaction_list"),
            {
                "transaction_type": Transaction.TransactionType.EXPENSE,
                "category": self.food_category.pk,
                "month": "6",
                "year": "2026",
            },
        )

        self.assertContains(response, "Weekly groceries")
        self.assertNotContains(response, "Restaurant dinner")
        self.assertNotContains(response, "Gas station")
        self.assertNotContains(response, "Biweekly paycheck")

    def test_filter_form_only_contains_logged_in_users_categories(self) -> None:
        response = self.client.get(reverse("tracker:transaction_list"))

        category_queryset = response.context["filter_form"].fields["category"].queryset

        self.assertIn(self.food_category, category_queryset)
        self.assertIn(self.transportation_category, category_queryset)
        self.assertIn(self.income_category, category_queryset)
        self.assertNotIn(self.other_user_category, category_queryset)

    def test_user_cannot_filter_using_another_users_category(self) -> None:
        response = self.client.get(
            reverse("tracker:transaction_list"),
            {"category": self.other_user_category.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["filter_form"].errors)
        self.assertNotContains(response, "Jane private groceries")

    def test_filters_never_include_another_users_transactions(self) -> None:
        response = self.client.get(
            reverse("tracker:transaction_list"),
            {
                "search": "groceries",
                "month": "6",
                "year": "2026",
            },
        )

        self.assertContains(response, "Weekly groceries")
        self.assertNotContains(response, "Jane private groceries")

    def test_no_matches_displays_filtered_empty_state(self) -> None:
        response = self.client.get(
            reverse("tracker:transaction_list"),
            {"search": "does not exist"},
        )

        self.assertContains(
            response,
            "No transactions matched your filters.",
        )
        self.assertNotContains(
            response,
            "You do not have any transactions yet.",
        )

    def test_clear_filters_link_appears_when_filter_is_active(self) -> None:
        response = self.client.get(
            reverse("tracker:transaction_list"),
            {"search": "groceries"},
        )

        self.assertContains(response, "Clear Filters")

    def test_year_choices_only_include_users_transaction_years(self) -> None:
        response = self.client.get(reverse("tracker:transaction_list"))

        year_choices = response.context["filter_form"].fields["year"].choices

        self.assertIn(("2026", "2026"), year_choices)
        self.assertIn(("2025", "2025"), year_choices)


class TransactionPaginationTests(TestCase):
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
        self.other_user_category = Category.objects.create(
            user=self.other_user,
            name="Jane Food",
            category_type=Category.CategoryType.EXPENSE,
        )

        for transaction_number in range(1, 13):
            Transaction.objects.create(
                user=self.user,
                category=self.expense_category,
                transaction_type=Transaction.TransactionType.EXPENSE,
                amount=Decimal("10.00"),
                description=f"John transaction {transaction_number}",
                transaction_date=date(2026, 6, transaction_number),
            )

        Transaction.objects.create(
            user=self.other_user,
            category=self.other_user_category,
            transaction_type=Transaction.TransactionType.EXPENSE,
            amount=Decimal("999.99"),
            description="Jane private transaction",
            transaction_date=date(2026, 6, 20),
        )

        self.client.login(
            username="johnny",
            password="StrongPass123!",
        )

    def test_first_page_contains_five_transactions(self) -> None:
        response = self.client.get(reverse("tracker:transaction_list"))

        self.assertEqual(len(response.context["page_obj"]), 5)
        self.assertEqual(response.context["page_obj"].number, 1)
        self.assertEqual(
            response.context["page_obj"].paginator.num_pages,
            3,
        )

    def test_second_page_contains_next_five_transactions(self) -> None:
        response = self.client.get(
            reverse("tracker:transaction_list"),
            {"page": "2"},
        )

        page_obj = response.context["page_obj"]

        self.assertEqual(page_obj.number, 2)
        self.assertEqual(len(page_obj), 5)
        self.assertTrue(page_obj.has_previous())
        self.assertTrue(page_obj.has_next())

    def test_last_page_contains_remaining_transactions(self) -> None:
        response = self.client.get(
            reverse("tracker:transaction_list"),
            {"page": "3"},
        )

        page_obj = response.context["page_obj"]

        self.assertEqual(page_obj.number, 3)
        self.assertEqual(len(page_obj), 2)
        self.assertTrue(page_obj.has_previous())
        self.assertFalse(page_obj.has_next())

    def test_invalid_page_value_returns_first_page(self) -> None:
        response = self.client.get(
            reverse("tracker:transaction_list"),
            {"page": "invalid"},
        )

        self.assertEqual(response.context["page_obj"].number, 1)

    def test_page_beyond_range_returns_last_page(self) -> None:
        response = self.client.get(
            reverse("tracker:transaction_list"),
            {"page": "999"},
        )

        self.assertEqual(response.context["page_obj"].number, 3)

    def test_pagination_does_not_include_other_users_transactions(self) -> None:
        response = self.client.get(
            reverse("tracker:transaction_list"),
            {"page": "1"},
        )

        self.assertEqual(
            response.context["page_obj"].paginator.count,
            12,
        )
        self.assertNotContains(response, "Jane private transaction")

    def test_filter_query_parameters_are_preserved(self) -> None:
        response = self.client.get(
            reverse("tracker:transaction_list"),
            {
                "search": "John",
                "transaction_type": Transaction.TransactionType.EXPENSE,
                "month": "6",
                "year": "2026",
                "page": "2",
            },
        )

        self.assertEqual(
            response.context["query_string"],
            "search=John&transaction_type=expense&month=6&year=2026",
        )

    def test_page_parameter_is_not_duplicated_in_query_string(self) -> None:
        response = self.client.get(
            reverse("tracker:transaction_list"),
            {
                "search": "John",
                "page": "2",
            },
        )

        query_string = response.context["query_string"]

        self.assertEqual(query_string, "search=John")
        self.assertNotIn("page=", query_string)

    def test_filtered_results_are_paginated(self) -> None:
        Transaction.objects.create(
            user=self.user,
            category=self.expense_category,
            transaction_type=Transaction.TransactionType.EXPENSE,
            amount=Decimal("20.00"),
            description="Unrelated purchase",
            transaction_date=date(2025, 1, 1),
        )

        response = self.client.get(
            reverse("tracker:transaction_list"),
            {
                "search": "John transaction",
                "year": "2026",
            },
        )

        page_obj = response.context["page_obj"]

        self.assertEqual(page_obj.paginator.count, 12)
        self.assertEqual(page_obj.paginator.num_pages, 3)
        self.assertNotContains(response, "Unrelated purchase")


class TransactionValidationTests(TestCase):
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
        self.other_user_category = Category.objects.create(
            user=self.other_user,
            name="Jane Food",
            category_type=Category.CategoryType.EXPENSE,
        )

        self.client.login(
            username="johnny",
            password="StrongPass123!",
        )

    def test_future_transaction_date_shows_field_error(self) -> None:
        future_date = timezone.localdate() + timedelta(days=1)

        response = self.client.post(
            reverse("tracker:transaction_create"),
            {
                "transaction_type": Transaction.TransactionType.EXPENSE,
                "category": self.expense_category.pk,
                "amount": "25.00",
                "description": "Future purchase",
                "transaction_date": future_date.isoformat(),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context["form"],
            "transaction_date",
            "Transaction date cannot be in the future.",
        )
        self.assertFalse(
            Transaction.objects.filter(description="Future purchase").exists()
        )

    def test_zero_amount_shows_clear_field_error(self) -> None:
        response = self.client.post(
            reverse("tracker:transaction_create"),
            {
                "transaction_type": Transaction.TransactionType.EXPENSE,
                "category": self.expense_category.pk,
                "amount": "0.00",
                "description": "Invalid amount",
                "transaction_date": timezone.localdate().isoformat(),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context["form"],
            "amount",
            "Amount must be at least $0.01.",
        )
        self.assertFalse(
            Transaction.objects.filter(description="Invalid amount").exists()
        )

    def test_negative_amount_shows_clear_field_error(self) -> None:
        response = self.client.post(
            reverse("tracker:transaction_create"),
            {
                "transaction_type": Transaction.TransactionType.EXPENSE,
                "category": self.expense_category.pk,
                "amount": "-10.00",
                "description": "Negative amount",
                "transaction_date": timezone.localdate().isoformat(),
            },
        )

        self.assertFormError(
            response.context["form"],
            "amount",
            "Amount must be at least $0.01.",
        )
        self.assertFalse(
            Transaction.objects.filter(description="Negative amount").exists()
        )

    def test_whitespace_description_shows_field_error(self) -> None:
        response = self.client.post(
            reverse("tracker:transaction_create"),
            {
                "transaction_type": Transaction.TransactionType.EXPENSE,
                "category": self.expense_category.pk,
                "amount": "25.00",
                "description": "       ",
                "transaction_date": timezone.localdate().isoformat(),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context["form"],
            "description",
            "Description cannot contain only whitespace.",
        )
        self.assertEqual(Transaction.objects.count(), 0)

    def test_description_is_trimmed_before_transaction_is_saved(self) -> None:
        response = self.client.post(
            reverse("tracker:transaction_create"),
            {
                "transaction_type": Transaction.TransactionType.EXPENSE,
                "category": self.expense_category.pk,
                "amount": "25.00",
                "description": "   Weekly groceries   ",
                "transaction_date": timezone.localdate().isoformat(),
            },
        )

        self.assertRedirects(
            response,
            reverse("tracker:transaction_list"),
        )

        transaction = Transaction.objects.get()

        self.assertEqual(transaction.description, "Weekly groceries")

    def test_tampered_category_type_combination_is_rejected(self) -> None:
        response = self.client.post(
            reverse("tracker:transaction_create"),
            {
                "transaction_type": Transaction.TransactionType.EXPENSE,
                "category": self.income_category.pk,
                "amount": "25.00",
                "description": "Invalid category combination",
                "transaction_date": timezone.localdate().isoformat(),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context["form"],
            "category",
            "The selected category type must match the transaction type.",
        )
        self.assertFalse(
            Transaction.objects.filter(
                description="Invalid category combination"
            ).exists()
        )

    def test_tampered_other_user_category_is_rejected(self) -> None:
        response = self.client.post(
            reverse("tracker:transaction_create"),
            {
                "transaction_type": Transaction.TransactionType.EXPENSE,
                "category": self.other_user_category.pk,
                "amount": "25.00",
                "description": "Tampered category",
                "transaction_date": timezone.localdate().isoformat(),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context["form"],
            "category",
            "Select a valid choice. That choice is not one of the available choices.",
        )
        self.assertFalse(
            Transaction.objects.filter(description="Tampered category").exists()
        )


class TemplatePolishTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="johnny",
            password="StrongPass123!",
        )
        self.category = Category.objects.create(
            user=self.user,
            name="Food",
            category_type=Category.CategoryType.EXPENSE,
        )

    def test_base_template_loads_stylesheet(self) -> None:
        response = self.client.get(reverse("tracker:home"))

        self.assertContains(
            response,
            'href="/static/tracker/styles.css"',
        )

    def test_dashboard_uses_summary_card_layout(self) -> None:
        self.client.login(
            username="johnny",
            password="StrongPass123!",
        )

        response = self.client.get(reverse("tracker:dashboard"))

        self.assertContains(response, 'class="summary-grid"')
        self.assertContains(response, "Total Income")
        self.assertContains(response, "Total Expenses")
        self.assertContains(response, "Balance")

    def test_success_message_uses_success_alert_class(self) -> None:
        self.client.login(
            username="johnny",
            password="StrongPass123!",
        )

        response = self.client.post(
            reverse("tracker:category_create"),
            {
                "name": "Transportation",
                "category_type": Category.CategoryType.EXPENSE,
            },
            follow=True,
        )

        self.assertContains(
            response,
            "Category created successfully.",
        )
        self.assertContains(
            response,
            "alert-success",
        )

    def test_login_form_preserves_next_destination(self) -> None:
        response = self.client.get(
            reverse("login"),
            {"next": reverse("tracker:dashboard")},
        )

        self.assertContains(
            response,
            'name="next"',
        )
        self.assertContains(
            response,
            f'value="{reverse("tracker:dashboard")}"',
        )
