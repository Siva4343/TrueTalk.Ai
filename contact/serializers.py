from rest_framework import serializers
from .models import Contact, SharedContact
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ['id', 'name', 'phone_number', 'email', 'created_at']
        read_only_fields = ['id', 'created_at']

class SharedContactSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    receiver = UserSerializer(read_only=True)
    
    class Meta:
        model = SharedContact
        fields = ['id', 'sender', 'receiver', 'contact_name', 'contact_phone', 
                 'contact_email', 'shared_at', 'is_accepted']
        read_only_fields = ['id', 'sender', 'shared_at', 'is_accepted']

class ShareContactSerializer(serializers.Serializer):
    receiver_id = serializers.IntegerField()
    contact_name = serializers.CharField(max_length=255)
    contact_phone = serializers.CharField(max_length=20)
    contact_email = serializers.EmailField(required=False, allow_blank=True)