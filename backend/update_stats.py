import sys

def update_views():
    file_path = "attendix/apps/company/views.py"
    with open(file_path, "r") as f:
        content = f.read()

    new_view = """class DashboardStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        today = timezone.localdate()
        from django.db.models import Sum, Count

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

            # 1. Attendance Stats
            total_employees = EmployeeProfile.objects.filter(**emp_q).count()
            att_q = dict(base_q, date=today)
            checked_in = Attendance.objects.filter(**att_q).count()
            late = Attendance.objects.filter(status='LATE', **att_q).count()
            half_day = Attendance.objects.filter(status='HALF_DAY', **att_q).count()
            absent = Attendance.objects.filter(status='ABSENT', **att_q).count()

            # Auto Checkout Stats
            this_month_start = today.replace(day=1)
            auto_checkouts_today = AttendanceSession.objects.filter(
                attendance__date=today, auto_checkout=True, **{f'attendance__{k}': v for k, v in base_q.items()}
            ).count()
            auto_checkouts_month = AttendanceSession.objects.filter(
                attendance__date__gte=this_month_start, auto_checkout=True, **{f'attendance__{k}': v for k, v in base_q.items()}
            ).count()

            top_auto_checkouts = list(AttendanceSession.objects.filter(
                attendance__date__gte=this_month_start, auto_checkout=True, **{f'attendance__{k}': v for k, v in base_q.items()}
            ).values('attendance__employee__username').annotate(count=Count('id')).order_by('-count')[:5])

            # 2. Leaves
            pending_leaves = LeaveRequest.objects.filter(status='PENDING', **base_q).count()
            approved_leaves = LeaveRequest.objects.filter(status='APPROVED', **base_q).count()
            rejected_leaves = LeaveRequest.objects.filter(status='REJECTED', **base_q).count()

            # 3. Overtime
            ot_pending = Overtime.objects.filter(status='PENDING', **base_q).count()
            ot_approved = Overtime.objects.filter(status='APPROVED', **base_q).count()
            ot_rejected = Overtime.objects.filter(status='REJECTED', **base_q).count()

            # 4. Reimbursement
            reimbs = Reimbursement.objects.filter(**base_q)
            reimb_paid = reimbs.filter(status='APPROVED').aggregate(Sum('amount'))['amount__sum'] or 0
            reimb_pending = reimbs.filter(status='PENDING').aggregate(Sum('amount'))['amount__sum'] or 0
            reimb_month = reimbs.filter(status='APPROVED', created_at__gte=this_month_start).aggregate(Sum('amount'))['amount__sum'] or 0

            # Reimbursement Graph Data (last 6 months)
            import datetime
            from dateutil.relativedelta import relativedelta
            reimb_graph = []
            for i in range(5, -1, -1):
                target_month = today - relativedelta(months=i)
                start_dt = target_month.replace(day=1)
                end_dt = (start_dt + relativedelta(months=1))
                amt = reimbs.filter(status='APPROVED', created_at__gte=start_dt, created_at__lt=end_dt).aggregate(Sum('amount'))['amount__sum'] or 0
                reimb_graph.append({
                    "name": start_dt.strftime("%b %Y"),
                    "amount": float(amt)
                })

            # 5. Advance Salary
            advances = AdvanceSalary.objects.filter(**base_q)
            adv_given = advances.aggregate(Sum('amount'))['amount__sum'] or 0
            adv_recovered = advances.aggregate(Sum('repaid_amount'))['repaid_amount__sum'] or 0
            adv_pending = float(adv_given) - float(adv_recovered)
            adv_month_recovered = advances.filter(updated_at__gte=this_month_start).aggregate(Sum('repaid_amount'))['repaid_amount__sum'] or 0 # Approximation

            # 6. Payroll
            payrolls = Payroll.objects.filter(**base_q)
            payroll_processed = payrolls.filter(status='PAID').count()
            payroll_pending = payrolls.filter(status__in=['DRAFT', 'APPROVED']).count()

            import datetime
            trends_data = []
            for i in range(6, -1, -1):
                date_point = today - datetime.timedelta(days=i)
                day_name = date_point.strftime('%a')
                trend_att_q = dict(base_q, date=date_point)
                present_count = Attendance.objects.filter(status__in=['PRESENT', 'LATE'], **trend_att_q).count()
                late_count = Attendance.objects.filter(status='LATE', **trend_att_q).count()
                trends_data.append({
                    "name": day_name,
                    "Present": present_count,
                    "Late": late_count
                })

            return Response({
                "role": user.role,
                "stats": {
                    "totalEmployees": total_employees,
                    "attendance": {
                        "present": checked_in,
                        "absent": absent,
                        "half_day": half_day,
                        "late": late,
                        "auto_checkouts_today": auto_checkouts_today,
                        "auto_checkouts_month": auto_checkouts_month,
                        "top_auto_checkouts": top_auto_checkouts
                    },
                    "leaves": {
                        "pending": pending_leaves,
                        "approved": approved_leaves,
                        "rejected": rejected_leaves
                    },
                    "overtime": {
                        "pending": ot_pending,
                        "approved": ot_approved,
                        "rejected": ot_rejected
                    },
                    "reimbursements": {
                        "paid": float(reimb_paid),
                        "pending": float(reimb_pending),
                        "this_month": float(reimb_month),
                        "graph": reimb_graph
                    },
                    "advance_salary": {
                        "given": float(adv_given),
                        "pending_recovery": adv_pending,
                        "recovered_this_month": float(adv_month_recovered)
                    },
                    "payroll": {
                        "processed": payroll_processed,
                        "pending": payroll_pending
                    }
                },
                "trends": trends_data
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
            return Response({
                "role": user.role,
                "stats": {
                    "checkedInTime": checked_in_time,
                    "checkedOutTime": checked_out_time,
                    "taskCompleteness": task_completeness,
                    "remainingLeaves": remaining_leaves
                }
            })"""

    import re
    # Using regex to replace the class
    pattern = re.compile(r'class DashboardStatsView\(APIView\):.*?(?=\n\n|\Z)', re.DOTALL)
    if pattern.search(content):
        new_content = content.replace(pattern.search(content).group(0), new_view)
        with open(file_path, "w") as f:
            f.write(new_content)
        print("Updated views.py successfully")
    else:
        print("Could not find DashboardStatsView")

update_views()
