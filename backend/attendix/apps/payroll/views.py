from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from .models import AdvanceSalary, Payroll
from .serializers import AdvanceSalarySerializer, PayrollSerializer
from .services import PayrollService

User = get_user_model()


class AdvanceSalaryViewSet(viewsets.ModelViewSet):
    queryset = AdvanceSalary.objects.all()
    serializer_class = AdvanceSalarySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['employee', 'status']

    def get_queryset(self):
        user = self.request.user
        base_qs = self.queryset.filter(employee__is_deleted=False, employee__is_active=True)
        if user.role == 'SUPER_ADMIN':
            firm_id = self.request.query_params.get('firm')
            if firm_id and firm_id != 'ALL' and firm_id != 'undefined':
                try:
                    base_qs = base_qs.filter(employee__firm_id=int(firm_id))
                except ValueError:
                    pass
            return base_qs
        if user.role == 'MANAGER':
            return base_qs.filter(employee__company=user.company, employee__firm=user.firm)
        if user.role == 'COMPANY_ADMIN':
            firm_id = self.request.query_params.get('firm')
            if firm_id and firm_id != 'ALL' and firm_id != 'undefined':
                try:
                    return base_qs.filter(employee__company=user.company, employee__firm_id=int(firm_id))
                except ValueError:
                    pass
            return base_qs.filter(employee__company=user.company)
        return base_qs.filter(employee=user)

    def perform_create(self, serializer):
        user = self.request.user
        status_val = 'PENDING'
        profile = getattr(user, 'employee_profile', None)
        if profile and profile.base_salary:
            limit = float(profile.base_salary) * 0.15
            amount = float(serializer.validated_data.get('amount', 0))
            if amount > limit:
                status_val = 'REJECTED'
        serializer.save(employee=user, status=status_val)

    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        if request.user.role not in ['SUPER_ADMIN', 'COMPANY_ADMIN', 'MANAGER']:
            return Response({"detail": "Only managers/admins can approve advance salary requests."}, status=status.HTTP_403_FORBIDDEN)
        
        adv = self.get_object()
        adv.status = 'APPROVED'
        adv.approved_by = request.user
        adv.save()
        return Response(AdvanceSalarySerializer(adv).data)

    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        if request.user.role not in ['SUPER_ADMIN', 'COMPANY_ADMIN', 'MANAGER']:
            return Response({"detail": "Only managers/admins can reject advance salary requests."}, status=status.HTTP_403_FORBIDDEN)
        
        adv = self.get_object()
        if adv.status == 'COMPLETED':
            return Response({"detail": "Cannot reject fully repaid requests."}, status=status.HTTP_400_BAD_REQUEST)
        if float(adv.repaid_amount) > 0:
            return Response({"detail": "Cannot reject requests that have already started repayment."}, status=status.HTTP_400_BAD_REQUEST)
        adv.status = 'REJECTED'
        adv.approved_by = request.user
        adv.save()
        return Response(AdvanceSalarySerializer(adv).data)

    @action(detail=True, methods=['post'], url_path='disburse')
    def disburse(self, request, pk=None):
        if request.user.role not in ['SUPER_ADMIN', 'COMPANY_ADMIN', 'MANAGER']:
            return Response({"detail": "Only managers/admins can disburse advance requests."}, status=status.HTTP_403_FORBIDDEN)
        
        adv = self.get_object()
        if adv.status != 'APPROVED':
            return Response({"detail": "Only approved advance requests can be disbursed."}, status=status.HTTP_400_BAD_REQUEST)
        
        adv.status = 'DISBURSED'
        adv.save()
        return Response(AdvanceSalarySerializer(adv).data)

    @action(detail=True, methods=['post'], url_path='mark-pending')
    def mark_pending(self, request, pk=None):
        if request.user.role not in ['SUPER_ADMIN', 'COMPANY_ADMIN', 'MANAGER']:
            return Response({"detail": "Only managers/admins can modify advance requests."}, status=status.HTTP_403_FORBIDDEN)
        
        adv = self.get_object()
        if adv.status == 'COMPLETED':
            return Response({"detail": "Cannot revert fully repaid requests."}, status=status.HTTP_400_BAD_REQUEST)
        if float(adv.repaid_amount) > 0:
            return Response({"detail": "Cannot revert requests that have already started repayment."}, status=status.HTTP_400_BAD_REQUEST)
        
        adv.status = 'PENDING'
        adv.save()
        return Response(AdvanceSalarySerializer(adv).data)


class PayrollViewSet(viewsets.ModelViewSet):
    queryset = Payroll.objects.all()
    serializer_class = PayrollSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['employee', 'month', 'year', 'status']

    def get_queryset(self):
        user = self.request.user
        base_qs = self.queryset.filter(employee__is_deleted=False, employee__is_active=True)
        if user.role == 'SUPER_ADMIN':
            firm_id = self.request.query_params.get('firm')
            if firm_id and firm_id != 'ALL' and firm_id != 'undefined':
                try:
                    base_qs = base_qs.filter(employee__firm_id=int(firm_id))
                except ValueError:
                    pass
            return base_qs
        if user.role == 'MANAGER':
            return base_qs.filter(employee__company=user.company, employee__firm=user.firm)
        if user.role == 'COMPANY_ADMIN':
            firm_id = self.request.query_params.get('firm')
            if firm_id and firm_id != 'ALL' and firm_id != 'undefined':
                try:
                    return base_qs.filter(employee__company=user.company, employee__firm_id=int(firm_id))
                except ValueError:
                    pass
            return base_qs.filter(employee__company=user.company)
        return base_qs.filter(employee=user)

    @action(detail=False, methods=['post'], url_path='generate')
    def generate(self, request):
        if request.user.role not in ['SUPER_ADMIN', 'COMPANY_ADMIN']:
            return Response({"detail": "Only admins can generate payrolls."}, status=status.HTTP_403_FORBIDDEN)
        
        employee_id = request.data.get('employee_id')
        month = request.data.get('month')
        year = request.data.get('year')

        if not employee_id or not month or not year:
            return Response({"detail": "employee_id, month, and year are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Get employee
        try:
            employee = User.objects.filter(id=employee_id).first()
            if not employee:
                # Try finding by profile ID
                from attendix.apps.employee.models import EmployeeProfile
                profile = EmployeeProfile.objects.filter(id=employee_id).first()
                if profile:
                    employee = profile.user
            
            if not employee:
                return Response({"detail": "Employee not found."}, status=status.HTTP_404_NOT_FOUND)

            if employee.company != request.user.company and request.user.role != 'SUPER_ADMIN':
                return Response({"detail": "Employee does not belong to your company."}, status=status.HTTP_403_FORBIDDEN)
        except User.DoesNotExist:
            return Response({"detail": "Employee not found."}, status=status.HTTP_404_NOT_FOUND)

        bonus = request.data.get('bonus', 0.0)
        try:
            bonus = float(bonus) if bonus else 0.0
        except ValueError:
            return Response({"detail": "Invalid bonus value."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            payroll = PayrollService.generate_monthly_payroll(employee, int(month), int(year), bonus=bonus)
            return Response(PayrollSerializer(payroll).data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({"detail": str(e.message if hasattr(e, 'message') else e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='payout')
    def payout(self, request, pk=None):
        if request.user.role not in ['SUPER_ADMIN', 'COMPANY_ADMIN']:
            return Response({"detail": "Only admins can process salary payouts."}, status=status.HTTP_403_FORBIDDEN)
        
        payroll = self.get_object()
        try:
            PayrollService.payout_salary(payroll)
            return Response(PayrollSerializer(payroll).data)
        except ValidationError as e:
            return Response({"detail": str(e.message if hasattr(e, 'message') else e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='remove-bonus')
    def remove_bonus(self, request, pk=None):
        if request.user.role not in ['SUPER_ADMIN', 'COMPANY_ADMIN']:
            return Response({"detail": "Only admins can modify bonuses."}, status=status.HTTP_403_FORBIDDEN)
        
        payroll = self.get_object()
        try:
            # Recalculate with bonus reset to 0.0
            payroll = PayrollService.generate_monthly_payroll(
                payroll.employee, 
                payroll.month, 
                payroll.year, 
                bonus=0.0
            )
            return Response(PayrollSerializer(payroll).data)
        except ValidationError as e:
            return Response({"detail": str(e.message if hasattr(e, 'message') else e)}, status=status.HTTP_400_BAD_REQUEST)
