
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .models import Period
from .forms import PeriodForm


def signup_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = UserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Welcome to LunaCycle!")
            return redirect("home")
    else:
        form = UserCreationForm()

    return render(request, "tracker/signup.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)
            return redirect("home")

        messages.error(request, "Invalid username or password.")

    return render(request, "tracker/login.html")


@login_required
def home(request):
    if request.method == "POST":
        form = PeriodForm(request.POST)

        if form.is_valid():
            period = form.save(commit=False)
            period.user = request.user
            period.save()

            messages.success(
                request,
                "Your period record was saved!"
            )
            return redirect("home")
    else:
        form = PeriodForm()

    # Get only this user's records, ordered by start date.
    all_periods = list(
        Period.objects.filter(user=request.user).order_by("start_date")
    )

    # Calculate the number of days between consecutive period starts.
    cycle_history = []

    for index in range(1, len(all_periods)):
        previous_start = all_periods[index - 1].start_date
        current_start = all_periods[index].start_date

        cycle_length = (current_start - previous_start).days

        if cycle_length > 0:
            cycle_history.append({
                "start_date": previous_start,
                "next_start_date": current_start,
                "length": cycle_length,
            })

    # Calculate the average from the recorded cycle lengths.
    average_cycle = None

    if cycle_history:
        average_cycle = round(
            sum(cycle["length"] for cycle in cycle_history)
            / len(cycle_history)
        )

    # Show the newest period and cycle first.
    periods = all_periods[::-1]
    cycle_history = cycle_history[::-1]

    context = {
        "form": form,
        "periods": periods,
        "cycle_history": cycle_history,
        "average_cycle": average_cycle,
    }

    return render(request, "tracker/home.html", context)


def logout_view(request):
    if request.method == "POST":
        logout(request)
        return redirect("login")

    return redirect("home")
