
from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("signup/", views.signup_view, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # Period calendar
    path("calendar/", views.calendar_view, name="calendar"),

    # Period records
    path(
        "period/<int:period_id>/edit/",
        views.edit_period,
        name="edit_period"
    ),
    path(
        "period/<int:period_id>/delete/",
        views.delete_period,
        name="delete_period"
    ),

    # Daily symptom journal
    path(
        "journal/",
        views.symptom_journal,
        name="symptom_journal"
    ),
    path(
        "journal/<int:entry_id>/edit/",
        views.edit_symptom,
        name="edit_symptom"
    ),
    path(
        "journal/<int:entry_id>/delete/",
        views.delete_symptom,
        name="delete_symptom"
    ),

    # Cycle insights and statistics
    path("insights/", views.insights_view, name="insights"),

    # Account settings
    path(
        "account-settings/",
        views.account_settings_view,
        name="account_settings"
    ),
]
