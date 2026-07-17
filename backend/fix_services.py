import os
import re

svc_path = "../backend/attendix/apps/attendance/services.py"
with open(svc_path, "r") as f:
    svc_content = f.read()

old_metrics = """        if not sessions.exists():
            return

        total_worked_seconds = 0.0
        first_session = sessions.first()
        last_session = sessions.last()"""

new_metrics = """        all_sessions = attendance.sessions.all().order_by('check_in_time')
        if not all_sessions.exists():
            return

        total_worked_seconds = 0.0
        first_session = all_sessions.first()
        last_session = all_sessions.last()
        
        has_active = False

        for session in all_sessions:
            checkin_dt = datetime.datetime.combine(attendance.date, session.check_in_time)
            
            if session.check_out_time:
                checkout_date = attendance.date
                if session.check_out_time < session.check_in_time:
                    checkout_date += datetime.timedelta(days=1)
                checkout_dt = datetime.datetime.combine(checkout_date, session.check_out_time)
                total_worked_seconds += (checkout_dt - checkin_dt).total_seconds()
            else:
                has_active = True
                from django.utils import timezone
                now_dt = timezone.localtime(timezone.now())
                total_worked_seconds += (now_dt - timezone.make_aware(checkin_dt)).total_seconds()

        total_worked_hours = round(total_worked_seconds / 3600.0, 2)
        attendance.total_worked_hours = total_worked_hours"""

svc_content = svc_content.replace(old_metrics, new_metrics)

# Fix break calculation to handle active session
old_break = """        # Break Hours: From first check-in to last check-out total time minus worked hours
        first_in_dt = datetime.datetime.combine(attendance.date, first_session.check_in_time)
        last_out_date = attendance.date
        if last_session.check_out_time < first_session.check_in_time:
            last_out_date += datetime.timedelta(days=1)
        last_out_dt = datetime.datetime.combine(last_out_date, last_session.check_out_time)"""

new_break = """        # Break Hours: From first check-in to last check-out (or now) total time minus worked hours
        first_in_dt = datetime.datetime.combine(attendance.date, first_session.check_in_time)
        if last_session.check_out_time:
            last_out_date = attendance.date
            if last_session.check_out_time < first_session.check_in_time:
                last_out_date += datetime.timedelta(days=1)
            last_out_dt = datetime.datetime.combine(last_out_date, last_session.check_out_time)
            total_elapsed_seconds = (last_out_dt - first_in_dt).total_seconds()
        else:
            from django.utils import timezone
            now_dt = timezone.localtime(timezone.now())
            total_elapsed_seconds = (now_dt - timezone.make_aware(first_in_dt)).total_seconds()"""

svc_content = svc_content.replace(old_break, new_break)

# Fix Half Day rule to check has_active
old_half_day = """        if total_worked_hours < shift_hours or (has_three_strikes and has_auto_checkout_today):
            attendance.status = Attendance.Statuses.HALF_DAY
        else:"""
new_half_day = """        if (total_worked_hours < shift_hours and not has_active) or (has_three_strikes and has_auto_checkout_today):
            attendance.status = Attendance.Statuses.HALF_DAY
        else:"""
svc_content = svc_content.replace(old_half_day, new_half_day)

with open(svc_path, "w") as f:
    f.write(svc_content)

