import re

with open("../backend/attendix/apps/employee/serializers.py", "r") as f:
    content = f.read()

new_fields = """    shift_start_time = serializers.TimeField(source='shift.start_time', read_only=True)
    shift_end_time = serializers.TimeField(source='shift.end_time', read_only=True)"""

pattern = r"    shift_start_time = serializers\.CharField\(required=False, allow_null=True, allow_blank=True\)\n    shift_end_time = serializers\.CharField\(required=False, allow_null=True, allow_blank=True\)"
content = re.sub(pattern, new_fields, content)

with open("../backend/attendix/apps/employee/serializers.py", "w") as f:
    f.write(content)
