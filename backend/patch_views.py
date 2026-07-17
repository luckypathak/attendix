import os
import re

# 1. Update company/views.py
comp_path = "../backend/attendix/apps/company/views.py"
with open(comp_path, "r") as f:
    comp_content = f.read()

# Replace the stats return object logic
old_stats = "            return Response({"
new_stats = """            # Ensure full schema contract
            stats = {
                "totalEmployees": total_employees,
                "attendance": {
                    "present": checked_in,
                    "late": late,
                    "half_day": half_day,
                    "absent": absent,
                    "auto_checkouts_today": auto_checkouts_today,
                    "auto_checkouts_month": auto_checkouts_month,
                    "top_auto_checkouts": top_checkouts
                },
                "reimbursements": {
                    "paid": reims_paid,
                    "pending": reims_pending,
                    "this_month": reims_month,
                    "graph": reims_graph
                },
                "advance_salary": {
                    "given": adv_given,
                    "pending_recovery": pending_recovery,
                    "recovered_this_month": recovered_this_month
                },
                "payroll": {
                    "processed": payroll_processed,
                    "pending": payroll_pending
                },
                "leaves": {
                    "pending": pending_leaves,
                    "approved": approved_leaves,
                    "rejected": rejected_leaves
                },
                "overtime": {
                    "pending": pending_ot,
                    "approved": approved_ot,
                    "rejected": rejected_ot
                }
            }
            
            # Additional trend tracking logic
            from datetime import timedelta
            trends = []
            for i in range(6, -1, -1):
                d = today - timedelta(days=i)
                trends.append({
                    "date": d.strftime("%a"),
                    "present": Attendance.objects.filter(date=d, **base_q).count()
                })
                
            # Recent Auto Checkouts for the new Dashboard history
            recent_auto_checkouts = AttendanceSession.objects.filter(
                auto_checkout=True, **{f'attendance__{k}': v for k, v in base_q.items()}
            ).select_related('attendance__employee', 'attendance__shift').order_by('-id')[:20]
            
            auto_checkout_history = []
            for session in recent_auto_checkouts:
                from attendix.apps.attendance.models import AttendanceAuditLog
                reason = "AUTO_CHECKOUT"
                log = AttendanceAuditLog.objects.filter(session=session).first()
                if log:
                    reason = log.reason
                
                auto_checkout_history.append({
                    "employee": session.attendance.employee.username,
                    "date": session.attendance.date.strftime("%Y-%m-%d"),
                    "shift": session.attendance.shift.name if session.attendance.shift else 'Default',
                    "checkout_time": str(session.check_out_time) if session.check_out_time else '',
                    "reason": reason
                })
                
            stats['attendance']['history'] = auto_checkout_history

            return Response({
                "role": user.role,
                "stats": stats,
                "trends": trends
            })
"""
# This requires replacing the return logic in DashboardStatsView
comp_content = re.sub(r"            return Response\(\{[\s\S]*?\}\)", new_stats, comp_content)

with open(comp_path, "w") as f:
    f.write(comp_content)


# 2. Update attendance/views.py OvertimeViewSet
att_path = "../backend/attendix/apps/attendance/views.py"
with open(att_path, "r") as f:
    att_content = f.read()

# Replace reject logic
old_reject = r"            # If still active, automatically check out employee[\s\S]*?attendance\.save\(\)"
new_reject = """            # If still active, automatically check out employee
            if not session.check_out_time:
                from django.utils import timezone
                from .services import AttendanceService
                from .models import AttendanceAuditLog
                now_dt = timezone.localtime(timezone.now())

                session.check_out_time = now_dt.time()
                session.auto_checkout = True
                session.save()

                attendance = session.attendance
                attendance.check_out_time = session.check_out_time
                attendance.save()
                
                # Recalculate metrics correctly based on shift
                AttendanceService._recalculate_attendance_metrics(
                    attendance,
                    attendance.shift or AttendanceService.get_active_shift(ot.employee),
                    attendance.date
                )
                
                # Add Audit Log
                AttendanceAuditLog.objects.create(
                    session=session,
                    user=request.user,
                    old_value={"check_out_time": None},
                    new_value={"check_out_time": str(session.check_out_time), "auto_checkout": True},
                    reason="ADMIN_REJECTED_AUTO_CHECKOUT"
                )
"""
att_content = re.sub(old_reject, new_reject, att_content)

with open(att_path, "w") as f:
    f.write(att_content)

