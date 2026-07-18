import re

with open("attendix/apps/attendance/management/commands/generate_missed_checkout_notifications.py", "r") as f:
    content = f.read()

content = content.replace("message=message,", "body=message,")
content = content.replace("type=\"ALERT\"", "notification_type=\"ALERT\"")

with open("attendix/apps/attendance/management/commands/generate_missed_checkout_notifications.py", "w") as f:
    f.write(content)
