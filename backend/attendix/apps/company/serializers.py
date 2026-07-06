from rest_framework import serializers
from .models import Company, Department, Designation, Firm


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'
        read_only_fields = ('company',)


class DesignationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Designation
        fields = '__all__'
        read_only_fields = ('company',)


class FirmSerializer(serializers.ModelSerializer):
    class Meta:
        model = Firm
        fields = '__all__'
        read_only_fields = ('company',)
