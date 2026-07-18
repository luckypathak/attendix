import calendar
import datetime
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from .models import Payroll, AdvanceSalary, PayrollBranchBreakdown
from attendix.apps.employee.models import EmployeeProfile, EmployeeFirmAllocation
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

        base_salary = float(profile.base_salary)
        hourly_rate = float(profile.hourly_rate)
        company = employee.company

        # 2. Get number of days in the month
        days_in_month = calendar.monthrange(year, month)[1]

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
                    
                    if leave_req:
                        total_range_days = float((leave_req.end_date - leave_req.start_date).days + 1)
                        duration = float(leave_req.get_leave_duration_days()) / total_range_days
                        
                        if leave_req.leave_type == 'UNPAID':
                            unpaid_leaves += duration
                            if duration < 1.0:
                                if attendance.check_in_time and attendance.check_out_time:
                                    worked_days += (1.0 - duration)
                                else:
                                    absent_days += (1.0 - duration)
                        else:
                            # Paid leave
                            worked_days += duration
                            if duration < 1.0:
                                if attendance.check_in_time and attendance.check_out_time:
                                    worked_days += (1.0 - duration)
                                else:
                                    absent_days += (1.0 - duration)
                    else:
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
            ot_pay = ot_hours * hourly_rate
        else:
            # Fallback overtime pay formula: (base salary / 240 hours) * 1.5 * ot_hours
            ot_pay = (base_salary / 240.0) * 1.5 * ot_hours

        # 4. Calculate Advance Salary Deductions
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
            # We repay from the first active advance request
            for adv in active_advances:
                rem = float(adv.remaining_amount)
                monthly_limit = float(adv.monthly_deduction)
                to_deduct = min(rem, monthly_limit)
                advance_deduction += to_deduct

        # 5. Salary Branch Allocation Calculation
        allocations = profile.firm_allocations.all()
        branch_details = []

        total_pf_deduction = 0.0
        total_gross_salary = 0.0
        total_net_salary = 0.0
        total_unpaid_leave_deduction = 0.0
        total_absent_deduction = 0.0
        total_advance_deduction = advance_deduction

        if allocations.exists():
            for alloc in allocations:
                b_base = float(alloc.base_salary)
                
                # Each branch independently calculates daily rate and deductions
                b_daily_rate = b_base / days_in_month if days_in_month > 0 else 0
                b_unpaid_leave_deduction = round(b_daily_rate * unpaid_leaves, 2)
                b_absent_deduction = round(b_daily_rate * absent_days, 2)
                b_earned_basic = max(0.0, b_base - b_unpaid_leave_deduction - b_absent_deduction)
                
                # PF Deduction config per branch
                b_pf = 0.0
                if alloc.pf_type == 'percentage':
                    b_pf = round(b_earned_basic * float(alloc.pf_value) / 100.0, 2)
                elif alloc.pf_type == 'flat':
                    b_pf = float(alloc.pf_value)
                
                # Proportional assignment for generic additions/deductions (Overtime, Bonus, Advance, Already Paid)
                # We calculate ratio based on this branch's base relative to total alloc base, 
                # so the overall totals sum up correctly.
                total_alloc_base = sum(float(a.base_salary) for a in allocations)
                ratio = b_base / total_alloc_base if total_alloc_base > 0 else (1.0 / len(allocations))
                
                b_ot_pay = ot_pay * ratio
                b_bonus = float(bonus) * ratio
                b_advance_deduct = advance_deduction * ratio
                b_already_paid = accumulated_already_paid * ratio
                
                b_gross = b_base + b_ot_pay + b_bonus
                b_deductions = b_unpaid_leave_deduction + b_absent_deduction + b_advance_deduct + b_pf
                b_net = max(0.0, b_gross - b_deductions - b_already_paid)
                
                total_pf_deduction += b_pf
                total_gross_salary += b_gross
                total_net_salary += b_net
                total_unpaid_leave_deduction += b_unpaid_leave_deduction
                total_absent_deduction += b_absent_deduction

                branch_details.append({
                    'firm': alloc.firm,
                    'base': b_base,
                    'gross': b_gross,
                    'pf': b_pf,
                    'unpaid_leave_deduction': b_unpaid_leave_deduction,
                    'absent_deduction': b_absent_deduction,
                    'advance_deduction': b_advance_deduct,
                    'net': b_net
                })
        else:
            # Single branch fallback
            daily_rate = base_salary / days_in_month
            unpaid_leave_deduction = round(daily_rate * unpaid_leaves, 2)
            absent_deduction = round(daily_rate * absent_days, 2)
            earned_basic = max(0.0, base_salary - unpaid_leave_deduction - absent_deduction)
            
            # Single branch PF config
            pf_deduction_amount = 0.0
            if profile.pf_type == 'percentage':
                pf_deduction_amount = round(earned_basic * float(profile.pf_value) / 100.0, 2)
            elif profile.pf_type == 'flat':
                pf_deduction_amount = float(profile.pf_value)
            elif profile.pf_deduction: # Legacy fallback
                pf_deduction_amount = round(earned_basic * 0.12, 2)

            total_pf_deduction = pf_deduction_amount
            total_gross_salary = base_salary + ot_pay + float(bonus)
            total_unpaid_leave_deduction = unpaid_leave_deduction
            total_absent_deduction = absent_deduction
            total_net_salary = max(0.0, total_gross_salary - (unpaid_leave_deduction + absent_deduction + advance_deduction + pf_deduction_amount) - accumulated_already_paid)

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
                'unpaid_leave_deduction': total_unpaid_leave_deduction,
                'absent_deduction': total_absent_deduction,
                'pf_deduction': total_pf_deduction,
                'already_paid': accumulated_already_paid,
                'gross_salary': total_gross_salary,
                'net_salary': total_net_salary,
                'status': 'DRAFT'
            }
        )

        # Sync branch distributions
        if allocations.exists():
            existing_breakdowns = {b.firm.id: b for b in payroll.branch_distributions.all()}
            for details in branch_details:
                PayrollBranchBreakdown.objects.update_or_create(
                    payroll=payroll,
                    firm=details['firm'],
                    defaults={
                        'base_salary': details['base'],
                        'unpaid_leave_deduction': details['unpaid_leave_deduction'],
                        'absent_deduction': details['absent_deduction'],
                        'advance_deduction': details['advance_deduction'],
                        'gross_salary': details['gross'],
                        'pf_deduction': details['pf'],
                        'net_salary': details['net']
                    }
                )
                existing_breakdowns.pop(details['firm'].id, None)
            for b in existing_breakdowns.values():
                b.delete()
        else:
            if employee.firm:
                PayrollBranchBreakdown.objects.update_or_create(
                    payroll=payroll,
                    firm=employee.firm,
                    defaults={
                        'base_salary': base_salary,
                        'unpaid_leave_deduction': total_unpaid_leave_deduction,
                        'absent_deduction': total_absent_deduction,
                        'advance_deduction': advance_deduction,
                        'gross_salary': total_gross_salary,
                        'pf_deduction': total_pf_deduction,
                        'net_salary': total_net_salary
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
