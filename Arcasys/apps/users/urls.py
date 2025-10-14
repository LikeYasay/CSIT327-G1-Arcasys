from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('', views.user_home, name='user_home'),
    # Auth URLs will be added when we move them from ArcasysApp
]