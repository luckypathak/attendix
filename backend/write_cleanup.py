content = """from django.core.management.base import BaseCommand
from django.utils import timezone
from attendix.apps.attendance.models import AttendanceSession, Overtime, AttendanceAuditLog
from attendix.apps.attendance.services import AttendanceService
from datetime import datetime, time, timedelta

class Command(BaseCommand):
    help = 'Monitors active sessions for Overtime requests and timeouts.'

    def handle(self, *args, **options):
        self.stdout.write("Running Auto Checkout & OT Monitor...")
        now_dt = timezone.localtime(timezone.now())
        
        active_sessions = AttendanceSession.objects.filter(
            check_out_time__isnull=True,
            auto_checkout=False
        ).select_related('attendance__shift', 'attendance__employee')

        for session in active_sessions:
            shift = session.attendance.shift
            if not shift:
                continue
                
            att_date = session.attendance.date
            shift_end_dt = timezone.make_aware(datetime.combine(att_date, shift.end_time))
            if shift.end_time < shift.start_time:
                shift_end_dt += timedelta(days=1)
                
            grace_period_end = shift_end_dt + timedelta(minutes=15)
            timeout_end = grace_period_end + timedelta(minutes=15) # Total 30 mins after shift
            
            if now_dt >= grace_period_end and now_dt < timeout_end:
                # 15+ minutes past shift end: generate OT request if not exists
                if session.ot_status not in ['PENDING', 'APPROVED', 'REJECTED']:
                    self.stdout.write(f"Generating Auto OT Request for Session {session.id}")
                    # Create Overtime Request
                    ot = Overtime.objects.create(
                        employee=session.attendance.employee,
                        attendance=session.attendance,
                        session=session,
                        date=att_date,
                        hours=0.0,
                        status='PENDING',
                        reason='AUTO_GENERATED_AFTER_SHIFT_END',
                        request_type='CONTINUE_SHIFT'
                    )
                    session.ot_status = 'PENDING'
                    session.save()
                    
                    # Create notification
                    from attendix.apps.company.models import Notification
                    Notification.objects.create(
                        recipient=None, # Broadcast to admins of this firm
                        firm=session.attendance.employee.firm,
                        company=session.attendance.employee.company,
                        title='Auto OT Request',
                        message=f"{session.attendance.employee.username} is working past shift end.",
                        type='OT_REQUEST'
                    )

            elif now_dt >= timeout_end:
                # 30+ minutes past shift end: Auto checkout if still pending or no OT
                if session.ot_status == 'PENDING' or not session.ot_status:
                    self.stdout.write(f"Timeout Auto Checkout for Session {session.id}")
                    
                    # Mark OT as rejected due to timeout if it existed
                    if session.ot_status == 'PENDING':
                        ot = Overtime.objects.filter(session=session, status='PENDING').first()
                        if ot:
                            ot.status = 'REJECTED'
                            ot.admin_remarks = 'AUTO_REJECTED_TIMEOUT'
                            ot.save()
                    
                    session.check_out_time = now_dt.time()
                    session.auto_checkout = True
                    session.ot_status = 'REJECTED'
                    session.save()
                    
                    # Recalculate
                    AttendanceService._recalculate_attendance_metrics(session.attendance, shift, att_date)
                    
                    # Audit Log
                    AttendanceAuditLog.objects.create(
                        session=session,
                        user=None,
                        old_value={"check_out_time": None, "auto_checkout": False},
                        new_value={"check_out_time": str(session.check_out_time), "auto_checkout": True},
                        reason="AUTO_CHECKOUT_TIMEOUT"
                    )
"""
with open("../backend/attendix/apps/attendance/management/commands/cleanup_active_sessions.py", "w") as f:
    f.write(content)
