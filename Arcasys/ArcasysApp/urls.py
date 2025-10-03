from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path("", views.landing, name="landing"),
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("verify-email/", views.verify_email_view, name="verify_email"),
    path("logout/", views.logout_view, name="logout"),
    path("events/", views.events_view, name="events"),
    path("contact/", views.contact_view, name="contact"),

    # Password reset routes - using custom views from views.py
    path(
        "password_reset/",
        views.CustomPasswordResetView.as_view(),
        name="password_reset"
    ),
    path(
        "password_reset/done/",
        views.CustomPasswordResetDoneView.as_view(),
        name="password_reset_done"
    ),
    # FIXED: This URL must include uidb64 and token parameters
    path(
        "reset/<uidb64>/<token>/",
        views.CustomPasswordResetConfirmView.as_view(),
        name="password_reset_confirm"
    ),
    # FIXED: Corrected the path
    path(
        "reset/done/",
        views.CustomPasswordResetCompleteView.as_view(),
        name="password_reset_complete"
    ),
]