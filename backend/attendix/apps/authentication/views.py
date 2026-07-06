from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from .serializers import MyTokenObtainPairSerializer, UserSerializer, UserRegisterSerializer, CompanyRegistrationSerializer

User = get_user_model()


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class UserRegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    # Allow registration by Company Admin and Super Admin
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        # RBAC Check: Only SUPER_ADMIN and COMPANY_ADMIN can register users
        requesting_user = request.user
        if requesting_user.role not in [User.Roles.SUPER_ADMIN, User.Roles.COMPANY_ADMIN]:
            return Response(
                {"detail": "You do not have permission to register users."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Company Admins can only register users for their own company
        data = request.data.copy()
        if requesting_user.role == User.Roles.COMPANY_ADMIN:
            data['company'] = requesting_user.company_id
            # Prevent Company Admins from creating Super Admins
            if data.get('role') == User.Roles.SUPER_ADMIN:
                data['role'] = User.Roles.EMPLOYEE
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


from rest_framework.views import APIView

class RegisterCompanyView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = CompanyRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "detail": "Company and Admin registered successfully. Please log in.",
                "user": user.username
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
