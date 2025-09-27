from django.urls import path
from . import views

urlpatterns = [
    path("", views.landing, name="landing"),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path("events/", views.events_view, name="events"),
]
