from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path("", views.landing, name="landing"),
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("events/", views.events_view, name="events"),
    path("contact/", views.contact_view, name="contact"),
    path("add_event/", views.add_event_view, name="add_event"),
    path("admin_dashboard/", views.admin_dashboard_view, name="admin_dashboard"),

    # Forgot password routes
    path(
        "password_reset/",
        auth_views.PasswordResetView.as_view(
            template_name="ArcasysApp/password_reset.html"
        ),
        name="password_reset"
    ),
    path(
        "password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="ArcasysApp/password_reset_done.html"
        ),
        name="password_reset_done"
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="ArcasysApp/password_reset_confirm.html"
        ),
        name="password_reset_confirm"
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="ArcasysApp/password_reset_complete.html"
        ),
        name="password_reset_complete"
    ),
]
