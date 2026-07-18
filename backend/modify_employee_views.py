import re

with open("../backend/attendix/apps/employee/views.py", "r") as f:
    content = f.read()

new_qs = """        # Admin optional query param scoping
        firm_id = self.request.query_params.get('firm')
        if firm_id and firm_id != 'ALL' and firm_id != 'undefined':
            from django.db.models import Q
            try:
                base_qs = base_qs.filter(
                    Q(user__firm_id=int(firm_id)) | Q(firm_allocations__firm_id=int(firm_id))
                ).distinct()
            except ValueError:
                pass"""

pattern = r"        # Admin optional query param scoping.*?(?=        return base_qs)"
content = re.sub(pattern, new_qs + "\n", content, flags=re.DOTALL)

with open("../backend/attendix/apps/employee/views.py", "w") as f:
    f.write(content)

