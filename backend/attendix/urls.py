from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.url_dirs if hasattr(admin.site, 'url_dirs') else admin.site.urls),
    
    # OpenAPI Swagger Docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/v1/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    # Versioned API routes
    path('api/v1/auth/', include('attendix.apps.authentication.urls')),
    path('api/v1/company/', include('attendix.apps.company.urls')),
    path('api/v1/employees/', include('attendix.apps.employee.urls')),
    path('api/v1/attendance/', include('attendix.apps.attendance.urls')),
    path('api/v1/leaves/', include('attendix.apps.leave.urls')),
    path('api/v1/payroll/', include('attendix.apps.payroll.urls')),
    path('api/v1/reimbursements/', include('attendix.apps.reimbursement.urls')),
    path('api/v1/todos/', include('attendix.apps.todo.urls')),
    path('api/v1/notifications/', include('attendix.apps.notifications.urls')),
    path('api/v1/audit/', include('attendix.apps.audit.urls')),
]

from attendix.apps.attendance.views_media import serve_database_file

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Serve media files from database in both debug and production/Render environments
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve_database_file, name='serve_media'),
]

# Start background daemon thread for Auto Checkout so it runs natively on Render without Celery
try:
    from attendix.background import start_background_tasks
    start_background_tasks()
except Exception as e:
    print("Could not start background tasks:", e)

