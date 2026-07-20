import os
import django
from datetime import date
from dotenv import load_dotenv
from rest_framework.test import APIRequestFactory, force_authenticate

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendix.settings')
django.setup()

from attendix.apps.attendance.views import AttendanceViewSet
from django.contrib.auth import get_user_model

User = get_user_model()
admin_user = User.objects.filter(role='SUPER_ADMIN').first()

factory = APIRequestFactory()
request = factory.get('/attendance/records/?date=2026-07-19')
force_authenticate(request, user=admin_user)

view = AttendanceViewSet.as_view({'get': 'list'})
response = view(request)
print("Response data count:", response.data.get('count') if hasattr(response.data, 'get') else len(response.data))
if 'results' in response.data:
    print("Sample result date:", response.data['results'][0]['date'] if response.data['results'] else "None")
    print("Total results:", len(response.data['results']))

