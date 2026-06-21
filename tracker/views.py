from decimal import Decimal
from django.contrib import messages
from django.contrib.auth import login
from django.core.paginator import Paginator
from django.db.models import RestrictedError, Sum, Q
from django.http import HttpRequest, HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .models import Category, Transaction
from .forms import CategoryForm, RegisterForm, TransactionForm, TransactionFilterForm


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
    transactions = Transaction.objects.filter(user=request.user)

    total_income = transactions.filter(
        transaction_type=Transaction.TransactionType.INCOME
    ).aggregate(total=Sum("amount", default=Decimal("0.00")))["total"]

    total_expenses = transactions.filter(
        transaction_type=Transaction.TransactionType.EXPENSE
    ).aggregate(total=Sum("amount", default=Decimal("0.00")))["total"]

    balance = total_income - total_expenses

    expense_totals_by_category = (
        transactions.filter(transaction_type=Transaction.TransactionType.EXPENSE)
        .values("category__name")
        .annotate(total=Sum("amount"))
        .order_by("-total", "category__name")
    )

    recent_transactions = transactions.select_related("category")[:5]

    context = {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "balance": balance,
        "expense_totals_by_category": expense_totals_by_category,
        "recent_transactions": recent_transactions,
    }

    return render(request, "tracker/dashboard.html", context)


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


@login_required
def transaction_list(request: HttpRequest) -> HttpResponse:
    transactions = Transaction.objects.filter(user=request.user).select_related(
        "category"
    )

    filter_form = TransactionFilterForm(
        request.GET or None,
        user=request.user,
    )

    if filter_form.is_valid():
        search = filter_form.cleaned_data["search"]
        transaction_type = filter_form.cleaned_data["transaction_type"]
        category = filter_form.cleaned_data["category"]
        month = filter_form.cleaned_data["month"]
        year = filter_form.cleaned_data["year"]

        if search:
            transactions = transactions.filter(
                Q(description__icontains=search) | Q(category__name__icontains=search)
            )

        if transaction_type:
            transactions = transactions.filter(transaction_type=transaction_type)

        if category:
            transactions = transactions.filter(category=category)

        if month:
            transactions = transactions.filter(transaction_date__month=int(month))

        if year:
            transactions = transactions.filter(transaction_date__year=int(year))

    paginator = Paginator(transactions, 5)

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    query_parameters = request.GET.copy()
    query_parameters.pop("page", None)
    query_string = query_parameters.urlencode()

    context = {
        "transactions": page_obj,
        "page_obj": page_obj,
        "filter_form": filter_form,
        "query_string": query_string,
        "filters_are_active": any(
            [
                request.GET.get("search"),
                request.GET.get("transaction_type"),
                request.GET.get("category"),
                request.GET.get("month"),
                request.GET.get("year"),
            ]
        ),
    }

    return render(
        request,
        "tracker/transaction_list.html",
        context,
    )


@login_required
def transaction_detail(request: HttpRequest, pk: int) -> HttpResponse:
    transaction = get_object_or_404(
        Transaction.objects.select_related("category"),
        pk=pk,
        user=request.user,
    )

    return render(
        request,
        "tracker/transaction_detail.html",
        {"transaction": transaction},
    )


@login_required
def transaction_create(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = TransactionForm(request.POST, user=request.user)

        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()

            messages.success(request, "Transaction created successfully.")
            return redirect("tracker:transaction_list")
    else:
        form = TransactionForm(user=request.user)

    return render(
        request,
        "tracker/transaction_form.html",
        {
            "form": form,
            "page_title": "Create Transaction",
            "button_text": "Create Transaction",
        },
    )


@login_required
def transaction_update(request: HttpRequest, pk: int) -> HttpResponse:
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)

    if request.method == "POST":
        form = TransactionForm(request.POST, instance=transaction, user=request.user)

        if form.is_valid():
            form.save()

            messages.success(request, "Transaction updated successfully.")
            return redirect("tracker:transaction_detail", pk=transaction.pk)
    else:
        form = TransactionForm(instance=transaction, user=request.user)

    return render(
        request,
        "tracker/transaction_form.html",
        {
            "form": form,
            "page_title": "Edit Transaction",
            "button_text": "Save Changes",
        },
    )


@login_required
def transaction_delete(request: HttpRequest, pk: int) -> HttpResponse:
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)

    if request.method == "POST":
        transaction.delete()
        messages.success(request, "Transaction deleted successfully.")
        return redirect("tracker:transaction_list")

    return render(
        request,
        "tracker/transaction_confirm_delete.html",
        {"transaction": transaction},
    )
