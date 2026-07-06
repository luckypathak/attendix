from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model

User = get_user_model()


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token['username'] = user.username
        token['email'] = user.email
        token['role'] = user.role
        token['company_id'] = user.company_id if user.company else None
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'role': self.user.role,
            'company_id': self.user.company_id if self.user.company else None,
            'firm_id': self.user.firm_id if self.user.firm else None,
            'firm_name': self.user.firm.name if self.user.firm else None
        }
        return data


class UserSerializer(serializers.ModelSerializer):
    firm_name = serializers.CharField(source='firm.name', read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'role', 'company', 'phone', 'is_active', 'firm', 'firm_name')
        read_only_fields = ('id', 'is_active')


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ('username', 'password', 'email', 'first_name', 'last_name', 'role', 'company', 'phone')

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            role=validated_data.get('role', User.Roles.EMPLOYEE),
            company=validated_data.get('company', None),
            phone=validated_data.get('phone', '')
        )
        return user


class CompanyRegistrationSerializer(serializers.Serializer):
    company_name = serializers.CharField(max_length=100)
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=6)

    def create(self, validated_data):
        from attendix.apps.company.models import Company
        
        # 1. Create the Company
        company = Company.objects.create(name=validated_data['company_name'])
        
        # 2. Create the Company Admin User
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            role=User.Roles.COMPANY_ADMIN,
            company=company
        )
        return user
