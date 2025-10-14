from django.urls import path
from . import views

app_name = 'marketing'

urlpatterns = [
    path('', views.landing_view, name='landing'),
    path('contact/', views.contact_view, name='contact'),
]