from rest_framework import serializers
from .models import AdvanceSalary, Payroll, PayrollBranchBreakdown


class AdvanceSalarySerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.username', read_only=True)
    remaining_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = AdvanceSalary
        fields = '__all__'
        read_only_fields = ('employee', 'approved_by', 'status', 'repaid_amount')


class PayrollBranchBreakdownSerializer(serializers.ModelSerializer):
    firm_name = serializers.CharField(source='firm.name', read_only=True)

    class Meta:
        model = PayrollBranchBreakdown
        fields = '__all__'


class PayrollSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.username', read_only=True)
    branch_distributions = PayrollBranchBreakdownSerializer(many=True, read_only=True)

    class Meta:
        model = Payroll
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

