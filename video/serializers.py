from rest_framework import serializers
from django.contrib.auth.models import User
from .models import CallSession, CallLog


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class CallSessionSerializer(serializers.ModelSerializer):
    caller = UserSerializer(read_only=True)
    receiver = UserSerializer(read_only=True)

    class Meta:
        model = CallSession
        fields = [
            'id', 'call_id', 'caller', 'receiver', 'call_type',
            'status', 'room_name', 'created_at', 'started_at', 'ended_at'
        ]


class CallLogSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = CallLog
        fields = ['id', 'call_session', 'user', 'action', 'timestamp']


class CallInitiateSerializer(serializers.Serializer):
    receiver_id = serializers.IntegerField()
    call_type = serializers.ChoiceField(choices=['audio', 'video'])
    room_name = serializers.CharField(max_length=255, required=False)
