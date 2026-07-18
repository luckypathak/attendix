import re

with open("attendix/apps/attendance/management/commands/generate_missed_checkout_notifications.py", "r") as f:
    content = f.read()

content = content.replace("notification_type=\"ALERT\",", "notification_type=\"IN_APP\",")
content = content.replace("is_read=False\n                    )", "status=\"PENDING\"\n                    )")

with open("attendix/apps/attendance/management/commands/generate_missed_checkout_notifications.py", "w") as f:
    f.write(content)
