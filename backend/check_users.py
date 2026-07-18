import os, sys, django
sys.path.append("/Users/luckyrajput/.gemini/antigravity-ide/scratch/pulseix-workforce-os/backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "attendix.settings")
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()
users = User.objects.filter(username__in=['kailash', 'rohit', 'om', 'kiran'])
for u in users:
    print(u.username, u.is_active)
