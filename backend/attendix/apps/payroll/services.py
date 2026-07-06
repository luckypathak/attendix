import calendar
import datetime
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from .models import Payroll, AdvanceSalary
from attendix.apps.employee.models import EmployeeProfile
from attendix.apps.attendance.models import Attendance, Overtime
from attendix.apps.leave.models import LeaveRequest, Holiday


class PayrollService:
    @classmethod
    @transaction.atomic
    def generate_monthly_payroll(cls, employee, month, year, bonus=0.0):
        # 1. Fetch employee profile
        try:
            profile = employee.employee_profile
        except EmployeeProfile.DoesNotExist:
            raise ValidationError(f"Employee profile not configured for user {employee.username}.")

        # Check if already paid to accumulate and allow recalculation
        existing_payroll = Payroll.objects.filter(employee=employee, month=month, year=year).first()
        accumulated_already_paid = 0.0
        if existing_payroll:
            if existing_payroll.status == 'PAID':
                accumulated_already_paid = float(existing_payroll.already_paid) + float(existing_payroll.net_salary)
            else:
                accumulated_already_paid = float(existing_payroll.already_paid)

        base_salary = profile.base_salary
        hourly_rate = profile.hourly_rate
        company = employee.company

        # 2. Get number of days in the month
        days_in_month = calendar.monthrange(year, month)[1]
        daily_rate = base_salary / days_in_month

        worked_days = 0.0
        absent_days = 0.0
        unpaid_leaves = 0.0
        holidays_count = 0.0

        # Loop through every day of the month to calculate attendance status
        for day in range(1, days_in_month + 1):
            date = datetime.date(year, month, day)
            
            # Fetch attendance
            attendance = Attendance.objects.filter(employee=employee, date=date).first()
            if attendance:
                # If they clocked in but did not clock out, it does not count as a worked day yet
                if attendance.check_in_time and not attendance.check_out_time:
                    absent_days += 1.0
                elif attendance.status in [Attendance.Statuses.PRESENT, Attendance.Statuses.LATE]:
                    worked_days += 1.0
                elif attendance.status == Attendance.Statuses.HALF_DAY:
                    worked_days += 0.5
                    absent_days += 0.5
                elif attendance.status == Attendance.Statuses.LEAVE:
                    # Look up leave request for type
                    leave_req = LeaveRequest.objects.filter(
                        employee=employee,
                        start_date__lte=date,
                        end_date__gte=date,
                        status='APPROVED'
                    ).first()
                    
                    if leave_req and leave_req.leave_type == 'UNPAID':
                        unpaid_leaves += 1.0
                    else:
                        # Paid leave counts as worked/paid day
                        worked_days += 1.0
                elif attendance.status == Attendance.Statuses.HOLIDAY:
                    worked_days += 1.0
                    holidays_count += 1.0
                elif attendance.status == Attendance.Statuses.ABSENT:
                    absent_days += 1.0
            else:
                # No attendance record, check if it was a Holiday
                is_holiday = Holiday.objects.filter(company=company, date=date).exists()
                if is_holiday:
                    worked_days += 1.0
                    holidays_count += 1.0
                else:
                    # No record, not a holiday => Absent
                    absent_days += 1.0

        # 3. Calculate Overtime Pay
        ot_hours = Overtime.objects.filter(
            employee=employee,
            date__year=year,
            date__month=month,
            status='APPROVED'
        ).aggregate(total_hours=Sum('hours'))['total_hours'] or 0.0
        
        ot_hours = float(ot_hours)
        if hourly_rate > 0:
            ot_pay = ot_hours * float(hourly_rate)
        else:
            # Fallback overtime pay formula: (base salary / 240 hours) * 1.5 * ot_hours
            ot_pay = ot_hours * (float(base_salary) / 240.0) * 1.5

        # 4. Calculate Deductions
        unpaid_leave_deduction = unpaid_leaves * float(daily_rate)
        absent_deduction = absent_days * float(daily_rate)

        # 5. Calculate Advance Salary Repayment
        advance_deduction = 0.0
        active_advances = AdvanceSalary.objects.filter(
            employee=employee,
            status='DISBURSED'
        ).order_by('created_at')

        # Check total remaining repayable amount
        total_remaining_adv = 0.0
        for adv in active_advances:
            total_remaining_adv += float(adv.remaining_amount)

        if total_remaining_adv > 0:
            # We repaye from the first active advance request
            for adv in active_advances:
                rem = float(adv.remaining_amount)
                monthly_limit = float(adv.monthly_deduction)
                to_deduct = min(rem, monthly_limit)
                advance_deduction += to_deduct

        # 6. Final Payslip Totals
        earned_basic = max(0.0, float(base_salary) - unpaid_leave_deduction - absent_deduction)
        pf_deduction_amount = 0.0
        if profile.pf_deduction:
            pf_deduction_amount = round(earned_basic * 0.12, 2)

        gross_salary = float(base_salary) + ot_pay + float(bonus)
        total_deductions = unpaid_leave_deduction + absent_deduction + advance_deduction + pf_deduction_amount
        net_salary = max(0.0, gross_salary - total_deductions - accumulated_already_paid)

        # Update or create payroll record
        payroll, created = Payroll.objects.update_or_create(
            employee=employee,
            month=month,
            year=year,
            defaults={
                'base_salary': base_salary,
                'worked_days': int(worked_days),
                'absent_days': int(absent_days),
                'unpaid_leaves': int(unpaid_leaves),
                'overtime_hours': ot_hours,
                'overtime_pay': ot_pay,
                'bonus': bonus,
                'advance_deduction': advance_deduction,
                'unpaid_leave_deduction': unpaid_leave_deduction,
                'absent_deduction': absent_deduction,
                'pf_deduction': pf_deduction_amount,
                'already_paid': accumulated_already_paid,
                'gross_salary': gross_salary,
                'net_salary': net_salary,
                'status': 'DRAFT'
            }
        )
        return payroll

    @classmethod
    @transaction.atomic
    def payout_salary(cls, payroll):
        if payroll.status == 'PAID':
            raise ValidationError("This salary has already been paid.")

        # Deduct repayment amount from active advances
        employee = payroll.employee
        amount_to_repay = float(payroll.advance_deduction)
        
        if amount_to_repay > 0:
            active_advances = AdvanceSalary.objects.filter(
                employee=employee,
                status='DISBURSED'
            ).order_by('created_at')

            for adv in active_advances:
                if amount_to_repay <= 0:
                    break
                rem = float(adv.remaining_amount)
                to_deduct = min(rem, amount_to_repay)
                
                adv.repaid_amount = float(adv.repaid_amount) + to_deduct
                if float(adv.repaid_amount) >= float(adv.amount):
                    adv.status = 'COMPLETED'
                adv.save()
                
                amount_to_repay -= to_deduct

        payroll.status = 'PAID'
        payroll.save()
        return payroll
