# login/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import PendingUser
from .models import CustomUser
class SignupSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=6)

class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class PhoneSerializer(serializers.Serializer):
    phone = serializers.CharField()

class VerifyOTPSerializer(serializers.Serializer):
    phone = serializers.CharField()
    otp = serializers.CharField()



class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name', 'profile_picture', 'google_id', 'login_provider']
        read_only_fields = ['id', 'google_id', 'login_provider']

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name', 'password']

    def create(self, validated_data):
        user = CustomUser.objects.create_user(**validated_data)
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name', 'profile_picture', 'login_provider']
        read_only_fields = ['id', 'login_provider']