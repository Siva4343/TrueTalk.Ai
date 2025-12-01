from rest_framework import serializers
from django.contrib.auth.models import User
from django.utils import timezone
from .models import CallSession, CallLog
import uuid


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user information for nested serialization"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id', 'username', 'email']


class UserSerializer(serializers.ModelSerializer):
    """Extended user serializer with additional info"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name']
        read_only_fields = ['id']
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username


class CallLogSerializer(serializers.ModelSerializer):
    """Serializer for call logs with user details"""
    user = UserBasicSerializer(read_only=True)
    call_id = serializers.CharField(source='call_session.call_id', read_only=True)
    
    class Meta:
        model = CallLog
        fields = ['id', 'call_session', 'call_id', 'user', 'action', 'timestamp']
        read_only_fields = ['id', 'timestamp']


class CallSessionListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing call sessions"""
    caller = UserBasicSerializer(read_only=True)
    receiver = UserBasicSerializer(read_only=True)
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = CallSession
        fields = [
            'id', 'call_id', 'caller', 'receiver', 'call_type',
            'status', 'room_name', 'created_at', 'duration'
        ]
        read_only_fields = ['id', 'call_id', 'created_at']
    
    def get_duration(self, obj):
        """Calculate call duration in seconds"""
        if obj.started_at and obj.ended_at:
            duration = (obj.ended_at - obj.started_at).total_seconds()
            return int(duration)
        return None


class CallSessionDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single call session with logs"""
    caller = UserBasicSerializer(read_only=True)
    receiver = UserBasicSerializer(read_only=True)
    logs = CallLogSerializer(many=True, read_only=True)
    duration = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    
    class Meta:
        model = CallSession
        fields = [
            'id', 'call_id', 'caller', 'receiver', 'call_type',
            'status', 'room_name', 'created_at', 'started_at', 
            'ended_at', 'duration', 'is_active', 'logs'
        ]
        read_only_fields = ['id', 'call_id', 'created_at', 'started_at', 'ended_at']
    
    def get_duration(self, obj):
        """Calculate call duration in seconds"""
        if obj.started_at and obj.ended_at:
            duration = (obj.ended_at - obj.started_at).total_seconds()
            return int(duration)
        elif obj.started_at and obj.status == 'ongoing':
            # For ongoing calls, calculate duration from start time
            duration = (timezone.now() - obj.started_at).total_seconds()
            return int(duration)
        return None
    
    def get_is_active(self, obj):
        """Check if call is currently active"""
        return obj.status in ['initiated', 'ongoing']


class CallInitiateSerializer(serializers.Serializer):
    """Serializer for initiating a new call"""
    receiver_id = serializers.IntegerField(required=True)
    call_type = serializers.ChoiceField(
        choices=['audio', 'video'],
        default='video',
        help_text="Type of call: audio or video"
    )
    room_name = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        help_text="Optional custom room name"
    )
    
    def validate_receiver_id(self, value):
        """Validate that receiver exists and is not the caller"""
        request = self.context.get('request')
        
        # Check if receiver exists
        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError("Receiver not found")
        
        # Check if caller is trying to call themselves
        if request and request.user.is_authenticated:
            if request.user.id == value:
                raise serializers.ValidationError("Cannot call yourself")
        
        return value
    
    def validate(self, data):
        """Additional validation"""
        # Generate room name if not provided
        if not data.get('room_name'):
            data['room_name'] = f"room_{uuid.uuid4().hex[:12]}"
        
        return data


class CallActionSerializer(serializers.Serializer):
    """Serializer for call actions (accept, reject, end)"""
    reason = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        help_text="Optional reason for the action"
    )


class CallStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating call status"""
    status = serializers.ChoiceField(
        choices=['initiated', 'ongoing', 'ended', 'missed'],
        help_text="New status for the call"
    )
    
    def validate_status(self, value):
        """Validate status transition"""
        instance = self.context.get('instance')
        if instance:
            current_status = instance.status
            
            # Define valid status transitions
            valid_transitions = {
                'initiated': ['ongoing', 'missed', 'ended'],
                'ongoing': ['ended'],
                'ended': [],  # Cannot transition from ended
                'missed': []  # Cannot transition from missed
            }
            
            if value not in valid_transitions.get(current_status, []):
                raise serializers.ValidationError(
                    f"Cannot transition from '{current_status}' to '{value}'"
                )
        
        return value
