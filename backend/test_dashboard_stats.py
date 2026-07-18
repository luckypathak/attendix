import os, sys, django
sys.path.append("/Users/luckyrajput/.gemini/antigravity-ide/scratch/pulseix-workforce-os/backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "attendix.settings")
django.setup()

from attendix.apps.company.views import DashboardStatsView
from rest_framework.test import APIRequestFactory, force_authenticate
from attendix.apps.authentication.models import User

factory = APIRequestFactory()
request = factory.get('/api/company/dashboard-stats/')
user = User.objects.filter(role='SUPER_ADMIN').first()
force_authenticate(request, user=user)

view = DashboardStatsView.as_view()
response = view(request)
print("SUCCESS!")
