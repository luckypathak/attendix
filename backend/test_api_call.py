import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "attendix.settings")
django.setup()

from attendix.apps.attendance.views import AttendanceViewSet
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from rest_framework.request import Request

User = get_user_model()
user = User.objects.first()

factory = RequestFactory()
wsgi_request = factory.get('/api/attendance/records/history/')
request = Request(wsgi_request)
request.user = user

view = AttendanceViewSet.as_view({'get': 'history'})
try:
    response = view(request)
    print("Status:", response.status_code)
except Exception as e:
    import traceback
    traceback.print_exc()

view2 = AttendanceViewSet.as_view({'get': 'current'})
try:
    response2 = view2(request)
    print("Status2:", response2.status_code)
except Exception as e:
    import traceback
    traceback.print_exc()
