# Django Expense Tracker

A full-stack personal finance application built with Django. Users can register, manage their own categories and transactions, review financial summaries, search and filter transaction history, and paginate through results securely.

## Features

- User registration, login, and logout
- Protected dashboard
- User-owned categories
- User-owned income and expense transactions
- Category CRUD
- Transaction CRUD
- Dashboard totals for:
  - Total income
  - Total expenses
  - Current balance
- Expense totals grouped by category
- Five most recent transactions
- Search by transaction description or category name
- Filter by:
  - Transaction type
  - Category
  - Month
  - Year
- Pagination with preserved filters
- Responsive layout
- Success and error messages
- Strong validation and ownership protection
- Django admin integration
- Comprehensive automated test suite

## Technology Stack

- Python
- Django
- SQLite
- HTML
- CSS
- Django Template Language
- Django ORM
- Django authentication system
- Django messages framework
- Django test framework

## Main Django Concepts Demonstrated

- Django projects and apps
- URL routing
- Function-based views
- Template inheritance
- Static files
- Authentication and sessions
- `login_required`
- Django forms and `ModelForm`
- Custom form initialization
- Model relationships with `ForeignKey`
- `TextChoices`
- `DecimalField`
- Model validation with `clean()`
- Database constraints
- `CASCADE`
- `RESTRICT`
- Ownership-safe querysets
- `get_object_or_404`
- Query aggregation
- `Sum`
- `values`
- `annotate`
- `select_related`
- `Q` objects
- Query parameters with `request.GET`
- Pagination with `Paginator`
- Django messages
- Admin customization
- Automated model, form, view, authorization, filter, pagination, and template tests

## Project Structure

```text
django-expense-tracker/
├── config/
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── templates/
│   ├── base.html
│   └── registration/
│       ├── login.html
│       └── register.html
│
├── tracker/
│   ├── migrations/
│   ├── static/
│   │   └── tracker/
│   │       └── styles.css
│   ├── templates/
│   │   └── tracker/
│   │       ├── category_confirm_delete.html
│   │       ├── category_form.html
│   │       ├── category_list.html
│   │       ├── dashboard.html
│   │       ├── home.html
│   │       ├── transaction_confirm_delete.html
│   │       ├── transaction_detail.html
│   │       ├── transaction_form.html
│   │       └── transaction_list.html
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
│
├── .gitignore
├── manage.py
├── requirements.txt
└── README.md
```

## Data Model

### Category

Each category belongs to one user.

Main fields:

- `user`
- `name`
- `category_type`
- `created_at`
- `updated_at`

Category types:

- Income
- Expense

A user cannot create duplicate categories with the same name and type.

### Transaction

Each transaction belongs to one user and one category.

Main fields:

- `user`
- `category`
- `transaction_type`
- `amount`
- `description`
- `transaction_date`
- `created_at`
- `updated_at`

Transaction types:

- Income
- Expense

Amounts are stored using `DecimalField` rather than floating-point values.

## Security and Ownership Protections

The application is designed so users can only access their own financial data.

Examples:

```python
Transaction.objects.filter(user=request.user)
```

```python
get_object_or_404(
    Transaction,
    pk=pk,
    user=request.user,
)
```

The same ownership checks are used for categories.

Additional protections include:

- Protected views with `login_required`
- CSRF protection on state-changing forms
- User ownership assigned on the server
- Category dropdowns limited to the logged-in user
- Tampered category IDs rejected
- Cross-user edit and delete attempts return 404
- Category and transaction types must match
- Future transaction dates are rejected
- Zero and negative transaction amounts are rejected
- Whitespace-only descriptions are rejected
- Categories in use by transactions cannot be deleted directly

## Dashboard Calculations

The dashboard uses Django ORM aggregation.

Total income:

```python
transactions.filter(
    transaction_type=Transaction.TransactionType.INCOME
).aggregate(
    total=Sum("amount", default=Decimal("0.00"))
)["total"]
```

Total expenses:

```python
transactions.filter(
    transaction_type=Transaction.TransactionType.EXPENSE
).aggregate(
    total=Sum("amount", default=Decimal("0.00"))
)["total"]
```

Balance:

```python
balance = total_income - total_expenses
```

Expenses grouped by category:

```python
transactions.filter(
    transaction_type=Transaction.TransactionType.EXPENSE
).values(
    "category__name"
).annotate(
    total=Sum("amount")
).order_by(
    "-total",
    "category__name",
)
```

## Search and Filtering

The transaction page supports:

- Description search
- Category-name search
- Transaction-type filtering
- Category filtering
- Month filtering
- Year filtering

Search uses Django `Q` objects:

```python
Q(description__icontains=search)
| Q(category__name__icontains=search)
```

Example URL:

```text
/transactions/?search=groceries&transaction_type=expense&month=6&year=2026
```

## Pagination

Transactions are paginated after ownership and filter rules are applied.

```python
paginator = Paginator(transactions, 5)
page_obj = paginator.get_page(request.GET.get("page"))
```

Active filters are preserved while switching pages.

Example:

```text
/transactions/?transaction_type=expense&year=2026&page=2
```

## Installation

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd django-expense-tracker
```

### 2. Create a virtual environment

Windows PowerShell:

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
```

Windows Git Bash:

```bash
py -m venv venv
source venv/Scripts/activate
```

macOS or Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Apply migrations

```bash
python manage.py migrate
```

### 5. Create an administrator account

```bash
python manage.py createsuperuser
```

### 6. Start the development server

```bash
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

## Running Tests

Run the full test suite:

```bash
python manage.py test
```

Run tests for only the tracker app:

```bash
python manage.py test tracker
```

Run a specific test class:

```bash
python manage.py test tracker.tests.TransactionViewTests
```

Run a specific test:

```bash
python manage.py test tracker.tests.TransactionViewTests.test_logged_in_user_can_create_transaction
```

## Useful Project Checks

Run Django's standard system check:

```bash
python manage.py check
```

Check for missing migrations:

```bash
python manage.py makemigrations --check --dry-run
```

View migration status:

```bash
python manage.py showmigrations
```

Verify the stylesheet can be located:

```bash
python manage.py findstatic tracker/styles.css
```

Review production-oriented warnings:

```bash
python manage.py check --deploy
```

```
## Test Coverage Areas

The test suite covers:

- Authentication
- Registration
- Login redirects
- Category models
- Transaction models
- Category CRUD
- Transaction CRUD
- Ownership and authorization
- Cross-user access prevention
- Dashboard aggregation
- Search and filtering
- Pagination
- Validation rules
- Static-file inclusion
- Message styling
- Login destination preservation

## Development Notes

- SQLite is used for local development.
- `db.sqlite3` is ignored by Git.
- The virtual environment is ignored by Git.
- Password handling is provided by Django's authentication system.
- Transaction amounts are always stored as positive decimal values.
- Income and expense behavior is determined by `transaction_type`.
- Deleting a user removes that user's categories and transactions.
- Deleting an individual category is restricted when transactions reference it.
```
