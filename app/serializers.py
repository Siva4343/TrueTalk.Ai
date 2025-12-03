from rest_framework import serializers
from django.contrib.auth.models import User
from .models import BusinessProfile

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class BusinessProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = BusinessProfile
        fields = '__all__'
        read_only_fields = ['user', 'is_verified', 'created_at', 'updated_at']
    
    def update(self, instance, validated_data):
        # Handle profile picture update
        if 'profile_picture' in validated_data:
            if instance.profile_picture:
                instance.profile_picture.delete(save=False)
        return super().update(instance, validated_data)

class UserWithProfileSerializer(serializers.ModelSerializer):
    business_profile = BusinessProfileSerializer(read_only=True)
    is_online = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'business_profile', 'is_online']
    
    def get_is_online(self, obj):
        if hasattr(obj, 'status'):
            return obj.status.is_online
        return False