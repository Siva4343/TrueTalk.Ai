from rest_framework import serializers
from .models import CallHistory, CallParticipant, ActiveCall
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class CallParticipantSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = CallParticipant
        fields = ['id', 'user', 'joined_at', 'left_at', 'role', 'is_active']

class CallHistorySerializer(serializers.ModelSerializer):
    caller = UserSerializer(read_only=True)
    callee = UserSerializer(read_only=True)
    participants = CallParticipantSerializer(many=True, read_only=True)
    duration_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = CallHistory
        fields = [
            'id', 'call_id', 'caller', 'callee', 'group', 'call_type', 
            'status', 'start_time', 'end_time', 'duration', 'duration_formatted',
            'end_reason', 'is_screen_sharing', 'participants'
        ]
    
    def get_duration_formatted(self, obj):
        if obj.duration:
            minutes = obj.duration // 60
            seconds = obj.duration % 60
            return f"{minutes:02d}:{seconds:02d}"
        return None

class ActiveCallSerializer(serializers.ModelSerializer):
    caller = UserSerializer(read_only=True)
    participant_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ActiveCall
        fields = [
            'id', 'call_id', 'caller', 'call_type', 'is_group_call', 
            'group', 'created_at', 'is_screen_sharing', 'participant_count'
        ]
    
    def get_participant_count(self, obj):
        return obj.participants.count()

class CallOfferSerializer(serializers.Serializer):
    caller = serializers.CharField()
    callee = serializers.CharField(required=False)
    offer = serializers.DictField()
    isVideo = serializers.BooleanField(default=False)
    isGroupCall = serializers.BooleanField(default=False)
    callId = serializers.CharField()
    groupId = serializers.IntegerField(required=False)

class CallAnswerSerializer(serializers.Serializer):
    caller = serializers.CharField()
    callee = serializers.CharField()
    answer = serializers.DictField()
    callId = serializers.CharField()

class IceCandidateSerializer(serializers.Serializer):
    candidate = serializers.DictField()
    target = serializers.CharField(required=False)
    callId = serializers.CharField()
    connectionId = serializers.CharField(required=False)

class CallEndSerializer(serializers.Serializer):
    callId = serializers.CharField()
    reason = serializers.CharField(required=False, default='ended')
    endedBy = serializers.CharField()