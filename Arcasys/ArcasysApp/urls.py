from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('events/', views.events_view, name='events'),
    path('contact/', views.contact_view, name='contact'),
    
    # Admin routes
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('admin-approval/approve/<uuid:user_id>/', views.approve_application, name='approve_application'),
    path('admin-approval/reject/<uuid:user_id>/', views.reject_application, name='reject_application'),
    path('add-events/', views.add_events_view, name='add_events'),
    
    # Password reset URLs
    path('password-reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', views.CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', views.CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
]
