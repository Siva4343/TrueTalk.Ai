from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Message


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username"]


class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    receiver = UserSerializer(read_only=True, allow_null=True)

    # Write-only helper fields to accept usernames from the client
    sender_username = serializers.CharField(write_only=True, required=True)
    receiver_username = serializers.CharField(
        write_only=True, required=False, allow_null=True, allow_blank=True
    )

    class Meta:
        model = Message
        fields = [
            "id",
            "sender",
            "receiver",
            "sender_username",
            "receiver_username",
            "text",
            "created_at",
            "is_read",
        ]

    def create(self, validated_data):
        """
        Override create to handle sender_username and receiver_username.
        Convert usernames to User objects before creating the Message.
        """
        from django.contrib.auth.models import User
        
        # Extract username fields
        sender_username = validated_data.pop("sender_username")
        receiver_username = validated_data.pop("receiver_username", None)
        
        # Get or create User objects
        sender, _ = User.objects.get_or_create(
            username=sender_username,
            defaults={"email": f"{sender_username}@example.com"},
        )
        
        receiver = None
        if receiver_username and receiver_username.strip():
            receiver, _ = User.objects.get_or_create(
                username=receiver_username.strip(),
                defaults={"email": f"{receiver_username.strip()}@example.com"},
            )
        
        # Create message with User objects
        validated_data["sender"] = sender
        validated_data["receiver"] = receiver
        
        return super().create(validated_data)

    def to_representation(self, instance):
        """
        Add sender_username and receiver_username to output so the frontend
        can easily display names.
        """
        data = super().to_representation(instance)
        data["sender_username"] = instance.sender.username
        data["receiver_username"] = (
            instance.receiver.username if instance.receiver else None
        )
        return data