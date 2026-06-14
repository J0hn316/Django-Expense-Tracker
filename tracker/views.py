from django.contrib import messages
from django.contrib.auth import login
from django.db.models import RestrictedError
from django.http import HttpRequest, HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .models import Category
from .forms import CategoryForm, RegisterForm


def home(request: HttpRequest) -> HttpResponse:
    return render(request, "tracker/home.html")


def register(request: HttpRequest) -> HttpRequest:
    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("tracker:dashboard")

    else:
        form = RegisterForm()

    return render(request, "registration/register.html", {"form": form})


@login_required
def dashboard(request: HttpRequest) -> HttpRequest:
    return render(request, "tracker/dashboard.html")


@login_required
def category_list(request: HttpRequest) -> HttpRequest:
    categories = Category.objects.filter(user=request.user)

    return render(request, "tracker/category_list.html", {"categories": categories})


@login_required
def category_create(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = CategoryForm(request.POST, user=request.user)

        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user
            category.save()

            messages.success(request, "Category created successfully.")
            return redirect("tracker:category_list")
    else:
        form = CategoryForm(user=request.user)

    return render(
        request,
        "tracker/category_form.html",
        {
            "form": form,
            "page_title": "Create Category",
            "button_text": "Create Category",
        },
    )


@login_required
def category_update(request: HttpRequest, pk: int) -> HttpResponse:
    category = get_object_or_404(Category, pk=pk, user=request.user)

    if request.method == "POST":
        form = CategoryForm(request.POST, instance=category, user=request.user)

        if form.is_valid():
            form.save()

            messages.success(request, "Category updated successfully.")
            return redirect("tracker:category_list")
    else:
        form = CategoryForm(instance=category, user=request.user)

    return render(
        request,
        "tracker/category_form.html",
        {
            "form": form,
            "page_title": "Edit Category",
            "button_text": "Save Changes",
        },
    )


@login_required
def category_delete(request: HttpRequest, pk: int) -> HttpResponse:
    category = get_object_or_404(Category, pk=pk, user=request.user)

    if request.method == "POST":
        try:
            category.delete()
            messages.success(request, "Category deleted successfully.")
        except RestrictedError:
            messages.error(
                request,
                "This category cannot be deleted because transactions are using it.",
            )

        return redirect("tracker:category_list")

    return render(
        request,
        "tracker/category_confirm_delete.html",
        {"category": category},
    )
