from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Message, Group, UserProfile

class UserSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(source='userprofile.phone_number', required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'email', 'phone_number']

class GroupSerializer(serializers.ModelSerializer):
    members = UserSerializer(many=True, read_only=True)

    class Meta:
        model = Group
        fields = ['id', 'name', 'members', 'created_at']

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    receiver = UserSerializer(read_only=True, allow_null=True)
    group = GroupSerializer(read_only=True, allow_null=True)

    # Write-only helper fields to accept usernames/group_ids from the client
    sender_username = serializers.CharField(write_only=True, required=True)
    receiver_username = serializers.CharField(
        write_only=True, required=False, allow_null=True, allow_blank=True
    )
    group_id = serializers.IntegerField(
        write_only=True, required=False, allow_null=True
    )

    class Meta:
        model = Message
        fields = [
            "id",
            "sender",
            "receiver",
            "group",
            "sender_username",
            "receiver_username",
            "group_id",
            "text",
            "msg_type",
            "attachment_url",
            "created_at",
            "is_read",
        ]

    def create(self, validated_data):
        """
        Override create to handle sender_username, receiver_username, and group_id.
        Convert usernames/ids to objects before creating the Message.
        """
        
        # Extract fields
        sender_username = validated_data.pop("sender_username")
        receiver_username = validated_data.pop("receiver_username", None)
        group_id = validated_data.pop("group_id", None)
        
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
            
        group = None
        if group_id:
            try:
                group = Group.objects.get(id=group_id)
            except Group.DoesNotExist:
                pass
        
        # Create message with objects
        validated_data["sender"] = sender
        validated_data["receiver"] = receiver
        validated_data["group"] = group
        
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
        data["group_name"] = instance.group.name if instance.group else None
        return data