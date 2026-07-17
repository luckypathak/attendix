from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import EmployeeProfile, EmployeeFirmAllocation
from attendix.apps.company.models import Department, Designation, Firm

User = get_user_model()


class EmployeeFirmAllocationSerializer(serializers.ModelSerializer):
    firm_name = serializers.CharField(source='firm.name', read_only=True)
    
    class Meta:
        model = EmployeeFirmAllocation
        fields = ('id', 'firm', 'firm_name', 'base_salary', 'pf_type', 'pf_value')


class EmployeeProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeProfile
        fields = '__all__'


class EmployeeDetailsSerializer(serializers.ModelSerializer):
    # Flat Representation
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    email = serializers.EmailField(source='user.email')
    first_name = serializers.CharField(source='user.first_name', required=False, allow_blank=True)
    last_name = serializers.CharField(source='user.last_name', required=False, allow_blank=True)
    phone = serializers.CharField(source='user.phone', required=False, allow_blank=True)
    role = serializers.CharField(source='user.role')
    username = serializers.CharField(source='user.username')
    password = serializers.CharField(source='user.password', write_only=True, required=False)
    
    # Nested dropdown IDs
    department_id = serializers.IntegerField(source='department.id', required=False, allow_null=True)
    designation_id = serializers.IntegerField(source='designation.id', required=False, allow_null=True)
    manager_id = serializers.IntegerField(source='manager.id', required=False, allow_null=True)
    
    department_name = serializers.CharField(source='department.name', read_only=True)
    designation_name = serializers.CharField(source='designation.name', read_only=True)
    manager_name = serializers.CharField(source='manager.username', read_only=True)

    # Firms and Shifts
    firm_id = serializers.IntegerField(required=False, allow_null=True)
    firm_name = serializers.CharField(source='user.firm.name', read_only=True)
    shift_id = serializers.IntegerField(required=False, allow_null=True)
    shift_name = serializers.CharField(source='shift.name', read_only=True)
    shift_start_time = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    shift_end_time = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    firm_allocations = EmployeeFirmAllocationSerializer(many=True, required=False)

    class Meta:
        model = EmployeeProfile
        fields = (
            'id', 'user_id', 'username', 'email', 'first_name', 'last_name', 'phone', 'role',
            'department_id', 'department_name', 'designation_id', 'designation_name',
            'manager_id', 'manager_name', 'base_salary', 'hourly_rate', 'joining_date',
            'pan_number', 'bank_account_no', 'bank_ifsc_code', 'created_at', 'updated_at',
            'password', 'firm_id', 'firm_name', 'shift_id', 'shift_name', 'pf_deduction',
            'pf_type', 'pf_value', 'firm_allocations',
            'shift_start_time', 'shift_end_time', 'allowed_leaves', 'used_leaves'
        )

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        user = getattr(instance, 'user', None)
        firm = getattr(user, 'firm', None) if user else None
        shift = getattr(instance, 'shift', None)
        
        ret['firm_id'] = firm.id if firm else None
        ret['shift_id'] = shift.id if shift else None
        ret['shift_start_time'] = shift.start_time.strftime('%I:%M %p') if (shift and shift.start_time) else None
        ret['shift_end_time'] = shift.end_time.strftime('%I:%M %p') if (shift and shift.end_time) else None
        
        # Explicitly set representation defaults to prevent DRF from skipping key fields on null relations
        ret['department_name'] = instance.department.name if instance.department else None
        ret['designation_name'] = instance.designation.name if instance.designation else None
        ret['manager_name'] = instance.manager.username if instance.manager else None
        ret['shift_name'] = shift.name if shift else None
        
        return ret


    def create(self, validated_data):
        firm_allocations_data = validated_data.pop('firm_allocations', [])
        user_data = validated_data.pop('user', {})
        dept_data = validated_data.pop('department', {})
        desg_data = validated_data.pop('designation', {})
        mgr_data = validated_data.pop('manager', {})

        firm_id = validated_data.pop('firm_id', None)
        shift_id = validated_data.pop('shift_id', None)
        shift_start_str = validated_data.pop('shift_start_time', None)
        shift_end_str = validated_data.pop('shift_end_time', None)

        # Resolve relations
        from attendix.apps.company.models import Firm, Department, Designation
        from attendix.apps.attendance.models import Shift

        firm = Firm.objects.filter(id=firm_id).first() if firm_id else None
        
        # Handle custom shift times
        shift = None
        if shift_start_str and shift_end_str:
            import datetime
            start_time = None
            end_time = None
            for fmt in ('%H:%M', '%H:%M:%S', '%I:%M %p', '%I:%M%p'):
                try:
                    start_time = datetime.datetime.strptime(shift_start_str.strip(), fmt).time()
                    break
                except ValueError:
                    continue
            for fmt in ('%H:%M', '%H:%M:%S', '%I:%M %p', '%I:%M%p'):
                try:
                    end_time = datetime.datetime.strptime(shift_end_str.strip(), fmt).time()
                    break
                except ValueError:
                    continue
            
            if start_time and end_time:
                company = self.context['request'].user.company
                shift, _ = Shift.objects.get_or_create(
                    company=company,
                    start_time=start_time,
                    end_time=end_time,
                    defaults={
                        'name': f"Custom Shift ({start_time.strftime('%I:%M %p')} - {end_time.strftime('%I:%M %p')})"
                    }
                )
        
        if not shift and shift_id:
            shift = Shift.objects.filter(id=shift_id).first()

        # Create user
        password = user_data.get('password')
        if not password:
            password = User.objects.make_random_password()
        user = User.objects.create_user(
            username=user_data.get('username'),
            email=user_data.get('email'),
            password=password,
            first_name=user_data.get('first_name', ''),
            last_name=user_data.get('last_name', ''),
            role=user_data.get('role', User.Roles.EMPLOYEE),
            phone=user_data.get('phone', ''),
            company=self.context['request'].user.company,
            firm=firm
        )

        department = Department.objects.filter(id=dept_data.get('id')).first() if dept_data.get('id') else None
        designation = Designation.objects.filter(id=desg_data.get('id')).first() if desg_data.get('id') else None
        manager = User.objects.filter(id=mgr_data.get('id')).first() if mgr_data.get('id') else None

        profile = EmployeeProfile.objects.create(
            user=user,
            department=department,
            designation=designation,
            manager=manager,
            shift=shift,
            **validated_data
        )

        for alloc_data in firm_allocations_data:
            EmployeeFirmAllocation.objects.create(employee_profile=profile, **alloc_data)

        # Profile creation complete

        return profile

    def update(self, instance, validated_data):
        firm_allocations_data = validated_data.pop('firm_allocations', None)
        user_data = validated_data.pop('user', {})
        dept_data = validated_data.pop('department', {})
        desg_data = validated_data.pop('designation', {})
        mgr_data = validated_data.pop('manager', {})

        firm_id = validated_data.pop('firm_id', None)
        shift_id = validated_data.pop('shift_id', None)
        shift_start_str = validated_data.pop('shift_start_time', None)
        shift_end_str = validated_data.pop('shift_end_time', None)

        from attendix.apps.company.models import Firm, Department, Designation
        from attendix.apps.attendance.models import Shift

        # Update User fields
        user = instance.user
        password = user_data.pop('password', None)
        if password:
            user.set_password(password)
        for attr, value in user_data.items():
            setattr(user, attr, value)

        if firm_id is not None:
            user.firm = Firm.objects.filter(id=firm_id).first()
        user.save()

        # Update Relations
        if 'id' in dept_data:
            instance.department = Department.objects.filter(id=dept_data.get('id')).first()
        if 'id' in desg_data:
            instance.designation = Designation.objects.filter(id=desg_data.get('id')).first()
        if 'id' in mgr_data:
            instance.manager = User.objects.filter(id=mgr_data.get('id')).first()
        
        # Handle custom shift times
        shift = None
        if shift_start_str and shift_end_str:
            import datetime
            start_time = None
            end_time = None
            for fmt in ('%H:%M', '%H:%M:%S', '%I:%M %p', '%I:%M%p'):
                try:
                    start_time = datetime.datetime.strptime(shift_start_str.strip(), fmt).time()
                    break
                except ValueError:
                    continue
            for fmt in ('%H:%M', '%H:%M:%S', '%I:%M %p', '%I:%M%p'):
                try:
                    end_time = datetime.datetime.strptime(shift_end_str.strip(), fmt).time()
                    break
                except ValueError:
                    continue
            
            if start_time and end_time:
                company = self.context['request'].user.company
                shift, _ = Shift.objects.get_or_create(
                    company=company,
                    start_time=start_time,
                    end_time=end_time,
                    defaults={
                        'name': f"Custom Shift ({start_time.strftime('%I:%M %p')} - {end_time.strftime('%I:%M %p')})"
                    }
                )
        
        if shift:
            instance.shift = shift
        elif shift_id is not None:
            instance.shift = Shift.objects.filter(id=shift_id).first()

        # Update Profile fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if firm_allocations_data is not None:
            existing_allocs = {a.firm.id: a for a in instance.firm_allocations.all()}
            incoming_firm_ids = [a['firm'].id for a in firm_allocations_data]
            
            # Delete removed ones
            for f_id, alloc in existing_allocs.items():
                if f_id not in incoming_firm_ids:
                    alloc.delete()
            
            # Create or update incoming
            for alloc_data in firm_allocations_data:
                firm = alloc_data['firm']
                if firm.id in existing_allocs:
                    alloc = existing_allocs[firm.id]
                    alloc.base_salary = alloc_data.get('base_salary', alloc.base_salary)
                    alloc.pf_type = alloc_data.get('pf_type', alloc.pf_type)
                    alloc.pf_value = alloc_data.get('pf_value', alloc.pf_value)
                    alloc.save()
                else:
                    EmployeeFirmAllocation.objects.create(employee_profile=instance, **alloc_data)

        return instance
