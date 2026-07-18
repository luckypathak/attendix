import re

with open("../backend/attendix/apps/payroll/services.py", "r") as f:
    content = f.read()

new_logic = """        # 5. Salary Branch Allocation Calculation
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
        else:"""

pattern = r"        # 5\. Salary Branch Allocation Calculation.*?(?=        else:)"
content = re.sub(pattern, new_logic, content, flags=re.DOTALL)

# Also need to update the update_or_create logic at the bottom of the method
new_sync_logic = """        # Sync branch distributions
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
                )"""

pattern2 = r"        # Sync branch distributions.*?(?=        return payroll)"
content = re.sub(pattern2, new_sync_logic + "\n", content, flags=re.DOTALL)

with open("../backend/attendix/apps/payroll/services.py", "w") as f:
    f.write(content)
