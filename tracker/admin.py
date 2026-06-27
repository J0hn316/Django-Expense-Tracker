from django.contrib import admin

from .models import Category, Transaction


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "category_type",
        "user",
        "created_at",
    ]
    list_filter = [
        "category_type",
        "created_at",
    ]
    search_fields = [
        "name",
        "user__username",
    ]
    ordering = [
        "user__username",
        "name",
    ]
    list_select_related = [
        "user",
    ]


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
    list_filter = [
        "transaction_type",
        "category",
        "transaction_date",
    ]
    search_fields = [
        "description",
        "category__name",
        "user__username",
    ]
    ordering = [
        "-transaction_date",
        "-created_at",
    ]
    date_hierarchy = "transaction_date"
    list_select_related = [
        "category",
        "user",
    ]
