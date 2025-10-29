from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    path('', views.events_view, name='events'),
    path('search/', views.events_search_ajax, name='events_search_ajax'),
    path('add/', views.add_event_view, name='add_event'),
    path('edit/<uuid:EventID>/', views.edit_event_view, name='edit_event'),
    path('admin-approval/', views.admin_approval_view, name='admin_approval'),
    path('admin-approval/approve/<uuid:user_id>/', views.approve_application, name='approve_application'),
    path('admin-approval/reject/<uuid:user_id>/', views.reject_application, name='reject_application'),
]