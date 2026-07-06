from rest_framework import serializers
from .models import Reimbursement


class ReimbursementSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.username', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.username', read_only=True)

    class Meta:
        model = Reimbursement
        fields = '__all__'
        read_only_fields = ('employee', 'approved_by', 'status', 'manager_comments')
