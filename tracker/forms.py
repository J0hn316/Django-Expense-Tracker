from django import forms
from datetime import date
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
            "transaction_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, user: User | None = None, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.user = user

        if self.user:
            self.instance.user = self.user
            self.fields["category"].queryset = Category.objects.filter(user=self.user)

    def clean_description(self) -> str:
        description = self.cleaned_data["description"].strip()

        if not description:
            raise forms.ValidationError("Description cannot be empty.")

        return description

    def clean(self) -> dict:
        cleaned_data = super().clean()

        category = cleaned_data.get("category")
        transaction_type = cleaned_data.get("transaction_type")

        if self.user and category and category.user != self.user:
            raise forms.ValidationError(
                "The selected category must belong to your account."
            )

        if category and transaction_type and category.category_type != transaction_type:
            raise forms.ValidationError(
                "The selected category type must match the transaction type."
            )

        return cleaned_data


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
