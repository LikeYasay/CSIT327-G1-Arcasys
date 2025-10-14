from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    path('', views.events_home, name='events_home'),
    # Event URLs will be added when we move them from ArcasysApp
]