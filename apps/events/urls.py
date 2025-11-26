from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    path('', views.events_view, name='events'),
    path('search/', views.events_search_ajax, name='events_search_api'),
    path('add/', views.add_event_view, name='add_event'),
    path('edit/<uuid:EventID>/', views.edit_event_view, name='edit_event'),
    path('admin-approval/', views.admin_approval_view, name='admin_approval'),
    path('admin-approval/approve/<uuid:user_id>/', views.approve_application, name='approve_application'),
    path('admin-approval/reject/<uuid:user_id>/', views.reject_application, name='reject_application'),
    path('backup-history/', views.backup_history_view, name='backup_history'),
    path("backup-dashboard/", views.backup_dashboard_view, name="backup_dashboard"),
    path('restore/', views.restore_operations_view, name='restore_operations'),
    path("run-backup/", views.run_backup, name="run_backup"),
    path("download-backup/<uuid:id>/", views.download_backup, name="download_backup"),
    path('view-log/<uuid:backup_id>/', views.view_log, name='view_log'),
    path('restore-full/', views.restore_full_database, name='restore_full'),
    path('check-restore-status/<uuid:restore_op_id>/', views.check_restore_status, name='check_restore_status'),
    path("departments/add/", views.add_department, name="add_department"),
    path("departments/delete/<uuid:dept_id>/",views.delete_department,name="delete_department"),
]