from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator


class Category(models.Model):
    class CategoryType(models.TextChoices):
        INCOME = "income", "Income"
        EXPENSE = "expense", "Expense"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="categories",
    )
    name = models.CharField(max_length=100)
    category_type = models.CharField(
        max_length=20,
        choices=CategoryType.choices,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "name", "category_type"],
                name="unique_category_name_type_per_user",
            )
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.get_category_type_display()})"


class Transaction(models.Model):
    class TransactionType(models.TextChoices):
        INCOME = "income", "Income"
        EXPENSE = "expense", "Expense"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="transactions",
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.RESTRICT,
        related_name="transactions",
    )

    transaction_type = models.CharField(
        max_length=20,
        choices=TransactionType.choices,
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )

    description = models.CharField(max_length=255)
    transaction_date = models.DateField(default=timezone.localdate)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-transaction_date", "-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name="transaction_amount_must_be_positive",
            )
        ]

    def clean(self) -> None:
        if self.category_id and self.category.user_id != self.user_id:
            raise ValidationError(
                "The selected category must belong to the transaction owner."
            )

        if self.category_id and self.category.category_type != self.transaction_type:
            raise ValidationError(
                "The selected category type must match the transaction type."
            )

    def __str__(self) -> str:
        return f"{self.description} - {self.amount}"
