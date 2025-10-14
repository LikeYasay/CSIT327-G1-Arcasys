from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Include your modular app URLs
    path('', include('apps.marketing.urls')),  # Landing page
    path('users/', include('apps.users.urls')),
    path('events/', include('apps.events.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)