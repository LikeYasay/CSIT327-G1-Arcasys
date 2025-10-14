from django.urls import path
from . import views

app_name = 'marketing'

urlpatterns = [
    path('', views.marketing_home, name='marketing_home'),
    # Marketing URLs will be added when we move them from ArcasysApp
]