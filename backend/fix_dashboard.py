import re

with open("../frontend/src/pages/Dashboard.jsx", "r") as f:
    content = f.read()

# Replace any direct stats.xyz with stats?.xyz?
content = content.replace("stats.attendance.present", "stats?.attendance?.present ?? 0")
content = content.replace("stats.attendance.late", "stats?.attendance?.late ?? 0")
content = content.replace("stats.attendance.absent", "stats?.attendance?.absent ?? 0")
content = content.replace("stats.attendance.half_day", "stats?.attendance?.half_day ?? 0")
content = content.replace("stats.attendance.auto_checkouts_today", "stats?.attendance?.auto_checkouts_today ?? 0")
content = content.replace("stats.attendance.auto_checkouts_month", "stats?.attendance?.auto_checkouts_month ?? 0")
content = content.replace("stats.attendance.top_auto_checkouts.length", "(stats?.attendance?.top_auto_checkouts || []).length")
content = content.replace("stats.attendance.top_auto_checkouts.map", "(stats?.attendance?.top_auto_checkouts || []).map")

content = content.replace("stats.reimbursements.paid", "stats?.reimbursements?.paid ?? 0")
content = content.replace("stats.reimbursements.pending", "stats?.reimbursements?.pending ?? 0")
content = content.replace("stats.reimbursements.this_month", "stats?.reimbursements?.this_month ?? 0")
content = content.replace("stats.reimbursements.graph", "stats?.reimbursements?.graph || []")

content = content.replace("stats.advance_salary.given", "stats?.advance_salary?.given ?? 0")
content = content.replace("stats.advance_salary.pending_recovery", "stats?.advance_salary?.pending_recovery ?? 0")
content = content.replace("stats.advance_salary.recovered_this_month", "stats?.advance_salary?.recovered_this_month ?? 0")

content = content.replace("stats.payroll.processed", "stats?.payroll?.processed ?? 0")
content = content.replace("stats.payroll.pending", "stats?.payroll?.pending ?? 0")

content = content.replace("stats.leaves.pending", "stats?.leaves?.pending ?? 0")
content = content.replace("stats.leaves.approved", "stats?.leaves?.approved ?? 0")

content = content.replace("stats.overtime.pending", "stats?.overtime?.pending ?? 0")
content = content.replace("stats.overtime.approved", "stats?.overtime?.approved ?? 0")

with open("../frontend/src/pages/Dashboard.jsx", "w") as f:
    f.write(content)

