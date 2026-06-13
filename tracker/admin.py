from django.contrib import admin

from .models import Category, Transaction


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "category_type", "user", "created_at"]
    list_filter = ["category_type", "created_at"]
    search_fields = ["name", "user__username"]


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        "description",
        "transaction_type",
        "amount",
        "category",
        "user",
        "transaction_date",
    ]
    list_filter = ["transaction_type", "category", "transaction_date"]
    search_fields = ["description", "category__name", "user__username"]
    date_hierarchy = "transaction_date"
