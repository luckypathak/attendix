from rest_framework import serializers
from .models import Todo


class TodoSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.username', read_only=True)
    employee_shift_end_time = serializers.SerializerMethodField()

    class Meta:
        model = Todo
        fields = '__all__'
        read_only_fields = ('completed_at', 'employee')

    def get_employee_shift_end_time(self, obj):
        try:
            profile = obj.employee.employee_profile
            if profile and profile.shift:
                return profile.shift.end_time.strftime('%H:%M')
        except Exception:
            pass
        return None

    def validate(self, attrs):
        instance = self.instance
        new_due_date = attrs.get('due_date')
        
        # Enforce reasoning if the due date is being postponed/extended to a later date
        if instance and new_due_date and instance.due_date:
            if new_due_date > instance.due_date:
                postpone_reason = attrs.get('postpone_reason')
                if not postpone_reason or not postpone_reason.strip():
                    raise serializers.ValidationError({
                        "postpone_reason": "A reason is required to extend the due date."
                    })
        return attrs
