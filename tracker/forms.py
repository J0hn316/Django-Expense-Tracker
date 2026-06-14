from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Category


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
