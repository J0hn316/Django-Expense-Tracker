from django import forms
from datetime import date
from decimal import Decimal
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Category, Transaction


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "category_type"]

    def __init__(self, *args, user: User | None = None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_name(self) -> str:
        name = self.cleaned_data["name"].strip()

        if not name:
            raise forms.ValidationError("Category name cannot be empty.")

        return name

    def clean(self) -> dict:
        cleaned_data = super().clean()

        name = cleaned_data.get("name")
        category_type = cleaned_data.get("category_type")

        if self.user and name and category_type:
            duplicate_categories = Category.objects.filter(
                user=self.user,
                name__iexact=name,
                category_type=category_type,
            )

            if self.instance.pk:
                duplicate_categories = duplicate_categories.exclude(pk=self.instance.pk)

            if duplicate_categories.exists():
                raise forms.ValidationError(
                    "You already have a category with this name and type."
                )

        return cleaned_data


class TransactionForm(forms.ModelForm):
    description = forms.CharField(
        max_length=255,
        strip=False,
    )
    amount = forms.DecimalField(
        min_value=Decimal("0.01"),
        max_digits=10,
        decimal_places=2,
        error_messages={
            "required": "Enter a transaction amount.",
            "invalid": "Enter a valid monetary amount.",
            "min_value": "Amount must be at least $0.01.",
            "max_digits": "Amount cannot contain more than 10 digits.",
            "max_decimal_places": "Amount cannot contain more than two decimal places.",
        },
    )

    class Meta:
        model = Transaction
        fields = [
            "transaction_type",
            "category",
            "amount",
            "description",
            "transaction_date",
        ]
        widgets = {
            "transaction_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "max": date.today().isoformat(),
                }
            ),
        }

    def __init__(self, *args, user: User | None = None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.user = user

        if self.user:
            self.instance.user = self.user
            self.fields["category"].queryset = Category.objects.filter(user=self.user)


class TransactionFilterForm(forms.Form):
    search = forms.CharField(
        required=False,
        label="Search",
        widget=forms.TextInput(
            attrs={"placeholder": "Search descriptions or categories"}
        ),
    )
    transaction_type = forms.ChoiceField(
        required=False,
        label="Type",
        choices=[
            ("", "All Types"),
            *Transaction.TransactionType.choices,
        ],
    )
    category = forms.ModelChoiceField(
        required=False,
        queryset=Category.objects.none(),
        empty_label="All Categories",
    )
    month = forms.ChoiceField(
        required=False,
        choices=[("", "All Months")],
    )
    year = forms.ChoiceField(
        required=False,
        choices=[("", "All Years")],
    )

    def __init__(
        self,
        *args,
        user: User | None = None,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.user = user

        if self.user:
            self.fields["category"].queryset = Category.objects.filter(user=self.user)

            transaction_dates = Transaction.objects.filter(user=self.user).dates(
                "transaction_date",
                "year",
                order="DESC",
            )

            available_years = [
                transaction_date.year for transaction_date in transaction_dates
            ]

            self.fields["year"].choices = [
                ("", "All Years"),
                *[(str(year), str(year)) for year in available_years],
            ]

        self.fields["month"].choices = [
            ("", "All Months"),
            *[
                (str(month_number), month_name)
                for month_number, month_name in enumerate(
                    [
                        "January",
                        "February",
                        "March",
                        "April",
                        "May",
                        "June",
                        "July",
                        "August",
                        "September",
                        "October",
                        "November",
                        "December",
                    ],
                    start=1,
                )
            ],
        ]
