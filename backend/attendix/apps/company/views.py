from rest_framework import viewsets, permissions
from .models import Company, Department, Designation, Firm
from .serializers import CompanySerializer, DepartmentSerializer, DesignationSerializer, FirmSerializer


class IsCompanyAdminOrSuperAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['SUPER_ADMIN', 'COMPANY_ADMIN']


class TenantModelViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'SUPER_ADMIN':
            return self.queryset
        
        # If model is Company itself, filter by pk
        if self.queryset.model == Company:
            return self.queryset.filter(pk=user.company_id)
            
        return self.queryset.filter(company=user.company)

    def perform_create(self, serializer):
        # Automatically assign company from user if not super admin
        if self.request.user.role != 'SUPER_ADMIN':
            serializer.save(company=self.request.user.company)
        else:
            serializer.save()


class CompanyViewSet(TenantModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    
    def get_permissions(self):
        if self.action in ['create', 'destroy']:
            return [permissions.IsAdminUser()] # Only django staff / absolute superadmins can create companies
        return [IsCompanyAdminOrSuperAdmin()]


class DepartmentViewSet(TenantModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer


class DesignationViewSet(TenantModelViewSet):
    queryset = Designation.objects.all()
    serializer_class = DesignationSerializer


class FirmViewSet(TenantModelViewSet):
    queryset = Firm.objects.all()
    serializer_class = FirmSerializer


from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q
from attendix.apps.employee.models import EmployeeProfile
from attendix.apps.attendance.models import Attendance
from attendix.apps.leave.models import LeaveRequest, LeaveBalance
from attendix.apps.todo.models import Todo

class DashboardStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        today = timezone.localdate()

        if user.role in ['SUPER_ADMIN', 'COMPANY_ADMIN', 'MANAGER']:
            # Read firm parameter
            firm_id = request.query_params.get('firm')
            
            # Setup base query dictionaries excluding deleted users
            emp_q = {'user__is_deleted': False, 'user__is_active': True}
            att_q = {'employee__is_deleted': False, 'employee__is_active': True, 'date': today}
            leave_q = {'employee__is_deleted': False, 'employee__is_active': True, 'status': 'PENDING'}
            
            if user.role != 'SUPER_ADMIN':
                emp_q['user__company'] = user.company
                att_q['employee__company'] = user.company
                leave_q['employee__company'] = user.company

            if user.role == 'MANAGER':
                emp_q['user__firm'] = user.firm
                att_q['employee__firm'] = user.firm
                leave_q['employee__firm'] = user.firm
            elif firm_id and firm_id != 'ALL' and firm_id != 'undefined':
                try:
                    f_id = int(firm_id)
                    emp_q['user__firm_id'] = f_id
                    att_q['employee__firm_id'] = f_id
                    leave_q['employee__firm_id'] = f_id
                except ValueError:
                    pass

            # Admin Dashboard Metrics
            total_employees = EmployeeProfile.objects.filter(**emp_q).count()
            
            # Real checked-in today count
            checked_in = Attendance.objects.filter(**att_q).count()
            
            # Real late arrivals count today
            late_q = dict(att_q, status='LATE')
            late = Attendance.objects.filter(**late_q).count()
            
            # Real pending leaves count
            pending_leaves = LeaveRequest.objects.filter(**leave_q).count()

            # Calculate real attendance trends for the last 7 days
            import datetime
            trends_data = []
            for i in range(6, -1, -1):
                date_point = today - datetime.timedelta(days=i)
                day_name = date_point.strftime('%a')
                
                trend_att_q = dict(att_q, date=date_point)
                trend_att_q.pop('status', None)
                
                present_count = Attendance.objects.filter(
                    status__in=['PRESENT', 'LATE'],
                    **trend_att_q
                ).count()
                
                late_count = Attendance.objects.filter(
                    status='LATE',
                    **trend_att_q
                ).count()
                
                trends_data.append({
                    "name": day_name,
                    "Present": present_count,
                    "Late": late_count
                })

            return Response({
                "role": user.role,
                "stats": {
                    "totalEmployees": total_employees,
                    "checkedIn": checked_in,
                    "late": late,
                    "pendingLeaves": pending_leaves
                },
                "trends": trends_data
            })
        else:
            # Employee Dashboard Metrics
            attendance_today = Attendance.objects.filter(
                employee=user,
                date=today
            ).first()
            
            checked_in_time = attendance_today.check_in_time.strftime('%I:%M %p') if (attendance_today and attendance_today.check_in_time) else 'Pending'
            checked_out_time = attendance_today.check_out_time.strftime('%I:%M %p') if (attendance_today and attendance_today.check_out_time) else 'Pending'
            
            # Tasks completeness
            todos_today = Todo.objects.filter(employee=user).filter(Q(due_date=today) | Q(created_at__date=today))
            total_tasks = todos_today.count()
            completed_tasks = todos_today.filter(is_completed=True).count()
            task_completeness = f"{completed_tasks}/{total_tasks} Tasks Done" if total_tasks > 0 else "No Tasks Assigned"

            # Leaves remaining
            balances = LeaveBalance.objects.filter(employee=user)
            remaining_leaves_sum = sum(b.allocated - b.used for b in balances)
            remaining_leaves = f"{remaining_leaves_sum} Days Left"

            return Response({
                "role": user.role,
                "stats": {
                    "checkedInTime": checked_in_time,
                    "checkedOutTime": checked_out_time,
                    "taskCompleteness": task_completeness,
                    "remainingLeaves": remaining_leaves
                }
            })
