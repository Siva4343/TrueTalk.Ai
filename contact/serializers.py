from rest_framework import serializers
from .models import Message

class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.CharField(source='sender.username', read_only=True)

    class Meta:
        model = Message
        fields = [
            "id",
            "sender",
            "text",
            "contact_name",
            "contact_phone",
            "timestamp",
        ]
