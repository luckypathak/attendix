from rest_framework import serializers
from .models import Todo


class TodoSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.username', read_only=True)

    class Meta:
        model = Todo
        fields = '__all__'
        read_only_fields = ('completed_at', 'employee')
