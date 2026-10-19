
import calendar
from collections import Counter
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .forms import PeriodForm, SymptomEntryForm
from .models import Period, SymptomEntry


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

    all_periods = list(
        Period.objects.filter(user=request.user).order_by("start_date")
    )

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

    average_cycle = None

    if cycle_history:
        average_cycle = round(
            sum(cycle["length"] for cycle in cycle_history)
            / len(cycle_history)
        )

    periods = all_periods[::-1]
    cycle_history = cycle_history[::-1]

    return render(request, "tracker/home.html", {
        "form": form,
        "periods": periods,
        "cycle_history": cycle_history,
        "average_cycle": average_cycle,
    })


def logout_view(request):
    if request.method == "POST":
        logout(request)
        return redirect("login")

    return redirect("home")


@login_required
def edit_period(request, period_id):
    period = get_object_or_404(
        Period,
        id=period_id,
        user=request.user
    )

    if request.method == "POST":
        form = PeriodForm(request.POST, instance=period)

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Your period record was updated!"
            )
            return redirect("home")
    else:
        form = PeriodForm(instance=period)

    return render(request, "tracker/edit_period.html", {
        "form": form,
        "period": period,
    })


@login_required
def delete_period(request, period_id):
    period = get_object_or_404(
        Period,
        id=period_id,
        user=request.user
    )

    if request.method == "POST":
        period.delete()
        messages.success(
            request,
            "Your period record was deleted."
        )

    return redirect("home")


@login_required
def calendar_view(request):
    today = timezone.localdate()
    month_value = request.GET.get("month", "")

    try:
        if month_value:
            selected_year, selected_month = map(
                int, month_value.split("-")
            )

            if not 1 <= selected_month <= 12:
                raise ValueError

            selected_date = date(selected_year, selected_month, 1)
        else:
            selected_date = date(today.year, today.month, 1)

    except (ValueError, TypeError):
        selected_date = date(today.year, today.month, 1)

    year = selected_date.year
    month = selected_date.month

    periods = list(
        Period.objects.filter(user=request.user).order_by("start_date")
    )

    cycle_lengths = []

    for index in range(1, len(periods)):
        difference = (
            periods[index].start_date
            - periods[index - 1].start_date
        ).days

        if difference > 0:
            cycle_lengths.append(difference)

    average_cycle = None

    if cycle_lengths:
        average_cycle = round(
            sum(cycle_lengths) / len(cycle_lengths)
        )

    predicted_start = None

    if average_cycle and periods:
        latest_start = max(
            period.start_date for period in periods
        )

        predicted_start = latest_start + timedelta(
            days=average_cycle
        )

        while predicted_start < today:
            predicted_start += timedelta(days=average_cycle)

    recorded_dates = set()

    for period in periods:
        current_date = period.start_date
        last_date = period.end_date or period.start_date

        while current_date <= last_date:
            recorded_dates.add(current_date)
            current_date += timedelta(days=1)

    first_weekday, days_in_month = calendar.monthrange(year, month)
    calendar_days = []

    for _ in range(first_weekday):
        calendar_days.append({
            "date": None,
            "is_period": False,
            "is_predicted": False,
            "is_today": False,
        })

    for day_number in range(1, days_in_month + 1):
        current_date = date(year, month, day_number)
        is_predicted = False

        if predicted_start:
            predicted_end = predicted_start + timedelta(days=4)
            is_predicted = (
                predicted_start <= current_date <= predicted_end
            )

        calendar_days.append({
            "date": current_date,
            "is_period": current_date in recorded_dates,
            "is_predicted": (
                is_predicted and current_date not in recorded_dates
            ),
            "is_today": current_date == today,
        })

    trailing_cells = (7 - len(calendar_days) % 7) % 7

    for _ in range(trailing_cells):
        calendar_days.append({
            "date": None,
            "is_period": False,
            "is_predicted": False,
            "is_today": False,
        })

    previous_month_date = (
        selected_date - timedelta(days=1)
    ).replace(day=1)

    if month == 12:
        next_month_date = date(year + 1, 1, 1)
    else:
        next_month_date = date(year, month + 1, 1)

    context = {
        "month_name": calendar.month_name[month],
        "year": year,
        "weekdays": [
            "Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"
        ],
        "calendar_days": calendar_days,
        "previous_month": previous_month_date.strftime("%Y-%m"),
        "next_month": next_month_date.strftime("%Y-%m"),
        "average_cycle": average_cycle,
        "predicted_start": predicted_start,
    }

    return render(request, "tracker/calendar.html", context)


@login_required
def symptom_journal(request):
    today = timezone.localdate()

    if request.method == "POST":
        form = SymptomEntryForm(request.POST)

        if form.is_valid():
            entry_date = form.cleaned_data["date"]

            existing_entry = SymptomEntry.objects.filter(
                user=request.user,
                date=entry_date
            ).first()

            if existing_entry:
                form.add_error(
                    "date",
                    "You already have a journal entry for this date. "
                    "Edit your existing entry instead."
                )
            else:
                entry = form.save(commit=False)
                entry.user = request.user
                entry.save()

                messages.success(
                    request,
                    "Your daily journal entry was saved!"
                )
                return redirect("symptom_journal")

    else:
        form = SymptomEntryForm(initial={"date": today})

    entries = SymptomEntry.objects.filter(
        user=request.user
    ).order_by("-date", "-created_at")

    return render(request, "tracker/symptom_journal.html", {
        "form": form,
        "entries": entries,
        "today": today,
    })


@login_required
def edit_symptom(request, entry_id):
    entry = get_object_or_404(
        SymptomEntry,
        id=entry_id,
        user=request.user
    )

    if request.method == "POST":
        form = SymptomEntryForm(request.POST, instance=entry)

        if form.is_valid():
            duplicate = SymptomEntry.objects.filter(
                user=request.user,
                date=form.cleaned_data["date"]
            ).exclude(id=entry.id).exists()

            if duplicate:
                form.add_error(
                    "date",
                    "You already have a journal entry for this date."
                )
            else:
                form.save()
                messages.success(
                    request,
                    "Your journal entry was updated!"
                )
                return redirect("symptom_journal")

    else:
        form = SymptomEntryForm(instance=entry)

    return render(request, "tracker/edit_symptom.html", {
        "form": form,
        "entry": entry,
    })


@login_required
def delete_symptom(request, entry_id):
    entry = get_object_or_404(
        SymptomEntry,
        id=entry_id,
        user=request.user
    )

    if request.method == "POST":
        entry.delete()
        messages.success(
            request,
            "Your journal entry was deleted."
        )

    return redirect("symptom_journal")


@login_required
def insights_view(request):
    today = timezone.localdate()

    periods = list(
        Period.objects.filter(
            user=request.user
        ).order_by("start_date")
    )

    cycle_lengths = []

    for index in range(1, len(periods)):
        cycle_length = (
            periods[index].start_date
            - periods[index - 1].start_date
        ).days

        if cycle_length > 0:
            cycle_lengths.append(cycle_length)

    average_cycle = None
    shortest_cycle = None
    longest_cycle = None

    if cycle_lengths:
        average_cycle = round(
            sum(cycle_lengths) / len(cycle_lengths)
        )
        shortest_cycle = min(cycle_lengths)
        longest_cycle = max(cycle_lengths)

    period_durations = []

    for period in periods:
        if (
            period.end_date
            and period.end_date >= period.start_date
        ):
            duration = (
                period.end_date - period.start_date
            ).days + 1

            period_durations.append(duration)

    average_period_duration = None

    if period_durations:
        average_period_duration = round(
            sum(period_durations) / len(period_durations), 1
        )

    predicted_start = None

    if average_cycle and periods:
        latest_start = max(
            period.start_date for period in periods
        )

        predicted_start = latest_start + timedelta(
            days=average_cycle
        )

        while predicted_start < today:
            predicted_start += timedelta(days=average_cycle)

    journal_entries = list(
        SymptomEntry.objects.filter(
            user=request.user
        ).order_by("-date", "-created_at")
    )

    average_pain = None

    if journal_entries:
        average_pain = round(
            sum(entry.pain_level for entry in journal_entries)
            / len(journal_entries),
            1
        )

    mood_counts = Counter(
        entry.get_mood_display()
        for entry in journal_entries
        if entry.mood
    )

    mood_stats = [
        {"label": mood, "count": count}
        for mood, count in mood_counts.most_common()
    ]

    most_common_mood = None

    if mood_stats:
        most_common_mood = mood_stats[0]["label"]

    symptom_counts = Counter()

    for entry in journal_entries:
        if entry.symptoms:
            normalized_text = (
                entry.symptoms
                .replace(";", ",")
                .replace("\n", ",")
            )

            for symptom in normalized_text.split(","):
                symptom = symptom.strip().lower()

                if symptom:
                    symptom_counts[symptom] += 1

    symptom_stats = [
        {"label": symptom, "count": count}
        for symptom, count in symptom_counts.most_common(10)
    ]

    context = {
        "total_periods": len(periods),
        "total_journal_entries": len(journal_entries),
        "average_cycle": average_cycle,
        "shortest_cycle": shortest_cycle,
        "longest_cycle": longest_cycle,
        "average_period_duration": average_period_duration,
        "predicted_start": predicted_start,
        "average_pain": average_pain,
        "most_common_mood": most_common_mood,
        "mood_stats": mood_stats,
        "symptom_stats": symptom_stats,
        "recent_entries": journal_entries[:5],
    }

    return render(request, "tracker/insights.html", context)


@login_required
def account_settings_view(request):
    user = request.user
    password_form = PasswordChangeForm(user=user)
    profile_error = None

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "update_profile":
            first_name = request.POST.get("first_name", "").strip()
            last_name = request.POST.get("last_name", "").strip()
            email = request.POST.get("email", "").strip()

            if email:
                try:
                    validate_email(email)
                except ValidationError:
                    profile_error = "Please enter a valid email address."

            if not profile_error:
                user.first_name = first_name
                user.last_name = last_name
                user.email = email
                user.save(update_fields=[
                    "first_name",
                    "last_name",
                    "email",
                ])

                messages.success(
                    request,
                    "Your account details have been updated!"
                )
                return redirect("account_settings")

        elif action == "change_password":
            password_form = PasswordChangeForm(
                user=user,
                data=request.POST
            )

            if password_form.is_valid():
                updated_user = password_form.save()
                update_session_auth_hash(request, updated_user)

                messages.success(
                    request,
                    "Your password has been changed successfully!"
                )
                return redirect("account_settings")

    return render(request, "tracker/account_settings.html", {
        "password_form": password_form,
        "profile_error": profile_error,
    })
