import os, sys, re

filepath = "attendix/apps/company/views.py"
with open(filepath, 'r') as f:
    content = f.read()

# We want to replace everything from `class DashboardStatsView(APIView):` 
# up to the next class or end of file, with a clean version.

import re
# Find the start of DashboardStatsView
start_idx = content.find("class DashboardStatsView(APIView):")
# Find the end (next class or end)
end_idx = content.find("class ", start_idx + 10)
if end_idx == -1:
    end_idx = len(content)

original_class = content[start_idx:end_idx]

# I will write the clean class and inject it
clean_class = """class DashboardStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        today = timezone.localdate()
        from django.db.models import Sum, Count
        from datetime import timedelta

        if user.role in ['SUPER_ADMIN', 'COMPANY_ADMIN', 'MANAGER']:
            firm_id = request.query_params.get('firm')
            
            emp_q = {'user__is_deleted': False, 'user__is_active': True}
            base_q = {'employee__is_deleted': False, 'employee__is_active': True}
            
            if user.role != 'SUPER_ADMIN':
                emp_q['user__company'] = user.company
                base_q['employee__company'] = user.company

            if user.role == 'MANAGER':
                emp_q['user__firm'] = user.firm
                base_q['employee__firm'] = user.firm
            elif firm_id and firm_id != 'ALL' and firm_id != 'undefined':
                try:
                    f_id = int(firm_id)
                    emp_q['user__firm_id'] = f_id
                    base_q['employee__firm_id'] = f_id
                except ValueError:
                    pass

            # Core Imports
            from attendix.apps.attendance.models import Attendance, AttendanceSession, Overtime
            from attendix.apps.leave.models import LeaveRequest
            from attendix.apps.reimbursement.models import Reimbursement
            from attendix.apps.payroll.models import AdvanceSalary, Payroll
            from attendix.apps.employee.models import EmployeeProfile

            # 1. Attendance Stats
            total_employees = EmployeeProfile.objects.filter(**emp_q).count()
            att_q = dict(base_q, date=today)
            checked_in = Attendance.objects.filter(status__in=['PRESENT', 'LATE'], **att_q).count()
            late = Attendance.objects.filter(status='LATE', **att_q).count()
            half_day = Attendance.objects.filter(status='HALF_DAY', **att_q).count()
            absent = Attendance.objects.filter(status='ABSENT', **att_q).count()

            # Auto Checkout Stats
            this_month_start = today.replace(day=1)
            yesterday = today - timedelta(days=1)
            
            auto_checkouts_today = AttendanceSession.objects.filter(
                attendance__date=today, auto_checkout=True, **{f'attendance__{k}': v for k, v in base_q.items()}
            ).count()
            auto_checkouts_yesterday = AttendanceSession.objects.filter(
                attendance__date=yesterday, auto_checkout=True, **{f'attendance__{k}': v for k, v in base_q.items()}
            ).count()
            auto_checkouts_month = AttendanceSession.objects.filter(
                attendance__date__gte=this_month_start, auto_checkout=True, **{f'attendance__{k}': v for k, v in base_q.items()}
            ).count()

            top_checkouts = list(AttendanceSession.objects.filter(
                attendance__date__gte=this_month_start, auto_checkout=True, **{f'attendance__{k}': v for k, v in base_q.items()}
            ).values('attendance__employee__username').annotate(count=Count('id')).order_by('-count')[:5])

            # 2. Leaves
            pending_leaves = LeaveRequest.objects.filter(status='PENDING', **base_q).count()
            approved_leaves = LeaveRequest.objects.filter(status='APPROVED', **base_q).count()
            rejected_leaves = LeaveRequest.objects.filter(status='REJECTED', **base_q).count()

            # 3. Overtime
            pending_ot = Overtime.objects.filter(status='PENDING', **base_q).count()
            approved_ot = Overtime.objects.filter(status='APPROVED', **base_q).count()
            rejected_ot = Overtime.objects.filter(status='REJECTED', **base_q).count()

            # 4. Reimbursement
            reimbs = Reimbursement.objects.filter(**base_q)
            reims_paid = reimbs.filter(status='APPROVED').aggregate(Sum('amount'))['amount__sum'] or 0
            reims_pending = reimbs.filter(status='PENDING').aggregate(Sum('amount'))['amount__sum'] or 0
            reims_month = reimbs.filter(status='APPROVED', created_at__gte=this_month_start).aggregate(Sum('amount'))['amount__sum'] or 0

            # Reimbursement Graph Data
            import datetime
            reims_graph = []
            for i in range(5, -1, -1):
                m_date = today - datetime.timedelta(days=i*30)
                m_start = m_date.replace(day=1)
                m_val = reimbs.filter(status='APPROVED', created_at__year=m_start.year, created_at__month=m_start.month).aggregate(Sum('amount'))['amount__sum'] or 0
                reims_graph.append({
                    "name": m_start.strftime("%b"),
                    "Amount": m_val
                })

            # 5. Advance Salary
            advs = AdvanceSalary.objects.filter(**base_q)
            adv_given = advs.filter(status='APPROVED').aggregate(Sum('amount'))['amount__sum'] or 0
            pending_recovery = advs.filter(status='APPROVED').aggregate(Sum('remaining_amount'))['remaining_amount__sum'] or 0
            recovered_this_month = advs.filter(status='APPROVED', created_at__gte=this_month_start).aggregate(Sum('amount'))['amount__sum'] or 0 # simplification

            # 6. Payroll
            payrolls = Payroll.objects.filter(**base_q)
            payroll_processed = payrolls.filter(status='PROCESSED').count()
            payroll_pending = payrolls.filter(status='PENDING').count()

            # Ensure full schema contract
            stats = {
                "totalEmployees": total_employees,
                "attendance": {
                    "present": checked_in,
                    "late": late,
                    "half_day": half_day,
                    "absent": absent,
                    "auto_checkouts_today": auto_checkouts_today,
                    "auto_checkouts_yesterday": auto_checkouts_yesterday,
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
            trends = []
            for i in range(6, -1, -1):
                d = today - timedelta(days=i)
                trends.append({
                    "date": d.strftime("%a"),
                    "present": Attendance.objects.filter(date=d, status__in=['PRESENT', 'LATE'], **base_q).count()
                })
                
            # Recent Auto Checkouts for the new Dashboard history
            recent_auto_checkouts = AttendanceSession.objects.filter(
                auto_checkout=True, **{f'attendance__{k}': v for k, v in base_q.items()}
            ).select_related('attendance__employee', 'attendance__shift').order_by('-id')[:20]
            
            auto_checkout_history = []
            for session in recent_auto_checkouts:
                from attendix.apps.attendance.models import AttendanceAuditLog
                reason = "AUTO_CHECKOUT"
                log = AttendanceAuditLog.objects.filter(session=session).order_by('-created_at').first()
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

        else:
            # Employee Dashboard Metrics
            from attendix.apps.attendance.models import Attendance
            from attendix.apps.todo.models import Todo
            from attendix.apps.leave.models import LeaveBalance
            from django.db.models import Q
            attendance_today = Attendance.objects.filter(employee=user, date=today).first()
            checked_in_time = attendance_today.check_in_time.strftime('%I:%M %p') if (attendance_today and attendance_today.check_in_time) else 'Pending'
            checked_out_time = attendance_today.check_out_time.strftime('%I:%M %p') if (attendance_today and attendance_today.check_out_time) else 'Pending'
            todos_today = Todo.objects.filter(employee=user).filter(Q(due_date=today) | Q(created_at__date=today))
            total_tasks = todos_today.count()
            completed_tasks = todos_today.filter(is_completed=True).count()
            task_completeness = f"{completed_tasks}/{total_tasks} Tasks Done" if total_tasks > 0 else "No Tasks Assigned"
            balances = LeaveBalance.objects.filter(employee=user)
            remaining_leaves_sum = sum(b.allocated - b.used for b in balances)
            remaining_leaves = f"{remaining_leaves_sum} Days Left"
            # Ensure full schema contract
            stats = {
                "attendance": {
                    "checked_in_time": checked_in_time,
                    "checked_out_time": checked_out_time,
                },
                "tasks": {
                    "completeness": task_completeness
                },
                "leaves": {
                    "remaining": remaining_leaves
                }
            }
            return Response({
                "role": user.role,
                "stats": stats,
                "trends": []
            })
"""

new_content = content[:start_idx] + clean_class + content[end_idx:]
with open(filepath, 'w') as f:
    f.write(new_content)

print("DashboardStatsView rewritten.")
