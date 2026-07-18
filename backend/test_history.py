import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "attendix.settings")
django.setup()

from django.test import RequestFactory
from attendix.apps.attendance.views import AttendanceViewSet
from django.contrib.auth import get_user_model

User = get_user_model()
user = User.objects.get(username='ilucky')

factory = RequestFactory()
request = factory.get('/api/attendance/records/history/')
request.user = user

view = AttendanceViewSet.as_view({'get': 'history'})
response = view(request)

print(response.status_code)
print(response.data)
