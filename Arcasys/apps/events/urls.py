from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    path('', views.events_view, name='events'),
    path('add-events/', views.add_events_view, name='add_events'),
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('admin-approval/approve/<uuid:user_id>/', views.approve_application, name='approve_application'),
    path('admin-approval/reject/<uuid:user_id>/', views.reject_application, name='reject_application'),
]