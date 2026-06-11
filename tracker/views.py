from django.contrib.auth import login
from django.shortcuts import redirect, render
from django.http import HttpRequest, HttpResponse
from django.contrib.auth.decorators import login_required

from .forms import RegisterForm


def home(request: HttpRequest) -> HttpResponse:
    return render(request, "tracker/home.html")


def register(req: HttpRequest) -> HttpRequest:
    if req.method == "POST":
        form = RegisterForm(req.POST)

        if form.is_valid():
            user = form.save()
            login(req, user)
            return redirect("tracker:dashboard")

    else:
        form = RegisterForm()

    return render(req, "registration/register.html", {"form": form})


@login_required
def dashboard(req: HttpRequest) -> HttpRequest:
    return render(req, "tracker/dashboard.html")
