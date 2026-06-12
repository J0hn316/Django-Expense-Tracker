from django.db import models
from django.conf import settings


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
