import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "attendix.settings")
django.setup()

from attendix.apps.attendance.models import Attendance
from attendix.apps.attendance.serializers import AttendanceSerializer
from django.test import RequestFactory
from rest_framework.request import Request

factory = RequestFactory()
wsgi_request = factory.get('/')
request = Request(wsgi_request)

records = Attendance.objects.all()[:2]
for rec in records:
    print(f"Testing record {rec.id}")
    try:
        data = AttendanceSerializer(rec, context={'request': request}).data
        print("Success!")
    except Exception as e:
        import traceback
        traceback.print_exc()

